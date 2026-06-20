import { PauseIcon, PencilIcon, PlayIcon, TrashIcon } from "./CollectionActionIcons";
import { SourceLinks } from "./SourceLinks";
import { type Interest } from "./types";

type InterestCardProps = {
  interest: Interest;
  isOffline: boolean;
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

const toggleInterestLabel = (interest: Interest): string =>
  `${interest.enabled ? "Pause" : "Resume"} ${interest.name}`;

const toggleInterestTooltip = (interest: Interest): string =>
  interest.enabled ? "Pause" : "Resume";

const ToggleInterestIcon = ({ enabled }: { enabled: boolean }) =>
  enabled ? <PauseIcon className="icon-button-icon" /> : <PlayIcon className="icon-button-icon" />;

const InterestActions = ({
  interest,
  isOffline,
  onEdit,
  onRemove,
  onToggle,
}: InterestCardProps) => (
  <div className="actions interest-actions" aria-label={`${interest.name} actions`}>
    <button
      aria-label={`Edit ${interest.name}`}
      className="icon-button"
      data-tooltip="Edit"
      title="Edit"
      type="button"
      onClick={() => onEdit(interest.id)}
    >
      <PencilIcon className="icon-button-icon" />
    </button>
    <button
      aria-label={toggleInterestLabel(interest)}
      className="icon-button"
      data-tooltip={toggleInterestTooltip(interest)}
      disabled={isOffline}
      title={isOffline ? "Connect to save interests" : undefined}
      type="button"
      onClick={() => onToggle(interest.id)}
    >
      <ToggleInterestIcon enabled={interest.enabled} />
    </button>
    <button
      aria-label={`Delete ${interest.name}`}
      className="icon-button danger"
      data-tooltip="Delete"
      disabled={isOffline}
      title={isOffline ? "Connect to save interests" : undefined}
      type="button"
      onClick={() => onRemove(interest.id)}
    >
      <TrashIcon className="icon-button-icon" />
    </button>
  </div>
);

const interestCardClassName = (interest: Interest): string =>
  `card interest-card ${interest.enabled ? "" : "disabled"}`;

const InterestStatusDot = ({ enabled }: { enabled: boolean }) => (
  <span aria-hidden="true" className={`interest-status-dot ${enabled ? "enabled" : "paused"}`} />
);

export const InterestCard = ({
  interest,
  isOffline,
  onEdit,
  onRemove,
  onToggle,
}: InterestCardProps) => {
  const showSources = hasSources(interest);

  return (
    <article className={interestCardClassName(interest)}>
      <div className="card-main">
        <div className="interest-card-top">
          <InterestStatusDot enabled={interest.enabled} />
          <div className="interest-title-group">
            <h3>{interest.name}</h3>
            <InterestBadges interest={interest} />
          </div>
        </div>
        <p>{interest.description || "No description yet."}</p>
        {showSources ? <SourceLinks interest={interest} /> : null}
      </div>
      <InterestActions
        interest={interest}
        isOffline={isOffline}
        onEdit={onEdit}
        onRemove={onRemove}
        onToggle={onToggle}
      />
    </article>
  );
};
