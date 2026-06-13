import { useQuery } from "@tanstack/react-query";
import { type Dispatch, type FormEvent, useEffect, useReducer, useState } from "react";

import { resolveSourceImage } from "./api";
import {
  createDraftSource,
  createEmptyInterestDraft,
  createInterestDraft,
  priorityOptions,
  sourceTypeOptions,
} from "./interestForm";
import {
  type Interest,
  type InterestDraft,
  type InterestSource,
  type Priority,
  type SourceImagePayload,
  type SourceType,
} from "./types";

type InterestEditorProps = {
  interest: Interest | null;
  isOffline: boolean;
  onCancelEdit: () => void;
  onCreateInterest: (draft: InterestDraft) => void;
  onUpdateInterest: (draft: InterestDraft) => void;
};

const sourceImagePreviewDelayMs = 450;

type DraftAction =
  | { type: "addSource" }
  | { type: "removeSource"; id: string }
  | { type: "setDescription"; description: string }
  | { type: "setEnabled"; enabled: boolean }
  | { type: "setName"; name: string }
  | { type: "setPriority"; priority: Priority }
  | { type: "setSourceEnabled"; enabled: boolean; id: string }
  | { type: "setSourceIgnoreKeywords"; id: string; ignoreKeywords: string[] }
  | { type: "setSourceImageUrl"; id: string; imageUrl: string }
  | { type: "setSourceLabel"; id: string; label: string }
  | { type: "setSourceType"; id: string; sourceType: SourceType }
  | { type: "setSourceUrl"; id: string; url: string };
type DraftDispatch = Dispatch<DraftAction>;

const updateSource = (
  sources: InterestSource[],
  id: string,
  update: (source: InterestSource) => InterestSource,
): InterestSource[] => sources.map((source) => (source.id === id ? update(source) : source));

// fallow-ignore-next-line complexity
const draftReducer = (draft: InterestDraft, action: DraftAction): InterestDraft => {
  switch (action.type) {
    case "addSource":
      return { ...draft, sources: [...draft.sources, createDraftSource()] };
    case "removeSource":
      return {
        ...draft,
        sources: draft.sources.map((source) =>
          source.id === action.id ? { ...source, deletedAt: new Date().toISOString() } : source,
        ),
      };
    case "setDescription":
      return { ...draft, description: action.description };
    case "setEnabled":
      return { ...draft, enabled: action.enabled };
    case "setName":
      return { ...draft, name: action.name };
    case "setPriority":
      return { ...draft, priority: action.priority };
    case "setSourceEnabled":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          enabled: action.enabled,
        })),
      };
    case "setSourceIgnoreKeywords":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          ignoreKeywords: action.ignoreKeywords,
        })),
      };
    case "setSourceImageUrl":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          imageUrl: action.imageUrl,
        })),
      };
    case "setSourceLabel":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          label: action.label,
        })),
      };
    case "setSourceType":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          type: action.sourceType,
        })),
      };
    case "setSourceUrl":
      return {
        ...draft,
        sources: updateSource(draft.sources, action.id, (source) => ({
          ...source,
          url: action.url,
        })),
      };
  }
};

const visibleSources = (draft: InterestDraft): InterestSource[] =>
  draft.sources.filter((source) => source.deletedAt == null);

const hasValidSource = (draft: InterestDraft): boolean =>
  visibleSources(draft).some((source) => source.url.trim());

const isValidDraft = (draft: InterestDraft): boolean =>
  draft.name.trim() !== "" && hasValidSource(draft);

const sourceDisplayName = (source: InterestSource, index: number): string =>
  source.label.trim() || `Source ${index + 1}`;

const keywordText = (keywords: string[]): string => keywords.join(", ");

const parseKeywordText = (text: string): string[] =>
  text
    .split(",")
    .map((keyword) => keyword.trim())
    .filter(Boolean);

const trimmed = (value: string | null | undefined): string => value?.trim() ?? "";

const useDebouncedValue = (value: string, delayMs: number): string => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [delayMs, value]);

  return debouncedValue;
};

const canResolveSourceImage = (manualImageUrl: string, sourceUrl: string): boolean =>
  manualImageUrl === "" && sourceUrl !== "";

const sourceImageUrl = (payload: SourceImagePayload | undefined): string =>
  trimmed(payload?.imageUrl);

const SourceImage = ({ imageUrl }: { imageUrl: string }) => (
  <img src={imageUrl} alt="" loading="lazy" />
);

type PreviewMessage = {
  text: string;
  visible: boolean;
};

const firstVisibleMessage = (messages: PreviewMessage[]): string | null =>
  messages.find((message) => message.visible)?.text ?? null;

const isNoImageFound = (imageUrl: string, isFetched: boolean): boolean =>
  isFetched && imageUrl === "";

