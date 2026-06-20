import { type ChangeEvent, useRef } from "react";

import { InterestCard } from "./InterestCard";
import { type Interest, type SaveStatus } from "./types";

type InterestsPanelProps = {
  interests: Interest[];
  isExporting: boolean;
  isImporting: boolean;
  isOffline: boolean;
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

const activeInterestCount = (interests: Interest[]): number =>
  interests.filter((interest) => interest.enabled).length;

const visibleSourceCount = (interests: Interest[]): number =>
  interests.reduce(
    (total, interest) =>
      total + interest.sources.filter((source) => source.deletedAt == null).length,
    0,
  );

const interestSummary = (interests: Interest[]): string => {
  const activeCount = activeInterestCount(interests);
  const sourceCount = visibleSourceCount(interests);

  return `${activeCount} active of ${interests.length} interests · ${sourceCount} sources tracked`;
};

const SaveStatusBadge = ({
  isOffline,
  saveError,
  saveStatus,
}: {
  isOffline: boolean;
  saveError: string | null;
  saveStatus: SaveStatus;
}) => {
  if (isOffline) {
    return <span className="save-status failed">Offline</span>;
  }

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
  isOffline: boolean;
  onExportInterests: () => void;
  onImportInterests: (file: File) => void;
};

const importConfirmationMessage =
  "Importing this file will replace all current interests. Continue?";

const selectedImportFile = (input: HTMLInputElement): File | null =>
  input.files === null ? null : input.files.item(0);

const exportButtonLabel = (isExporting: boolean, isOffline: boolean): string => {
  if (isOffline) {
    return "Connect to export";
  }

  return isExporting ? "Exporting..." : "Export";
};

const importButtonLabel = (isImporting: boolean, isOffline: boolean): string => {
  if (isOffline) {
    return "Connect to import";
  }

  return isImporting ? "Importing..." : "Import";
};

const exportButtonTitle = (isOffline: boolean): string | undefined =>
  isOffline ? "Connect to export interests" : undefined;

const importButtonTitle = (isOffline: boolean): string | undefined =>
  isOffline ? "Connect to import interests" : undefined;

const transferButtonDisabled = (isPending: boolean, isOffline: boolean): boolean =>
  isPending || isOffline;

const openImportPicker = (input: HTMLInputElement | null): void => {
  if (input === null) {
    return;
  }

  input.click();
};

type InterestTransferButtonProps = {
  disabled: boolean;
  label: string;
  onClick: () => void;
  title: string | undefined;
};

const InterestTransferButton = ({
  disabled,
  label,
  onClick,
  title,
}: InterestTransferButtonProps) => (
  <button
    className="button ghost compact"
    disabled={disabled}
    title={title}
    type="button"
    onClick={onClick}
  >
    {label}
  </button>
);

type InterestImportControlProps = {
  isImporting: boolean;
  isOffline: boolean;
  onImportInterests: (file: File) => void;
};

const InterestImportControl = ({
  isImporting,
  isOffline,
  onImportInterests,
}: InterestImportControlProps) => {
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
    <>
      <InterestTransferButton
        disabled={transferButtonDisabled(isImporting, isOffline)}
        label={importButtonLabel(isImporting, isOffline)}
        onClick={() => openImportPicker(fileInputRef.current)}
        title={importButtonTitle(isOffline)}
      />
      <input
        ref={fileInputRef}
        className="visually-hidden"
        type="file"
        accept="application/json,.json"
        onChange={handleImportSelection}
      />
    </>
  );
};

const InterestTransferControls = ({
  isExporting,
  isImporting,
  isOffline,
  onExportInterests,
  onImportInterests,
}: InterestTransferControlsProps) => {
  return (
    <div className="interest-transfer-actions" aria-label="Interest import and export">
      <InterestTransferButton
        disabled={transferButtonDisabled(isExporting, isOffline)}
        label={exportButtonLabel(isExporting, isOffline)}
        onClick={onExportInterests}
        title={exportButtonTitle(isOffline)}
      />
      <InterestImportControl
        isImporting={isImporting}
        isOffline={isOffline}
        onImportInterests={onImportInterests}
      />
    </div>
  );
};

type InterestCardsProps = {
  interests: Interest[];
  isOffline: boolean;
  loadError: string | null;
  onEditInterest: (id: string) => void;
  onRemoveInterest: (id: string) => void;
  onToggleInterest: (id: string) => void;
};

const InterestCards = ({
  interests,
  isOffline,
  loadError,
  onEditInterest,
  onRemoveInterest,
  onToggleInterest,
}: InterestCardsProps) => (
  <div className="cards" aria-live="polite">
    {loadError !== null ? null : interests.length === 0 ? (
      <p className="empty">No interests yet. Create one with as many sources as it needs.</p>
    ) : (
      interests.map((interest) => (
        <InterestCard
          interest={interest}
          isOffline={isOffline}
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
  isOffline,
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
        <p className="panel-copy interest-panel-summary">{interestSummary(interests)}</p>
      </div>
      <div className="panel-header-actions">
        <InterestTransferControls
          isExporting={isExporting}
          isImporting={isImporting}
          isOffline={isOffline}
          onExportInterests={onExportInterests}
          onImportInterests={onImportInterests}
        />
        <SaveStatusBadge isOffline={isOffline} saveError={saveError} saveStatus={saveStatus} />
      </div>
    </div>

    <LoadError loadError={loadError} />

    <InterestCards
      interests={interests}
      isOffline={isOffline}
      loadError={loadError}
      onEditInterest={onEditInterest}
      onRemoveInterest={onRemoveInterest}
      onToggleInterest={onToggleInterest}
    />
  </section>
);
