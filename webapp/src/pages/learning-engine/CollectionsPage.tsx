import { useState } from "react";

import { TrashIcon } from "./CollectionActionIcons";
import {
  filterSavedUpdatesBySourceType,
  type SourceTypeFilter,
  sourceTypeFilterLabel,
} from "./sourceTypeFilters";
import { SourceTypeFilterSelect } from "./SourceTypeFilterSelect";
import { type Collection, type SavedCollectionUpdate } from "./types";
import { UpdateSourceAvatar } from "./UpdateSourceAvatar";

type CollectionsPageProps = {
  collections: Collection[];
  collectionsError: string | null;
  isLoadingCollections: boolean;
  isRemovingSavedUpdate: boolean;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
};

const savedAtFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

const CollectionSavedUpdate = ({
  collectionId,
  isRemovingSavedUpdate,
  onRemoveSavedUpdate,
  savedUpdate,
}: {
  collectionId: string;
  isRemovingSavedUpdate: boolean;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
  savedUpdate: SavedCollectionUpdate;
}) => (
  <article className="collection-update-card">
    <UpdateSourceAvatar update={savedUpdate.update} />
    <div className="collection-update-content">
      <a href={savedUpdate.update.url} rel="noreferrer" target="_blank">
        {savedUpdate.update.title ?? "Untitled update"}
      </a>
      <div className="update-item-meta">
        <span>
          {savedUpdate.update.source_interest.source_label} ·{" "}
          {savedUpdate.update.source_interest.source_type}
        </span>
        <span>Saved {savedAtFormatter.format(savedUpdate.saved_at)}</span>
      </div>
    </div>
    <button
      aria-label="Remove from collection"
      className="icon-button danger"
      data-tooltip="Remove from collection"
      disabled={isRemovingSavedUpdate}
      onClick={() => onRemoveSavedUpdate(collectionId, savedUpdate.update_key)}
      title="Remove from collection"
      type="button"
    >
      <TrashIcon className="icon-button-icon" />
    </button>
  </article>
);

const CollectionPanel = ({
  collection,
  isRemovingSavedUpdate,
  onRemoveSavedUpdate,
  sourceTypeFilter,
}: {
  collection: Collection;
  isRemovingSavedUpdate: boolean;
  onRemoveSavedUpdate: (collectionId: string, updateKey: string) => void;
  sourceTypeFilter: SourceTypeFilter;
}) => {
  const visibleSavedUpdates = filterSavedUpdatesBySourceType(
    collection.saved_updates,
    sourceTypeFilter,
  );

  return (
    <section className="collection-panel" aria-label={collection.name}>
      <div className="collection-panel-header">
        <div>
          <h3>{collection.name}</h3>
          <p>
            {visibleSavedUpdates.length} saved{" "}
            {visibleSavedUpdates.length === 1 ? "update" : "updates"}
          </p>
        </div>
      </div>
      {visibleSavedUpdates.length === 0 ? (
        <div className="updates-callout empty">
          <strong>No saved updates</strong>
          <span>
            {sourceTypeFilter === "all"
              ? "Save updates from the Updates page to collect them here."
              : `No saved ${sourceTypeFilterLabel(sourceTypeFilter).toLowerCase()} updates in this collection.`}
          </span>
        </div>
      ) : (
        <div className="collection-update-list">
          {visibleSavedUpdates.map((savedUpdate) => (
            <CollectionSavedUpdate
              collectionId={collection.id}
              isRemovingSavedUpdate={isRemovingSavedUpdate}
              key={`${collection.id}-${savedUpdate.update_key}`}
              onRemoveSavedUpdate={onRemoveSavedUpdate}
              savedUpdate={savedUpdate}
            />
          ))}
        </div>
      )}
    </section>
  );
};

export const CollectionsPage = ({
  collections,
  collectionsError,
  isLoadingCollections,
  isRemovingSavedUpdate,
  onRemoveSavedUpdate,
}: CollectionsPageProps) => {
  const [sourceTypeFilter, setSourceTypeFilter] = useState<SourceTypeFilter>("all");

  return (
    <section className="panel collections-page" aria-label="Collections">
      <div className="panel-header row">
        <div>
          <p className="section-label">Collections</p>
          <h2>Saved updates</h2>
        </div>
        <SourceTypeFilterSelect
          label="Source type"
          onChange={setSourceTypeFilter}
          value={sourceTypeFilter}
        />
      </div>

      {collectionsError !== null ? (
        <div className="updates-callout error">
          <strong>Could not load collections</strong>
          <span>{collectionsError}</span>
        </div>
      ) : null}

      {isLoadingCollections ? (
        <div className="updates-callout loading">
          <strong>Loading collections...</strong>
          <span>Reading saved updates from local storage.</span>
        </div>
      ) : null}

      <div className="collections-grid">
        {collections.map((collection) => (
          <CollectionPanel
            collection={collection}
            isRemovingSavedUpdate={isRemovingSavedUpdate}
            key={collection.id}
            onRemoveSavedUpdate={onRemoveSavedUpdate}
            sourceTypeFilter={sourceTypeFilter}
          />
        ))}
      </div>
    </section>
  );
};