const SourceImagePreviewMessage = ({ message }: { message: string | null }) =>
  message === null ? null : <span className="source-image-preview-note">{message}</span>;

const OptionalSourceImage = ({ imageUrl }: { imageUrl: string }) =>
  imageUrl === "" ? null : <SourceImage imageUrl={imageUrl} />;

const previewableImageUrl = (imageUrl: string, message: string | null): string =>
  message === null ? imageUrl : "";

const SourceImageManualPreview = ({ imageUrl }: { imageUrl: string }) => (
  <div className="source-image-preview">
    <span>Preview Image</span>
    <SourceImage imageUrl={imageUrl} />
  </div>
);

const SourceImageOfflinePreview = () => (
  <div className="source-image-preview">
    <span>Preview Image</span>
    <span className="source-image-preview-note">Connect to preview image</span>
  </div>
);

const SourceImagePreviewResult = ({
  imageUrl,
  isDebouncing,
  isError,
  isFetched,
  isFetching,
}: {
  imageUrl: string;
  isDebouncing: boolean;
  isError: boolean;
  isFetched: boolean;
  isFetching: boolean;
}) => {
  const message = firstVisibleMessage([
    { text: "Loading...", visible: isDebouncing },
    { text: "Loading...", visible: isFetching },
    { text: "Image preview unavailable", visible: isError },
    { text: "No image found", visible: isNoImageFound(imageUrl, isFetched) },
  ]);

  return (
    <div className="source-image-preview">
      <span>Preview Image</span>
      <SourceImagePreviewMessage message={message} />
      <OptionalSourceImage imageUrl={previewableImageUrl(imageUrl, message)} />
    </div>
  );
};

const canQuerySourceImage = (
  isOffline: boolean,
  manualImageUrl: string,
  sourceUrl: string,
): boolean => !isOffline && canResolveSourceImage(manualImageUrl, sourceUrl);

const SourceImagePreview = ({
  isOffline,
  source,
}: {
  isOffline: boolean;
  source: InterestSource;
}) => {
  const manualImageUrl = trimmed(source.imageUrl);
  const sourceUrl = source.url.trim();
  const debouncedSourceUrl = useDebouncedValue(sourceUrl, sourceImagePreviewDelayMs);
  const imageQuery = useQuery({
    enabled: canQuerySourceImage(isOffline, manualImageUrl, debouncedSourceUrl),
    queryFn: () => resolveSourceImage({ type: source.type, url: debouncedSourceUrl }),
    queryKey: ["learning-engine", "source-image", source.type, debouncedSourceUrl] as const,
  });
  const resolvedImageUrl = sourceImageUrl(imageQuery.data);
  const isDebouncing = sourceUrl !== debouncedSourceUrl;

  if (manualImageUrl !== "") {
    return <SourceImageManualPreview imageUrl={manualImageUrl} />;
  }

  if (sourceUrl === "") {
    return null;
  }

  if (isOffline) {
    return <SourceImageOfflinePreview />;
  }

  return (
    <SourceImagePreviewResult
      imageUrl={resolvedImageUrl}
      isDebouncing={isDebouncing}
      isError={imageQuery.isError}
      isFetched={imageQuery.isFetched}
      isFetching={imageQuery.isFetching}
    />
  );
};

