import { type ChangeEvent } from "react";

import { BookmarkIcon, HeartIcon } from "./CollectionActionIcons";
import { type Collection, type Update, type UpdatesPayload } from "./types";
import { UpdateSourceAvatar } from "./UpdateSourceAvatar";

type UpdatesPageProps = {
  days: number;
  isChecking: boolean;
  isOffline: boolean;
  isRemovingSavedUpdate: boolean;
  isSavingToCollection: boolean;
  collections: Collection[];
  onDaysChange: (days: number) => void;
  onRefresh: () => void;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
  onSaveUpdateToCollection: (collectionId: string, update: Update) => void;
  updates: UpdatesPayload | null;
  updatesError: string | null;
};

type UpdateGroup = {
  interestName: string;
  updates: Update[];
};

type UpdateCollectionActionProps = {
  collections: Collection[];
  isRemovingSavedUpdate: boolean;
  isSavingToCollection: boolean;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
  onSaveUpdateToCollection: (collectionId: string, update: Update) => void;
  update: Update;
};

type CollectionSaveButtonProps = Omit<UpdateCollectionActionProps, "collections"> & {
  collection: Collection;
};

type CollectionToggleAction = {
  isSaved: boolean;
  label: string;
  run: () => void;
};

const updateDayOptions = [2, 7, 14, 30] as const;

const groupUpdates = (updates: Update[]): UpdateGroup[] => {
  const groups = new Map<string, Update[]>();

  updates.forEach((update) => {
    const interestName = update.source_interest.interest_name;
    const group = groups.get(interestName) ?? [];
    groups.set(interestName, [...group, update]);
  });

  return [...groups.entries()].map(([interestName, groupedUpdates]) => ({
    interestName,
    updates: groupedUpdates,
  }));
};

const updateKey = (update: Update): string =>
  `${update.source_interest.interest_name}-${update.source_interest.source_url}-${update.url}`;

const updateWindowLabel = (days: number): string =>
  days === 1 ? "the last day" : `the last ${days} days`;

const publishedLabelFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

const publishedLabel = (published: Date | undefined): string | null => {
  if (published === undefined) {
    return null;
  }

  return publishedLabelFormatter.format(published);
};

const updateDescription = (summary: string | null | undefined): string | null => {
  const description = summary?.trim();

  return description === undefined || description.length === 0 ? null : description;
};

const sourceIdentity = (update: Update): string =>
  update.source_interest.source_id === null || update.source_interest.source_id === undefined
    ? `url:${update.source_interest.source_url}`
    : `id:${update.source_interest.source_id}`;

const savedUpdateMatches = (
  savedUpdate: Collection["saved_updates"][number],
  update: Update,
): boolean =>
  savedUpdate.update.url === update.url &&
  savedUpdate.update.source_interest.source_type === update.source_interest.source_type &&
  sourceIdentity(savedUpdate.update) === sourceIdentity(update);

const savedUpdateInCollection = (
  collection: Collection,
  update: Update,
): Collection["saved_updates"][number] | undefined =>
  collection.saved_updates.find((savedUpdate) => savedUpdateMatches(savedUpdate, update));

const CollectionIcon = ({ collection }: { collection: Collection }) =>
  collection.id === "liked" ? (
    <HeartIcon className="icon-button-icon" />
  ) : (
    <BookmarkIcon className="icon-button-icon" />
  );

const savedButtonClassName = (isSaved: boolean): string =>
  isSaved ? "icon-button saved" : "icon-button";

const SavedCollectionMarker = ({ isSaved }: { isSaved: boolean }) =>
  isSaved ? <span className="icon-button-check" aria-hidden="true" /> : null;

const collectionToggleAction = ({
  collection,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
  update,
}: CollectionSaveButtonProps): CollectionToggleAction => {
  const savedUpdate = savedUpdateInCollection(collection, update);

  if (savedUpdate !== undefined) {
    return {
      isSaved: true,
      label: `Remove from ${collection.name}`,
      run: () => onRemoveSavedUpdate(collection.id, savedUpdate.update_key),
    };
  }

  return {
    isSaved: false,
    label: `Save to ${collection.name}`,
    run: () => onSaveUpdateToCollection(collection.id, update),
  };
};

const CollectionSaveButton = ({
  collection,
  isRemovingSavedUpdate,
  isSavingToCollection,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
  update,
}: CollectionSaveButtonProps) => {
  const action = collectionToggleAction({
    collection,
    isRemovingSavedUpdate,
    isSavingToCollection,
    onRemoveSavedUpdate,
    onSaveUpdateToCollection,
    update,
  });

  return (
    <button
      aria-label={action.label}
      aria-pressed={action.isSaved}
      className={savedButtonClassName(action.isSaved)}
      data-tooltip={action.label}
      disabled={isSavingToCollection || isRemovingSavedUpdate}
      onClick={action.run}
      title={action.label}
      type="button"
    >
      <CollectionIcon collection={collection} />
      <SavedCollectionMarker isSaved={action.isSaved} />
    </button>
  );
};

