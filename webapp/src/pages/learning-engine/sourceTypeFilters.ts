import { type SavedCollectionUpdate, type SourceType, type Update } from "./types";

export type SourceTypeFilter = SourceType | "all";

type SourceTypeFilterOption = {
  label: string;
  value: SourceTypeFilter;
};

const sourceTypeLabels: Record<SourceType, string> = {
  feed: "Feeds",
  page: "Pages",
  spotify_podcast: "Spotify podcasts",
  twitter_account: "X/Twitter accounts",
  youtube_channel: "YouTube channels",
};

export const sourceTypeFilterOptions: SourceTypeFilterOption[] = [
  { label: "All source types", value: "all" },
  { label: sourceTypeLabels.feed, value: "feed" },
  { label: sourceTypeLabels.page, value: "page" },
  { label: sourceTypeLabels.youtube_channel, value: "youtube_channel" },
  { label: sourceTypeLabels.twitter_account, value: "twitter_account" },
  { label: sourceTypeLabels.spotify_podcast, value: "spotify_podcast" },
];

export const sourceTypeFilterLabel = (sourceTypeFilter: SourceTypeFilter): string =>
  sourceTypeFilter === "all" ? "All source types" : sourceTypeLabels[sourceTypeFilter];

export const filterUpdatesBySourceType = (
  updates: Update[],
  sourceTypeFilter: SourceTypeFilter,
): Update[] => {
  if (sourceTypeFilter === "all") {
    return updates;
  }

  return updates.filter((update) => update.source_interest.source_type === sourceTypeFilter);
};

export const filterSavedUpdatesBySourceType = (
  savedUpdates: SavedCollectionUpdate[],
  sourceTypeFilter: SourceTypeFilter,
): SavedCollectionUpdate[] => {
  if (sourceTypeFilter === "all") {
    return savedUpdates;
  }

  return savedUpdates.filter(
    (savedUpdate) => savedUpdate.update.source_interest.source_type === sourceTypeFilter,
  );
};
