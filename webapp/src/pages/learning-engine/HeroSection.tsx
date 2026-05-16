type HeroSectionProps = {
  enabledInterests: number;
  sourcesTracked: number;
  totalInterests: number;
};

const SummaryMetric = ({ label, value }: { label: string; value: number }) => (
  <span className="summary-metric">
    <strong>{value}</strong>
    <span>{label}</span>
  </span>
);

export const HeroSection = ({
  enabledInterests,
  sourcesTracked,
  totalInterests,
}: HeroSectionProps) => (
  <section id="top" className="hero">
    <div className="hero-copy">
      <p className="eyebrow">Local engine</p>
      <h1>Learning Engine</h1>
      <p className="subtitle">Track the sources that feed your personal learning loop.</p>
    </div>

    <aside className="summary-card" aria-label="Learning Engine summary">
      <div className="summary-header">
        <span className="status-dot" />
        <span>Ready</span>
      </div>
      <div className="stats-grid">
        <SummaryMetric value={enabledInterests} label="active" />
        <SummaryMetric value={totalInterests} label="tracked" />
        <SummaryMetric value={sourcesTracked} label="sources" />
      </div>
    </aside>
  </section>
);
