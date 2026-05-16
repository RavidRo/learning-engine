import { SourceLinks } from "./SourceLinks";
import { type Interest } from "./types";

type InterestCardProps = {
  interest: Interest;
  onEdit: (id: string) => void;
  onRemove: (id: string) => void;
  onToggle: (id: string) => void;
};

const hasSources = (interest: Interest): boolean =>
  interest.sources.some((source) => source.deletedAt == null);

const InterestBadges = ({ interest }: { interest: Interest }) => (
  <div className="meta">
    <span className={`badge priority-${interest.priority}`}>{interest.priority}</span>
    <span className="badge">{interest.enabled ? "enabled" : "paused"}</span>
    <span className="badge">
      {interest.sources.filter((source) => source.deletedAt == null).length} sources
    </span>
  </div>
);

const InterestActions = ({ interest, onEdit, onRemove, onToggle }: InterestCardProps) => (
  <div className="actions">
    <button className="button ghost" type="button" onClick={() => onEdit(interest.id)}>
      Edit
    </button>
    <button className="button ghost" type="button" onClick={() => onToggle(interest.id)}>
      {interest.enabled ? "Disable" : "Enable"}
    </button>
    <button className="button danger" type="button" onClick={() => onRemove(interest.id)}>
      Delete
    </button>
  </div>
);

export const InterestCard = ({ interest, onEdit, onRemove, onToggle }: InterestCardProps) => {
  const showSources = hasSources(interest);

  return (
    <article className={`card ${interest.enabled ? "" : "disabled"}`}>
      <div className="card-main">
        <div>
          <h3>{interest.name}</h3>
          <InterestBadges interest={interest} />
        </div>
        <p>{interest.description || "No description yet."}</p>
        {showSources ? <SourceLinks interest={interest} /> : null}
      </div>
      <InterestActions
        interest={interest}
        onEdit={onEdit}
        onRemove={onRemove}
        onToggle={onToggle}
      />
    </article>
  );
};
