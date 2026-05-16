import {
  type Interest,
  type InterestDraft,
  type InterestFormValues,
  type InterestSource,
  type Priority,
  type SourceType,
} from "./types";

/** Converts a free-text label into a stable URL-safe identifier fragment. */
const slugify = (text: string): string => {
  const slug = text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || crypto.randomUUID();
};

/** Creates a blank source row for the interest editor. */
export const createDraftSource = (): InterestSource => ({
  deletedAt: null,
  enabled: true,
  id: crypto.randomUUID(),
  label: "",
  type: "feed",
  url: "",
});

/** Creates a blank interest draft for the shared create/edit editor. */
export const createEmptyInterestDraft = (): InterestDraft => ({
  description: "",
  enabled: true,
  id: null,
  name: "",
  priority: "medium",
  sources: [createDraftSource()],
});

/** Converts a persisted interest into an editable draft. */
export const createInterestDraft = (interest: Interest): InterestDraft => ({
  description: interest.description,
  enabled: interest.enabled,
  id: interest.id,
  name: interest.name,
  priority: interest.priority,
  sources: interest.sources
    .filter((source) => source.deletedAt == null)
    .map((source) => ({ ...source })),
});

/** Normalizes an editor draft into values that can be persisted. */
const normalizeInterestDraft = (draft: InterestDraft): InterestFormValues | null => {
  const name = draft.name.trim();

  if (!name) {
    return null;
  }

  return {
    description: draft.description.trim(),
    name,
    priority: draft.priority,
    sources: draft.sources
      .filter((source) => source.deletedAt == null)
      .map((source) => ({
        deletedAt: null,
        enabled: source.enabled,
        id: source.id ?? crypto.randomUUID(),
        label: source.label.trim() || "Source",
        type: source.type,
        url: source.url.trim(),
      }))
      .filter((source) => source.url),
  };
};

/** Creates a persisted interest from a valid editor draft. */
export const createInterest = (draft: InterestDraft): Interest | null => {
  const formValues = normalizeInterestDraft(draft);

  if (formValues === null) {
    return null;
  }

  const now = String(Date.now());

  return {
    deletedAt: null,
    description: formValues.description,
    enabled: draft.enabled,
    id: `${slugify(formValues.name)}-${now}`,
    name: formValues.name,
    priority: formValues.priority,
    sources: formValues.sources.map((source) => ({
      ...source,
      id: `${slugify(source.label)}-${crypto.randomUUID()}`,
    })),
  };
};

/** Applies a valid editor draft to an existing interest while preserving deleted sources. */
export const updateInterestFromDraft = (
  interest: Interest,
  draft: InterestDraft,
): Interest | null => {
  const formValues = normalizeInterestDraft(draft);

  if (formValues === null) {
    return null;
  }

  const visibleSourceIds = new Set(formValues.sources.map((source) => source.id));
  const deletedSources = interest.sources.filter(
    (source) => source.deletedAt != null && source.id !== null && !visibleSourceIds.has(source.id),
  );

  return {
    ...interest,
    description: formValues.description,
    enabled: draft.enabled,
    name: formValues.name,
    priority: formValues.priority,
    sources: [...formValues.sources, ...deletedSources],
  };
};

export const sourceTypeOptions: { label: string; value: SourceType }[] = [
  { label: "Feed", value: "feed" },
  { label: "Page", value: "page" },
  { label: "YouTube channel", value: "youtube_channel" },
  { label: "Twitter/X account", value: "twitter_account" },
  { label: "Spotify podcast", value: "spotify_podcast" },
];

export const priorityOptions: Priority[] = ["high", "medium", "low"];
