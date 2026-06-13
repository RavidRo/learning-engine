import { type ChangeEvent, useRef } from "react";

import { InterestCard } from "./InterestCard";
import { type Interest, type SaveStatus } from "./types";

type InterestsPanelProps = {
  interests: Interest[];
  isExporting: boolean;
  isImporting: boolean;
  loadError: string | null;
  onExportInterests: () => void;
  onEditInterest: (id: string) => void;
  onImportInterests: (file: File) => void;
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

type InterestTransferControlsProps = {
  isExporting: boolean;
  isImporting: boolean;
  onExportInterests: () => void;
  onImportInterests: (file: File) => void;
};

const importConfirmationMessage =
  "Importing this file will replace all current interests. Continue?";

const selectedImportFile = (input: HTMLInputElement): File | null =>
  input.files === null ? null : input.files.item(0);

const InterestTransferControls = ({
  isExporting,
  isImporting,
  onExportInterests,
  onImportInterests,
}: InterestTransferControlsProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImportSelection = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = selectedImportFile(event.currentTarget);
    event.currentTarget.value = "";

    if (file === null) {
      return;
    }

    if (!window.confirm(importConfirmationMessage)) {
      return;
    }

    onImportInterests(file);
  };

  return (
    <div className="interest-transfer-actions" aria-label="Interest import and export">
      <button
        className="button ghost compact"
        disabled={isExporting}
        type="button"
        onClick={onExportInterests}
      >
        {isExporting ? "Exporting..." : "Export"}
      </button>
      <button
        className="button ghost compact"
        disabled={isImporting}
        type="button"
        onClick={() => fileInputRef.current?.click()}
      >
        {isImporting ? "Importing..." : "Import"}
      </button>
      <input
        ref={fileInputRef}
        className="visually-hidden"
        type="file"
        accept="application/json,.json"
        onChange={handleImportSelection}
      />
    </div>
  );
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
  isExporting,
  isImporting,
  loadError,
  onExportInterests,
  onEditInterest,
  onImportInterests,
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
      <div className="panel-header-actions">
        <InterestTransferControls
          isExporting={isExporting}
          isImporting={isImporting}
          onExportInterests={onExportInterests}
          onImportInterests={onImportInterests}
        />
        <SaveStatusBadge saveError={saveError} saveStatus={saveStatus} />
      </div>
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
