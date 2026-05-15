import { type SyntheticEvent, useEffect, useMemo, useState } from "react";

type Priority = "high" | "medium" | "low";
type InterestType = "technology";

interface Interest {
  id: string;
  name: string;
  type: InterestType;
  priority: Priority;
  official_site_url: string;
  official_feed_url: string;
  watch_keywords: string[];
  ignore_keywords: string[];
  notes: string;
  enabled: boolean;
}

interface InterestsPayload {
  interests?: Interest[];
}

interface TechnologyUpdate {
  interest_name: string;
  title?: string;
  url: string;
  published?: string;
}

interface TechnologyUpdatesPayload {
  interests_checked?: number;
  updates?: TechnologyUpdate[];
  errors?: unknown[];
  error?: string;
}

interface ToastState {
  message: string;
  visible: boolean;
}

const emptyToast: ToastState = { message: "Saved locally", visible: false };

function slugify(text: string): string {
  const slug = text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || crypto.randomUUID();
}

function parseList(value: FormDataEntryValue | null): string[] {
  const rawValue = typeof value === "string" ? value : "";
  return rawValue
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function getString(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

async function readError(response: Response): Promise<string> {
  const message = await response.text();
  return message || response.statusText;
}

export function App() {
  const [interests, setInterests] = useState<Interest[]>([]);
  const [updates, setUpdates] = useState<TechnologyUpdatesPayload | null>(null);
  const [toast, setToast] = useState<ToastState>(emptyToast);
  const [isSaving, setIsSaving] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const stats = useMemo(() => {
    const enabled = interests.filter((item) => item.enabled).length;
    const feeds = interests.filter((item) => item.official_feed_url).length;
    return { enabled, feeds, total: interests.length };
  }, [interests]);

  useEffect(() => {
    let isActive = true;

    async function loadInterests(): Promise<void> {
      try {
        const response = await fetch("/api/interests");
        if (!response.ok) {
          throw new Error(await readError(response));
        }
        const payload = (await response.json()) as InterestsPayload;
        if (isActive) {
          setInterests(payload.interests ?? []);
          setLoadError(null);
        }
      } catch (error) {
        if (isActive) {
          setLoadError(error instanceof Error ? error.message : "Failed to load interests");
        }
      }
    }

    void loadInterests();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (!toast.visible) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setToast((current) => ({ ...current, visible: false }));
    }, 1400);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [toast.visible]);

  function showToast(message = "Saved locally"): void {
    setToast({ message, visible: true });
  }

  async function saveInterests(nextInterests = interests): Promise<void> {
    setIsSaving(true);
    try {
      const response = await fetch("/api/interests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interests: nextInterests }, null, 2),
      });

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      showToast();
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Failed to save");
    } finally {
      setIsSaving(false);
    }
  }

  async function checkTechnologyUpdates(): Promise<void> {
    setIsChecking(true);
    try {
      const response = await fetch("/api/technology-updates");
      const payload = (await response.json()) as TechnologyUpdatesPayload;
      if (!response.ok) {
        throw new Error(payload.error ?? "Failed to fetch updates");
      }
      setUpdates(payload);
      showToast("Technology updates checked");
    } catch (error) {
      setUpdates({
        errors: [error instanceof Error ? error.message : "Failed to fetch updates"],
        updates: [],
      });
    } finally {
      setIsChecking(false);
    }
  }

  function addInterest(event: SyntheticEvent<HTMLFormElement, SubmitEvent>): void {
    event.preventDefault();

    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = getString(formData, "name");
    if (!name) {
      return;
    }

    const nextInterests: Interest[] = [
      {
        id: `${slugify(name)}-${String(Date.now())}`,
        name,
        type: "technology",
        priority: getString(formData, "priority") as Priority,
        official_site_url: getString(formData, "officialSiteUrl"),
        official_feed_url: getString(formData, "officialFeedUrl"),
        watch_keywords: parseList(formData.get("watchKeywords")),
        ignore_keywords: parseList(formData.get("ignoreKeywords")),
        notes: getString(formData, "notes"),
        enabled: true,
      },
      ...interests,
    ];

    setInterests(nextInterests);
    form.reset();
    void saveInterests(nextInterests);
  }

  function toggleInterest(id: string): void {
    const nextInterests = interests.map((item) =>
      item.id === id ? { ...item, enabled: !item.enabled } : item,
    );
    setInterests(nextInterests);
    void saveInterests(nextInterests);
  }

  function deleteInterest(id: string): void {
    const nextInterests = interests.filter((item) => item.id !== id);
    setInterests(nextInterests);
    void saveInterests(nextInterests);
  }

  return (
    <>
      <main className="shell">
        <nav className="topbar" aria-label="Main navigation">
          <a className="brand" href="#top" aria-label="Learning Engine home">
            <span className="brand-mark">LE</span>
            <span>Learning Engine</span>
          </a>
          <div className="navlinks" aria-label="Sections">
            <a href="#interests">Interests</a>
            <a href="#add">Technology</a>
            <a href="#briefing">Briefing</a>
          </div>
        </nav>

        <section id="top" className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Local v0.3</p>
            <h1>Your personal signal layer for learning.</h1>
            <p className="subtitle">
              Track technology sources and keep focused updates ready for a quiet evening review.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#add">
                Add interest
              </a>
              <a className="button ghost" href="#briefing">
                Briefing prompt
              </a>
            </div>
          </div>

          <aside className="summary-card" aria-label="Learning Engine summary">
            <div className="summary-header">
              <span className="status-dot" />
              <span>Local engine</span>
            </div>
            <div className="stats-grid">
              <StatCard value={stats.enabled} label="active" />
              <StatCard value={stats.total} label="tracked" />
              <StatCard value={stats.feeds} label="feeds" />
              <StatCard value="v0.3" label="private" />
            </div>
          </aside>
        </section>

        <section className="workspace" aria-label="Interest workspace">
          <aside id="add" className="panel add-panel">
            <div className="panel-header">
              <p className="section-label">Quick add</p>
              <h2>Add a technology</h2>
            </div>

            <form className="form-grid" onSubmit={addInterest}>
              <label>
                Name
                <input name="name" placeholder="Distributed Systems" required />
              </label>
              <div className="split-fields">
                <label>
                  Type
                  <select name="type" defaultValue="technology" disabled>
                    <option value="technology">technology</option>
                  </select>
                </label>
                <label>
                  Priority
                  <select name="priority" defaultValue="medium">
                    <option value="high">high</option>
                    <option value="medium">medium</option>
                    <option value="low">low</option>
                  </select>
                </label>
              </div>
              <label>
                Official website URL
                <input
                  name="officialSiteUrl"
                  type="url"
                  placeholder="https://www.typescriptlang.org/"
                />
              </label>
              <label>
                Official updates/feed URL
                <input
                  name="officialFeedUrl"
                  type="url"
                  placeholder="https://devblogs.microsoft.com/typescript/feed/"
                />
              </label>
              <div className="split-fields">
                <label>
                  Watch keywords
                  <input name="watchKeywords" placeholder="release, beta, compiler" />
                </label>
                <label>
                  Ignore keywords
                  <input name="ignoreKeywords" placeholder="webinar, case study" />
                </label>
              </div>
              <label>
                Notes
                <textarea name="notes" placeholder="What should count as useful signal?" />
              </label>
              <button className="button primary" type="submit">
                Save interest
              </button>
            </form>
          </aside>

          <section id="interests" className="panel list-panel">
            <div className="panel-header row">
              <div>
                <p className="section-label">Signal list</p>
                <h2>Your interests</h2>
              </div>
              <div className="header-actions">
                <button
                  className="button ghost"
                  type="button"
                  onClick={() => {
                    void checkTechnologyUpdates();
                  }}
                  disabled={isChecking}
                >
                  {isChecking ? "Checking..." : "Check updates"}
                </button>
                <button
                  className="button ghost"
                  type="button"
                  onClick={() => {
                    void saveInterests();
                  }}
                  disabled={isSaving}
                >
                  {isSaving ? "Saving..." : "Save now"}
                </button>
              </div>
            </div>

            {loadError === null ? null : (
              <p className="empty">Failed to load interests. {loadError}</p>
            )}
            {updates === null ? null : <TechnologyUpdates payload={updates} />}

            <div className="cards" aria-live="polite">
              {interests.length === 0 ? (
                <p className="empty">No interests yet. Add one source to begin.</p>
              ) : (
                interests.map((interest) => (
                  <InterestCard
                    interest={interest}
                    key={interest.id}
                    onDelete={deleteInterest}
                    onToggle={toggleInterest}
                  />
                ))
              )}
            </div>
          </section>
        </section>

        <section id="briefing" className="panel briefing">
          <div>
            <p className="section-label">Next ritual</p>
            <h2>Evening briefing prompt</h2>
          </div>
          <pre>Read my Learning Engine interests and prepare an evening briefing.</pre>
        </section>
      </main>

      <div className={`toast ${toast.visible ? "show" : ""}`} role="status" aria-live="polite">
        {toast.message}
      </div>
    </>
  );
}

