#!/usr/bin/env python3
"""Generate a visual HTML briefing from the Learning Engine server.

Usage:
    python3 scripts/generate_briefing.py --days 14

The script intentionally fetches data from the running engine server instead of
reading local files directly. That keeps the briefing path exercising the same
API the UI will use.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
BRIEFINGS_DIR = PROJECT_ROOT / "briefings"
DEFAULT_SERVER = "http://127.0.0.1:8765"
ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
JsonObject = dict[str, Any]

TOPIC_SUMMARIES = {
    "OpenAI model announcements": {
        "stance": "Agentic coding moved from demo to deployment story.",
        "summary": "OpenAI’s strongest signal was Codex: mobile access, Windows sandboxing, internal safety practice, and multiple enterprise adoption stories. GPT-5.5 Instant and voice API model posts add a model/API layer, but the strategic throughline is organizations operationalizing coding agents.",
        "why": "Relevant for Puzzle/Mador: safe sandboxes, rollout patterns, and concrete adoption stories are the playbook material—not just shiny model names.",
        "watch": "Separate primary model/API launches from marketing/customer stories so the feed does not become noisy.",
    },
    "T3 Code": {
        "stance": "A coding-agent control plane is shipping at high velocity.",
        "summary": "T3 Code produced frequent nightlies plus tagged releases v0.0.23 and v0.0.24. The cadence suggests an early product moving quickly around agent orchestration/control-plane workflows.",
        "why": "This is directly aligned with Ravid’s AI-assisted workflow goals: watch for provider support, stability, and whether it becomes useful as a team-facing harness.",
        "watch": "Look for docs, breaking changes, and a non-nightly release that signals it is ready for serious experiments.",
    },
    "Clawbolt": {
        "stance": "Mozilla.ai’s self-hostable AI client is iterating fast.",
        "summary": "Clawbolt released seven versions in the window, including ServiceTitan integration MVP/polish notes and several patch releases. The signal is product integration and demo readiness rather than a single major announcement.",
        "why": "Worth tracking as a possible open-source/self-hostable AI client pattern for enterprise environments.",
        "watch": "Check whether releases include deployment docs, auth/provider hardening, and real connector maturity.",
    },
    "Anthropic model announcements": {
        "stance": "Claude is being packaged into business/vertical workflows.",
        "summary": "Anthropic’s official news page surfaced Claude for Small Business, higher limits plus a SpaceX compute deal, finance agents, and creative-work positioning. The theme is go-to-market packaging around Claude and agents.",
        "why": "Relevant for comparing model-provider strategy: OpenAI is emphasizing Codex deployment; Anthropic is emphasizing Claude products, usage limits, and vertical agent narratives.",
        "watch": "This source is page-watched, not RSS. Dates/titles should be treated as best-effort until a cleaner official feed exists.",
    },
    "Python": {
        "stance": "Python release train continues: stable, beta, and RC all visible.",
        "summary": "Python published 3.14.5 final, 3.15.0 beta 1, and the 3.14.5 release candidate. This is routine but important platform hygiene.",
        "why": "For production systems, this points to upcoming compatibility testing and dependency readiness checks.",
        "watch": "Track breaking/deprecation notes around 3.15 beta and security fixes in maintenance releases.",
    },
    "Hermes Agent": {
        "stance": "Hermes continues maturing as the local agent OS layer.",
        "summary": "Hermes Agent v0.13.0, the Tenacity Release, landed in the briefing window.",
        "why": "Relevant because this is becoming part of Ravid’s personal operating system and AI-assisted workflow stack.",
        "watch": "Read release notes for reliability, tool execution, gateway, skill, and scheduling changes.",
    },
    "VoidZero": {
        "stance": "Rolldown 1.0 is the JavaScript tooling headline.",
        "summary": "VoidZero announced Rolldown 1.0, an important milestone in the Oxc/Vite/Rolldown toolchain story.",
        "why": "Potentially relevant for frontend build performance, bundling architecture, and future Vite ecosystem direction.",
        "watch": "Look for migration notes, ecosystem adoption, and whether it changes default tooling choices.",
    },
}


def fetch_json(url: str) -> JsonObject:
    if urlparse(url).scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError("Only HTTP and HTTPS URLs can be fetched")

    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("Expected a JSON object response")
        return cast(JsonObject, payload)


def clean_title(title: str) -> str:
    title = re.sub(r"^(?:[A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})", "", title or "")
    title = title.replace("Announcements", " — ")
    title = re.sub(r"\s+", " ", title).strip(" —")
    return title or "Untitled update"


def fmt_date(value: str) -> str:
    if not value:
        return "undated"
    return value[:10]


def escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def group_updates(updates: list[JsonObject]) -> dict[str, list[JsonObject]]:
    grouped: dict[str, list[JsonObject]] = defaultdict(list)
    for update in updates:
        normalized_update = dict(update)
        normalized_update["clean_title"] = clean_title(normalized_update.get("title", ""))
        grouped[normalized_update.get("interest_name", "Other")].append(normalized_update)
    return dict(sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])))


def render_link(update: JsonObject) -> str:
    title = escape(update.get("clean_title") or update.get("title") or "Untitled update")
    url = escape(update.get("url"))
    date = escape(fmt_date(update.get("published_at") or update.get("published") or ""))
    source_type = escape(update.get("source_type", "feed"))
    keywords = ", ".join(update.get("matched_keywords", [])[:5])
    keyword_markup = f'<span class="keywords">{escape(keywords)}</span>' if keywords else ""
    return f"""
      <li>
        <span class="date">{date}</span>
        <a href="{url}" target="_blank" rel="noreferrer">{title}</a>
        <span class="source-pill">{source_type}</span>
        {keyword_markup}
      </li>
    """


def render_topic(name: str, updates: list[JsonObject]) -> str:
    info = TOPIC_SUMMARIES.get(name, {})
    latest = updates[0] if updates else {}
    release_count = sum(
        1 for item in updates if re.search(r"\bv?\d+\.\d+|release|beta|rc|nightly", item.get("title", ""), re.I)
    )
    all_links = "\n".join(render_link(update) for update in updates)
    return f"""
    <section class="topic-card">
      <div class="topic-topline">
        <div>
          <p class="eyebrow">{escape(name)}</p>
          <h2>{escape(info.get("stance", "Tracked signal"))}</h2>
        </div>
        <div class="metric"><strong>{len(updates)}</strong><span>updates</span></div>
      </div>
      <p class="summary">{escape(info.get("summary", "Relevant updates were found in the selected window."))}</p>
      <div class="why-grid">
        <div><strong>Why it matters</strong><p>{escape(info.get("why", "Review the linked source items for full context."))}</p></div>
        <div><strong>Watch next</strong><p>{escape(info.get("watch", "Look for follow-up releases or official migration notes."))}</p></div>
        <div><strong>Latest</strong><p><a href="{escape(latest.get("url"))}" target="_blank" rel="noreferrer">{escape(latest.get("clean_title") or latest.get("title"))}</a></p></div>
        <div><strong>Release-like items</strong><p>{release_count}</p></div>
      </div>
      <details>
        <summary>Full source links for {escape(name)}</summary>
        <ul class="source-list">{all_links}</ul>
      </details>
    </section>
    """


def build_html(payload: JsonObject, output_name: str) -> str:
    raw_updates = payload.get("updates", [])
    updates = [
        dict(update, clean_title=clean_title(update.get("title", "")))
        for update in raw_updates
        if isinstance(update, dict)
    ]
    grouped = group_updates(updates)
    counts = Counter(update.get("interest_name") for update in updates)
    source_counts = Counter(update.get("source_type", "feed") for update in updates)
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    days = payload.get("days") or "all"
    since = payload.get("since") or "beginning"
    top_topics = counts.most_common(4)
    sparkbars = "".join(
        f'<div class="spark-row"><span>{escape(name)}</span><b style="width:{max(8, count / max(counts.values() or [1]) * 100):.1f}%"></b><em>{count}</em></div>'
        for name, count in counts.most_common()
    )
    topic_cards = "\n".join(render_topic(name, items) for name, items in grouped.items())
    timeline = "\n".join(render_link(update) for update in updates[:18])
    top_topic_markup = "".join(f"<span>{escape(name)} · {count}</span>" for name, count in top_topics)
    errors = payload.get("errors", [])
    error_markup = (
        ""
        if not errors
        else "<ul>"
        + "".join(f"<li>{escape(e.get('interest_name'))}: {escape(e.get('error'))}</li>" for e in errors)
        + "</ul>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Learning Engine Briefing · Last {escape(days)} days</title>
  <style>
    :root {{ color-scheme: dark; --bg:#070912; --panel:#101625; --panel2:#151d31; --text:#edf3ff; --muted:#93a4c0; --line:rgba(255,255,255,.11); --accent:#8cf7d0; --hot:#ff8bd1; --blue:#88a7ff; --amber:#ffd166; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background: radial-gradient(circle at top left, rgba(136,167,255,.25), transparent 30rem), radial-gradient(circle at top right, rgba(255,139,209,.16), transparent 26rem), var(--bg); color:var(--text); }}
    a {{ color: var(--accent); text-decoration: none; }} a:hover {{ text-decoration: underline; }}
    .shell {{ width:min(1180px, calc(100vw - 40px)); margin:0 auto; padding:42px 0 70px; }}
    .hero {{ display:grid; grid-template-columns: 1.45fr .9fr; gap:24px; align-items:stretch; }}
    .glass {{ background:linear-gradient(145deg, rgba(16,22,37,.92), rgba(21,29,49,.74)); border:1px solid var(--line); box-shadow:0 20px 80px rgba(0,0,0,.36); border-radius:28px; }}
    .hero-main {{ padding:36px; position:relative; overflow:hidden; }}
    .hero-main:after {{ content:""; position:absolute; inset:auto -8rem -9rem auto; width:22rem; height:22rem; border-radius:999px; background:radial-gradient(circle, rgba(140,247,208,.22), transparent 65%); }}
    .kicker {{ margin:0 0 14px; color:var(--accent); font-weight:800; letter-spacing:.14em; text-transform:uppercase; font-size:.78rem; }}
    h1 {{ margin:0; font-size:clamp(2.4rem, 6vw, 5.8rem); line-height:.94; letter-spacing:-.08em; }}
    .lead {{ color:#cdd8ec; font-size:1.12rem; max-width:760px; line-height:1.7; margin:24px 0 0; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:28px; }}
    .chips span, .source-pill {{ border:1px solid var(--line); color:#dce7fb; background:rgba(255,255,255,.06); border-radius:999px; padding:7px 10px; font-size:.82rem; }}
    .hero-side {{ padding:24px; display:grid; gap:16px; }}
    .stat-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .stat {{ padding:18px; border-radius:20px; background:rgba(255,255,255,.055); border:1px solid var(--line); }}
    .stat strong {{ display:block; font-size:2.05rem; letter-spacing:-.04em; }}
    .stat span {{ color:var(--muted); font-size:.88rem; }}
    .signal-map {{ margin-top:24px; padding:26px; }}
    .signal-map h2, .topic-card h2 {{ margin:0; letter-spacing:-.035em; }}
    .spark-row {{ display:grid; grid-template-columns: 210px 1fr 36px; gap:14px; align-items:center; margin:14px 0; color:#dce7fb; }}
    .spark-row b {{ display:block; height:12px; border-radius:999px; background:linear-gradient(90deg,var(--accent),var(--blue),var(--hot)); box-shadow:0 0 24px rgba(140,247,208,.2); }}
    .spark-row span {{ color:#cbd6ea; }} .spark-row em {{ color:var(--muted); font-style:normal; text-align:right; }}
    .insights {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:18px; margin:24px 0; }}
    .insight {{ padding:22px; border-radius:24px; border:1px solid var(--line); background:linear-gradient(180deg, rgba(255,255,255,.075), rgba(255,255,255,.035)); }}
    .insight h3 {{ margin:0 0 10px; }} .insight p {{ color:#c7d3e8; line-height:1.6; margin:0; }}
    .topic-card {{ margin-top:20px; padding:26px; border-radius:28px; background:rgba(16,22,37,.88); border:1px solid var(--line); }}
    .topic-topline {{ display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }}
    .eyebrow {{ color:var(--blue); text-transform:uppercase; letter-spacing:.12em; font-size:.76rem; font-weight:800; margin:0 0 8px; }}
    .metric {{ min-width:86px; padding:12px; border:1px solid var(--line); border-radius:18px; text-align:center; background:rgba(255,255,255,.055); }}
    .metric strong {{ display:block; font-size:2rem; }} .metric span {{ color:var(--muted); font-size:.75rem; }}
    .summary {{ color:#d8e2f4; line-height:1.7; font-size:1.02rem; }}
    .why-grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; margin:18px 0; }}
    .why-grid div {{ padding:16px; border:1px solid var(--line); border-radius:18px; background:rgba(255,255,255,.045); }}
    .why-grid strong {{ color:#fff; }} .why-grid p {{ color:#bdc9df; line-height:1.5; margin:.5rem 0 0; }}
    details {{ margin-top:18px; }} summary {{ cursor:pointer; color:var(--amber); font-weight:800; }}
    .source-list {{ list-style:none; padding:0; margin:14px 0 0; display:grid; gap:10px; }}
    .source-list li {{ display:grid; grid-template-columns: 96px 1fr auto auto; gap:10px; align-items:center; padding:11px 12px; border-radius:14px; background:rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.07); }}
    .date {{ color:var(--muted); font-variant-numeric:tabular-nums; }} .keywords {{ color:#9fb0cb; font-size:.8rem; }}
    .timeline {{ margin-top:24px; padding:26px; }}
    .note {{ margin-top:24px; padding:18px 20px; color:#c5d0e4; line-height:1.65; border:1px dashed rgba(255,255,255,.18); border-radius:20px; background:rgba(255,255,255,.035); }}
    footer {{ color:var(--muted); margin-top:28px; text-align:center; }}
    @media (max-width: 900px) {{ .hero, .insights, .why-grid {{ grid-template-columns:1fr; }} .source-list li {{ grid-template-columns:1fr; }} .spark-row {{ grid-template-columns:1fr; gap:7px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-main glass">
        <p class="kicker">Learning Engine Briefing · generated {escape(generated)}</p>
        <h1>Two weeks of signal, distilled.</h1>
        <p class="lead">The briefing pulls from feed and page sources through the local engine server. It covers updates since <strong>{escape(since)}</strong>, then compresses them into themes, decisions, and source-backed reading paths.</p>
        <div class="chips">{top_topic_markup}</div>
      </div>
      <aside class="hero-side glass">
        <div class="stat-grid">
          <div class="stat"><strong>{len(updates)}</strong><span>matching updates</span></div>
          <div class="stat"><strong>{len(grouped)}</strong><span>active topics</span></div>
          <div class="stat"><strong>{payload.get("sources_checked", 0)}</strong><span>sources checked</span></div>
          <div class="stat"><strong>{source_counts.get("page", 0)}</strong><span>page-fallback items</span></div>
        </div>
        <div class="note"><strong>Clover read:</strong> the dominant theme is not “new models” in isolation. It is agentic software development becoming operational: Codex workflows, T3 Code as control plane, Clawbolt as self-hostable client, and Hermes as local agent OS.</div>
      </aside>
    </section>

    <section class="signal-map glass">
      <h2>Signal density map</h2>
      <p class="summary">Volume is not importance, but it shows where the current information firehose is pointed.</p>
      {sparkbars}
    </section>

    <section class="insights">
      <article class="insight"><h3>1. Coding agents are leaving toy mode.</h3><p>OpenAI’s Codex posts, T3 Code’s release cadence, and Hermes/T3/Clawbolt movement point to agent workflows becoming deployable systems with sandboxes, provider control, and team process implications.</p></article>
      <article class="insight"><h3>2. Self-hostable AI clients deserve a serious look.</h3><p>Clawbolt’s rapid patch stream is early-stage, but the shape matters for enterprise settings where data boundaries, provider choice, and local deployment are non-negotiable.</p></article>
      <article class="insight"><h3>3. Toolchain upgrades continue quietly.</h3><p>Python’s release train and Rolldown 1.0 are less flashy than model launches, but these are the substrate changes that affect build reliability, performance, and developer experience.</p></article>
    </section>

    {topic_cards}

    <section class="timeline glass">
      <h2>Latest-source timeline</h2>
      <p class="summary">A quick path into the raw source trail. Every item links to the source captured by the engine.</p>
      <ul class="source-list">{timeline}</ul>
    </section>

    <section class="note">
      <strong>Blind spots / quality notes:</strong>
      Anthropic is collected with an official-page fallback because no clean official RSS feed is tracked yet; dates and titles are best-effort extraction. OpenAI’s feed is broad and currently captures some adoption/marketing posts because they match Codex/model keywords. Errors from the engine: {len(errors)}. {error_markup}
    </section>

    <footer>Generated by Learning Engine · <code>{escape(output_name)}</code></footer>
  </main>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    payload = fetch_json(f"{args.server.rstrip('/')}/api/updates?days={args.days}")
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    output_name = args.output or f"briefing-{stamp}-last-{args.days}-days.html"
    BRIEFINGS_DIR.mkdir(exist_ok=True)
    output_path = BRIEFINGS_DIR / output_name
    output_path.write_text(build_html(payload, output_name), encoding="utf-8")
    json_path = BRIEFINGS_DIR / output_name.replace(".html", ".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "html": str(output_path),
                "json": str(json_path),
                "updates": len(payload.get("updates", [])),
                "topics": len({update.get("interest_name") for update in payload.get("updates", [])}),
                "errors": len(payload.get("errors", [])),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