const BasicInterestFields = ({
  dispatch,
  draft,
}: {
  dispatch: DraftDispatch;
  draft: InterestDraft;
}) => (
  <>
    <label>
      Name
      <input
        name="name"
        onChange={(event) => dispatch({ name: event.currentTarget.value, type: "setName" })}
        placeholder="TypeScript"
        required
        value={draft.name}
      />
    </label>

    <div className="split-fields">
      <label>
        Priority
        <select
          name="priority"
          onChange={(event) =>
            dispatch({ priority: event.currentTarget.value as Priority, type: "setPriority" })
          }
          value={draft.priority}
        >
          {priorityOptions.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </label>
      <label>
        Status
        <span className="toggle-control">
          <span>{draft.enabled ? "Enabled" : "Paused"}</span>
          <input
            checked={draft.enabled}
            name="enabled"
            onChange={(event) =>
              dispatch({ enabled: event.currentTarget.checked, type: "setEnabled" })
            }
            type="checkbox"
          />
        </span>
      </label>
    </div>

    <label>
      Description
      <textarea
        name="description"
        onChange={(event) =>
          dispatch({ description: event.currentTarget.value, type: "setDescription" })
        }
        placeholder="What information about this topic belongs in briefings?"
        required
        value={draft.description}
      />
    </label>
  </>
);

const SourceEditorCard = ({
  dispatch,
  index,
  isOffline,
  source,
  sourcesCount,
}: {
  dispatch: DraftDispatch;
  index: number;
  isOffline: boolean;
  source: InterestSource;
  sourcesCount: number;
}) => (
  <section className="source-editor-card">
    <div className="source-editor-title">
      <strong>{sourceDisplayName(source, index)}</strong>
      <button
        className="button danger compact"
        disabled={sourcesCount === 1}
        type="button"
        onClick={() => dispatch({ id: source.id, type: "removeSource" })}
      >
        Remove
      </button>
    </div>
    <label>
      Source label
      <input
        name={`source-${source.id}-label`}
        onChange={(event) =>
          dispatch({
            id: source.id,
            label: event.currentTarget.value,
            type: "setSourceLabel",
          })
        }
        placeholder="Official dev blog"
        required
        value={source.label}
      />
    </label>
    <div className="split-fields">
      <label>
        Source type
        <select
          name={`source-${source.id}-type`}
          onChange={(event) =>
            dispatch({
              id: source.id,
              sourceType: event.currentTarget.value as SourceType,
              type: "setSourceType",
            })
          }
          value={source.type}
        >
          {sourceTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Status
        <span className="toggle-control">
          <span>{source.enabled ? "Enabled" : "Paused"}</span>
          <input
            checked={source.enabled}
            name={`source-${source.id}-enabled`}
            onChange={(event) =>
              dispatch({
                enabled: event.currentTarget.checked,
                id: source.id,
                type: "setSourceEnabled",
              })
            }
            type="checkbox"
          />
        </span>
      </label>
    </div>
    <label>
      Source URL
      <input
        name={`source-${source.id}-url`}
        onChange={(event) =>
          dispatch({
            id: source.id,
            type: "setSourceUrl",
            url: event.currentTarget.value,
          })
        }
        placeholder="URL, @handle, channel ID, or Spotify show URI"
        required
        value={source.url}
      />
    </label>
    <label>
      Image URL
      <input
        name={`source-${source.id}-image-url`}
        onChange={(event) =>
          dispatch({
            id: source.id,
            imageUrl: event.currentTarget.value,
            type: "setSourceImageUrl",
          })
        }
        placeholder="https://example.com/avatar.png"
        value={source.imageUrl ?? ""}
      />
    </label>
    <SourceImagePreview isOffline={isOffline} source={source} />
    <label>
      Ignore keywords
      <input
        name={`source-${source.id}-ignore-keywords`}
        onChange={(event) =>
          dispatch({
            id: source.id,
            ignoreKeywords: parseKeywordText(event.currentTarget.value),
            type: "setSourceIgnoreKeywords",
          })
        }
        placeholder="nightly, webinar"
        value={keywordText(source.ignoreKeywords)}
      />
    </label>
  </section>
);

const SourcesEditor = ({
  dispatch,
  isOffline,
  sources,
}: {
  dispatch: DraftDispatch;
  isOffline: boolean;
  sources: InterestSource[];
}) => (
  <div className="sources-editor">
    <div className="source-editor-header">
      <div>
        <p className="section-label">Sources</p>
        <h3>Collection endpoints</h3>
      </div>
      <button
        className="button ghost compact"
        type="button"
        onClick={() => dispatch({ type: "addSource" })}
      >
        Add source
      </button>
    </div>

    {sources.map((source, index) => (
      <SourceEditorCard
        dispatch={dispatch}
        index={index}
        isOffline={isOffline}
        key={source.id}
        source={source}
        sourcesCount={sources.length}
      />
    ))}
  </div>
);

// fallow-ignore-next-line complexity
export const InterestEditor = ({
  interest,
  isOffline,
  onCancelEdit,
  onCreateInterest,
  onUpdateInterest,
}: InterestEditorProps) => {
  const initialDraft =
    interest === null ? createEmptyInterestDraft() : createInterestDraft(interest);
  const [draft, dispatch] = useReducer(draftReducer, initialDraft);
  const isEditing = interest !== null;
  const sources = visibleSources(draft);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();

    if (!isValidDraft(draft)) {
      return;
    }

    if (isEditing) {
      onUpdateInterest(draft);
      return;
    }

    onCreateInterest(draft);
  };

  return (
    <aside id="add" className="panel add-panel">
      <div className="panel-header row">
        <div>
          <p className="section-label">{isEditing ? "Editor" : "New interest"}</p>
          <h2>{isEditing ? "Edit interest" : "Create an interest"}</h2>
        </div>
        {isEditing ? (
          <button className="button ghost compact" type="button" onClick={onCancelEdit}>
            New
          </button>
        ) : null}
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <BasicInterestFields dispatch={dispatch} draft={draft} />
        <SourcesEditor dispatch={dispatch} isOffline={isOffline} sources={sources} />

        <button
          className="button primary"
          disabled={!isValidDraft(draft) || isOffline}
          title={isOffline ? "Connect to save interests" : undefined}
          type="submit"
        >
          {isOffline ? "Connect to save" : isEditing ? "Save changes" : "Create interest"}
        </button>
      </form>
    </aside>
  );
};