function StatCard({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function InterestCard({
  interest,
  onDelete,
  onToggle,
}: {
  interest: Interest;
  onDelete: (id: string) => void;
  onToggle: (id: string) => void;
}) {
  const hasDetails =
    interest.official_site_url ||
    interest.official_feed_url ||
    interest.watch_keywords.length > 0 ||
    interest.ignore_keywords.length > 0;

  return (
    <article className={`card ${interest.enabled ? "" : "disabled"}`}>
      <div className="card-main">
        <div>
          <h3>{interest.name}</h3>
          <div className="meta">
            <span className="badge">{interest.type}</span>
            <span className={`badge priority-${interest.priority}`}>{interest.priority}</span>
            <span className="badge">{interest.enabled ? "enabled" : "paused"}</span>
          </div>
        </div>
        <p>{interest.notes || "No notes yet."}</p>
        {hasDetails ? <OfficialLinks interest={interest} /> : null}
      </div>
      <div className="actions">
        <button className="button ghost" type="button" onClick={() => onToggle(interest.id)}>
          {interest.enabled ? "Disable" : "Enable"}
        </button>
        <button className="button danger" type="button" onClick={() => onDelete(interest.id)}>
          Delete
        </button>
      </div>
    </article>
  );
}

function OfficialLinks({ interest }: { interest: Interest }) {
  return (
    <div className="official-links">
      {interest.official_site_url ? (
        <a href={interest.official_site_url} target="_blank" rel="noreferrer">
          official site
        </a>
      ) : null}
      {interest.official_feed_url ? (
        <a href={interest.official_feed_url} target="_blank" rel="noreferrer">
          updates feed
        </a>
      ) : null}
      {interest.watch_keywords.map((keyword) => (
        <span className="source" key={`watch-${keyword}`}>
          watch:{keyword}
        </span>
      ))}
      {interest.ignore_keywords.map((keyword) => (
        <span className="source" key={`ignore-${keyword}`}>
          ignore:{keyword}
        </span>
      ))}
    </div>
  );
}

function TechnologyUpdates({ payload }: { payload: TechnologyUpdatesPayload }) {
  const updates = payload.updates ?? [];
  const errors = payload.errors ?? [];
  const checked = payload.interests_checked ?? 0;

  return (
    <div className="updates-panel">
      <h3>Technology updates</h3>
      <p>
        {checked} technology {checked === 1 ? "feed" : "feeds"} checked
      </p>
      {updates.length === 0 ? (
        <p>No matching updates found.</p>
      ) : (
        updates.slice(0, 8).map((update) => (
          <article className="update-item" key={`${update.url}-${update.title ?? ""}`}>
            <strong>{update.interest_name}</strong>
            <a href={update.url} target="_blank" rel="noreferrer">
              {update.title ?? "Untitled update"}
            </a>
            {update.published ? <span>{update.published}</span> : null}
          </article>
        ))
      )}
      {errors.length > 0 ? (
        <p className="updates-error">
          {errors.length} feed {errors.length === 1 ? "error" : "errors"} while checking updates.
        </p>
      ) : null}
    </div>
  );
}