const CollectionSaveActions = ({
  collections,
  isRemovingSavedUpdate,
  isSavingToCollection,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
  update,
}: UpdateCollectionActionProps) => (
  <div className="update-collection-actions" aria-label="Save update to collection">
    {collections.map((collection) => (
      <CollectionSaveButton
        collection={collection}
        isRemovingSavedUpdate={isRemovingSavedUpdate}
        isSavingToCollection={isSavingToCollection}
        key={collection.id}
        onRemoveSavedUpdate={onRemoveSavedUpdate}
        onSaveUpdateToCollection={onSaveUpdateToCollection}
        update={update}
      />
    ))}
  </div>
);

const UpdateItem = ({
  collections,
  isRemovingSavedUpdate,
  isSavingToCollection,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
  update,
}: UpdateCollectionActionProps) => {
  const label = publishedLabel(update.published);
  const description = updateDescription(update.summary);

  return (
    <article className="update-item-card">
      <UpdateSourceAvatar update={update} />
      <div className="update-item-content">
        <a href={update.url} target="_blank" rel="noreferrer">
          {update.title ?? "Untitled update"}
        </a>
        {description === null ? null : <p className="update-item-description">{description}</p>}
        <div className="update-item-meta">
          <span>
            {update.source_interest.source_label} · {update.source_interest.source_type}
          </span>
          {label ? <span>{label}</span> : null}
        </div>
      </div>
      <CollectionSaveActions
        collections={collections}
        isRemovingSavedUpdate={isRemovingSavedUpdate}
        isSavingToCollection={isSavingToCollection}
        onRemoveSavedUpdate={onRemoveSavedUpdate}
        onSaveUpdateToCollection={onSaveUpdateToCollection}
        update={update}
      />
    </article>
  );
};

const UpdateGroupCard = ({
  collections,
  group,
  isRemovingSavedUpdate,
  isSavingToCollection,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
}: {
  collections: Collection[];
  group: UpdateGroup;
  isRemovingSavedUpdate: boolean;
  isSavingToCollection: boolean;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
  onSaveUpdateToCollection: (collectionId: string, update: Update) => void;
}) => (
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
        <UpdateItem
          collections={collections}
          isRemovingSavedUpdate={isRemovingSavedUpdate}
          isSavingToCollection={isSavingToCollection}
          key={updateKey(update)}
          onRemoveSavedUpdate={onRemoveSavedUpdate}
          onSaveUpdateToCollection={onSaveUpdateToCollection}
          update={update}
        />
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
      <strong>
        {new Set(payload.updates.map((update) => update.source_interest.interest_name)).size}
      </strong>
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
  isOffline,
  isRemovingSavedUpdate,
  isSavingToCollection,
  collections,
  onDaysChange,
  onRefresh,
  onRemoveSavedUpdate,
  onSaveUpdateToCollection,
  updates,
  updatesError,
}: UpdatesPageProps) => {
  const groups = groupUpdates(updates?.updates ?? []);

  return (
    <section id="updates" className="panel updates-page" aria-label="Updates">
      <div className="panel-header row">
        <div className="updates-header-summary">
          <p className="section-label">Updates</p>
          {updates !== null && <UpdatesSummary payload={updates} />}
        </div>
        <div className="updates-header-actions">
          <UpdateDaysSelect days={days} onDaysChange={onDaysChange} />
          <button
            className="button primary"
            type="button"
            onClick={onRefresh}
            disabled={isChecking || isOffline}
            title={isOffline ? "Connect to refresh updates" : undefined}
          >
            {isOffline ? "Connect to refresh" : isChecking ? "Refreshing..." : "Refresh"}
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
          <section className="updates-feed" aria-label="Updates feed">
            <SourceErrors payload={updates} />
            {groups.length === 0 ? (
              <EmptyUpdates days={days} />
            ) : (
              groups.map((group) => (
                <UpdateGroupCard
                  collections={collections}
                  group={group}
                  isRemovingSavedUpdate={isRemovingSavedUpdate}
                  isSavingToCollection={isSavingToCollection}
                  key={group.interestName}
                  onRemoveSavedUpdate={onRemoveSavedUpdate}
                  onSaveUpdateToCollection={onSaveUpdateToCollection}
                />
              ))
            )}
          </section>
        </div>
      )}
    </section>
  );
};
