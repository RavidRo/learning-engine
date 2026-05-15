import { InterestCard } from "./InterestCard";
import { UpdatesPanel } from "./UpdatesPanel";
import { type Interest, type UpdatesPayload } from "./types";

type InterestsPanelProps = {
  interests: Interest[];
  isChecking: boolean;
  isSaving: boolean;
  loadError: string | null;
  onCheckUpdates: () => void;
  onRemoveInterest: (id: string) => void;
  onSaveInterests: () => void;
  onToggleInterest: (id: string) => void;
  updates: UpdatesPayload | null;
};

type PanelActionsProps = {
  isChecking: boolean;
  isSaving: boolean;
  onCheckUpdates: () => void;
  onSaveInterests: () => void;
};

const PanelActions = ({
  isChecking,
  isSaving,
  onCheckUpdates,
  onSaveInterests,
}: PanelActionsProps) => (
  <div className="header-actions">
    <button className="button ghost" type="button" onClick={onCheckUpdates} disabled={isChecking}>
      {isChecking ? "Checking..." : "Check updates"}
    </button>
    <button className="button ghost" type="button" onClick={onSaveInterests} disabled={isSaving}>
      {isSaving ? "Saving..." : "Save now"}
    </button>
  </div>
);

const LoadError = ({ loadError }: { loadError: string | null }) =>
  loadError === null ? null : <p className="empty">Failed to load interests. {loadError}</p>;

type InterestCardsProps = {
  interests: Interest[];
  onRemoveInterest: (id: string) => void;
  onToggleInterest: (id: string) => void;
};

const InterestCards = ({ interests, onRemoveInterest, onToggleInterest }: InterestCardsProps) => (
  <div className="cards" aria-live="polite">
    {interests.length === 0 ? (
      <p className="empty">No interests yet. Add one source to begin.</p>
    ) : (
      interests.map((interest) => (
        <InterestCard
          interest={interest}
          key={interest.id}
          onRemove={onRemoveInterest}
          onToggle={onToggleInterest}
        />
      ))
    )}
  </div>
);

export const InterestsPanel = ({
  interests,
  isChecking,
  isSaving,
  loadError,
  onCheckUpdates,
  onRemoveInterest,
  onSaveInterests,
  onToggleInterest,
  updates,
}: InterestsPanelProps) => (
  <section id="interests" className="panel list-panel">
    <div className="panel-header row">
      <div>
        <p className="section-label">Signal list</p>
        <h2>Your interests</h2>
      </div>
      <PanelActions
        isChecking={isChecking}
        isSaving={isSaving}
        onCheckUpdates={onCheckUpdates}
        onSaveInterests={onSaveInterests}
      />
    </div>

    <LoadError loadError={loadError} />
    {updates === null ? null : <UpdatesPanel payload={updates} />}

    <InterestCards
      interests={interests}
      onRemoveInterest={onRemoveInterest}
      onToggleInterest={onToggleInterest}
    />
  </section>
);
