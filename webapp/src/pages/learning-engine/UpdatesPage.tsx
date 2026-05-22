import { type ChangeEvent, useState } from "react";

import { type Update } from "./schemas";
import { type UpdatesPayload } from "./types";

type UpdatesPageProps = {
  days: number;
  isChecking: boolean;
  onDaysChange: (days: number) => void;
  onRefresh: () => void;
  updates: UpdatesPayload | null;
  updatesError: string | null;
};

type UpdateGroup = {
  interestName: string;
  updates: Update[];
};

const updateDayOptions = [2, 7, 14, 30] as const;

const groupUpdates = (updates: Update[]): UpdateGroup[] => {
  const groups = new Map<string, Update[]>();

  updates.forEach((update) => {
    const group = groups.get(update.interest_name) ?? [];
    groups.set(update.interest_name, [...group, update]);
  });

  return [...groups.entries()].map(([interestName, groupedUpdates]) => ({
    interestName,
    updates: groupedUpdates,
  }));
};

const updateKey = (update: Update): string =>
  `${update.interest_name}-${update.source_url}-${update.url}`;

const updateWindowLabel = (days: number): string =>
  days === 1 ? "the last day" : `the last ${days} days`;

const sourceInitial = (label: string): string => label.trim().charAt(0).toUpperCase() || "•";

const SourceAvatar = ({ update }: { update: Update }) => {
  const [imageFailed, setImageFailed] = useState(false);
  const imageUrl = update.source_image_url?.trim();
  const showImage = imageUrl !== undefined && imageUrl !== "" && !imageFailed;

  if (!showImage) {
    return (
      <span className="source-avatar fallback" aria-hidden="true">
        {sourceInitial(update.source_label)}
      </span>
    );
  }

  return (
    <img
      className="source-avatar"
      src={imageUrl}
      alt=""
      loading="lazy"
      onError={() => setImageFailed(true)}
    />
  );
};

const UpdateItem = ({ update }: { update: Update }) => (
  <article className="update-item-card">
    <SourceAvatar update={update} />
    <div className="update-item-content">
      <div className="update-item-meta">
        <span>
          {update.source_label} · {update.source_type}
        </span>
        {update.published ? <span>{update.published}</span> : null}
      </div>
      <a href={update.url} target="_blank" rel="noreferrer">
        {update.title ?? "Untitled update"}
      </a>
    </div>
  </article>
);

const UpdateGroupCard = ({ group }: { group: UpdateGroup }) => (
  <section className="update-group">
    <div className="update-group-header">
      <div>
        <h3>{group.interestName}</h3>
        <p>
          {group.updates.length} {group.updates.length === 1 ? "update" : "updates"}
        </p>
      </div>
    </div>
    <div className="update-items">
      {group.updates.map((update) => (
        <UpdateItem key={updateKey(update)} update={update} />
      ))}
    </div>
  </section>
);

const UpdatesSummary = ({ payload }: { payload: UpdatesPayload }) => (
  <aside className="updates-summary">
    <div className="summary-box">
      <strong>{payload.updates.length}</strong>
      <span>updates found</span>
    </div>
    <div className="summary-box">
      <strong>{payload.sources_checked}</strong>
      <span>sources checked</span>
    </div>
    <div className="summary-box">
      <strong>{new Set(payload.updates.map((update) => update.interest_name)).size}</strong>
      <span>interests with updates</span>
    </div>
  </aside>
);

const sourceErrorKey = (error: UpdatesPayload["errors"][number]): string =>
  `${error.interest_name}-${error.source_label}-${error.source_url}`;

const SourceErrorItem = ({ error }: { error: UpdatesPayload["errors"][number] }) => (
  <article className="source-error-item">
    <div>
      <strong>{error.interest_name}</strong>
      <span>
        {error.source_label} · {error.source_url}
      </span>
    </div>
    <details>
      <summary>More details</summary>
      <p>{error.error}</p>
    </details>
  </article>
);

const SourceErrors = ({ payload }: { payload: UpdatesPayload }) =>
  payload.errors.length === 0 ? null : (
    <div className="updates-callout warning">
      <strong>
        {payload.errors.length} source {payload.errors.length === 1 ? "error" : "errors"}
      </strong>
      <span>Successful sources still appear below. Review the affected source settings.</span>
      <div className="source-error-list">
        {payload.errors.map((error) => (
          <SourceErrorItem error={error} key={sourceErrorKey(error)} />
        ))}
      </div>
    </div>
  );

const RequestError = ({ updatesError }: { updatesError: string | null }) =>
  updatesError === null ? null : (
    <div className="updates-callout error">
      <strong>Could not load updates</strong>
      <span>{updatesError}</span>
    </div>
  );

const EmptyUpdates = ({ days }: { days: number }) => (
  <div className="updates-callout empty">
    <strong>No updates found</strong>
    <span>The enabled sources did not publish matching updates in {updateWindowLabel(days)}.</span>
  </div>
);

const UpdateDaysSelect = ({
  days,
  onDaysChange,
}: {
  days: number;
  onDaysChange: (days: number) => void;
}) => {
  const handleChange = (event: ChangeEvent<HTMLSelectElement>): void => {
    onDaysChange(Number(event.target.value));
  };

  return (
    <label className="days-select-control">
      <span>Show</span>
      <select value={days} onChange={handleChange} aria-label="Update time window">
        {updateDayOptions.map((option) => (
          <option key={option} value={option}>
            Last {option} days
          </option>
        ))}
      </select>
    </label>
  );
};

// fallow-ignore-next-line complexity
export const UpdatesPage = ({
  days,
  isChecking,
  onDaysChange,
  onRefresh,
  updates,
  updatesError,
}: UpdatesPageProps) => {
  const groups = groupUpdates(updates?.updates ?? []);

  return (
    <section id="updates" className="panel updates-page">
      <div className="panel-header row">
        <div>
          <p className="section-label">Updates</p>
          <h2>{updateWindowLabel(days)}</h2>
          <p className="panel-copy">Updates grouped by interest.</p>
        </div>
        <div className="updates-header-actions">
          <UpdateDaysSelect days={days} onDaysChange={onDaysChange} />
          <button
            className="button primary"
            type="button"
            onClick={onRefresh}
            disabled={isChecking}
          >
            {isChecking ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {isChecking && updates === null ? (
        <div className="updates-callout loading">
          <strong>Checking sources...</strong>
          <span>Collecting updates from enabled sources for {updateWindowLabel(days)}.</span>
        </div>
      ) : null}

      <RequestError updatesError={updatesError} />

      {updates === null ? null : (
        <div className="updates-layout">
          <UpdatesSummary payload={updates} />
          <div className="updates-feed">
            <SourceErrors payload={updates} />
            {groups.length === 0 ? (
              <EmptyUpdates days={days} />
            ) : (
              groups.map((group) => <UpdateGroupCard group={group} key={group.interestName} />)
            )}
          </div>
        </div>
      )}
    </section>
  );
};
