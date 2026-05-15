import { StatCard } from "../../components/StatCard";

type HeroSectionProps = {
  enabledInterests: number;
  feedsWithUpdates: number;
  totalInterests: number;
};

export const HeroSection = ({
  enabledInterests,
  feedsWithUpdates,
  totalInterests,
}: HeroSectionProps) => (
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
        <StatCard value={enabledInterests} label="active" />
        <StatCard value={totalInterests} label="tracked" />
        <StatCard value={feedsWithUpdates} label="feeds" />
        <StatCard value="v0.3" label="private" />
      </div>
    </aside>
  </section>
);
