import { InterestCard } from "./InterestCard";
import { type Interest, type SaveStatus } from "./types";

type InterestsPanelProps = {
  interests: Interest[];
  loadError: string | null;
  onEditInterest: (id: string) => void;
  onRemoveInterest: (id: string) => void;
  onToggleInterest: (id: string) => void;
  saveError: string | null;
  saveStatus: SaveStatus;
};

const LoadError = ({ loadError }: { loadError: string | null }) =>
  loadError === null ? null : <p className="empty">Failed to load interests. {loadError}</p>;

const SaveStatusBadge = ({
  saveError,
  saveStatus,
}: {
  saveError: string | null;
  saveStatus: SaveStatus;
}) => {
  const labels: Record<SaveStatus, string> = {
    failed: `Save failed${saveError ? `: ${saveError}` : ""}`,
    idle: "Ready",
    saved: "Saved",
    saving: "Saving...",
  };

  return <span className={`save-status ${saveStatus}`}>{labels[saveStatus]}</span>;
};

type InterestCardsProps = {
  interests: Interest[];
  onEditInterest: (id: string) => void;
  onRemoveInterest: (id: string) => void;
  onToggleInterest: (id: string) => void;
};

const InterestCards = ({
  interests,
  onEditInterest,
  onRemoveInterest,
  onToggleInterest,
}: InterestCardsProps) => (
  <div className="cards" aria-live="polite">
    {interests.length === 0 ? (
      <p className="empty">No interests yet. Create one with as many sources as it needs.</p>
    ) : (
      interests.map((interest) => (
        <InterestCard
          interest={interest}
          key={interest.id}
          onEdit={onEditInterest}
          onRemove={onRemoveInterest}
          onToggle={onToggleInterest}
        />
      ))
    )}
  </div>
);

export const InterestsPanel = ({
  interests,
  loadError,
  onEditInterest,
  onRemoveInterest,
  onToggleInterest,
  saveError,
  saveStatus,
}: InterestsPanelProps) => (
  <section id="interests" className="panel list-panel">
    <div className="panel-header row">
      <div>
        <p className="section-label">Signal list</p>
        <h2>Your interests</h2>
      </div>
      <SaveStatusBadge saveError={saveError} saveStatus={saveStatus} />
    </div>

    <LoadError loadError={loadError} />

    <InterestCards
      interests={interests}
      onEditInterest={onEditInterest}
      onRemoveInterest={onRemoveInterest}
      onToggleInterest={onToggleInterest}
    />
  </section>
);
