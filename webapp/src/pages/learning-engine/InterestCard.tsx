import { OfficialLinks } from "./OfficialLinks";
import { type Interest } from "./types";

type InterestCardProps = {
  interest: Interest;
  onRemove: (id: string) => void;
  onToggle: (id: string) => void;
};

const hasInterestDetails = (interest: Interest): boolean =>
  Boolean(
    interest.official_site_url ||
    interest.official_feed_url ||
    interest.watch_keywords.length > 0 ||
    interest.ignore_keywords.length > 0,
  );

const InterestBadges = ({ interest }: { interest: Interest }) => (
  <div className="meta">
    <span className="badge">{interest.type}</span>
    <span className={`badge priority-${interest.priority}`}>{interest.priority}</span>
    <span className="badge">{interest.enabled ? "enabled" : "paused"}</span>
  </div>
);

const InterestActions = ({ interest, onRemove, onToggle }: InterestCardProps) => (
  <div className="actions">
    <button className="button ghost" type="button" onClick={() => onToggle(interest.id)}>
      {interest.enabled ? "Disable" : "Enable"}
    </button>
    <button className="button danger" type="button" onClick={() => onRemove(interest.id)}>
      Delete
    </button>
  </div>
);

export const InterestCard = ({ interest, onRemove, onToggle }: InterestCardProps) => {
  const showOfficialLinks = hasInterestDetails(interest);

  return (
    <article className={`card ${interest.enabled ? "" : "disabled"}`}>
      <div className="card-main">
        <div>
          <h3>{interest.name}</h3>
          <InterestBadges interest={interest} />
        </div>
        <p>{interest.notes || "No notes yet."}</p>
        {showOfficialLinks ? <OfficialLinks interest={interest} /> : null}
      </div>
      <InterestActions interest={interest} onRemove={onRemove} onToggle={onToggle} />
    </article>
  );
};
