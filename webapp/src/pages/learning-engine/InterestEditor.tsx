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

const sourceTypeLabel = (sourceType: SourceType): string =>
  sourceTypeOptions.find((option) => option.value === sourceType)?.label ?? sourceType;

const sourceInitial = (label: string): string => label.trim().charAt(0).toUpperCase() || "S";

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

const canQuerySourceImage = (
  isOffline: boolean,
  manualImageUrl: string,
  sourceUrl: string,
): boolean => !isOffline && canResolveSourceImage(manualImageUrl, sourceUrl);

const useSourceHeaderImageUrl = ({
  isOffline,
  source,
}: {
  isOffline: boolean;
  source: InterestSource;
}): string => {
  const manualImageUrl = trimmed(source.imageUrl);
  const sourceUrl = source.url.trim();
  const debouncedSourceUrl = useDebouncedValue(sourceUrl, sourceImagePreviewDelayMs);
  const imageQuery = useQuery({
    enabled: canQuerySourceImage(isOffline, manualImageUrl, debouncedSourceUrl),
    queryFn: () => resolveSourceImage({ type: source.type, url: debouncedSourceUrl }),
    queryKey: ["signal-garden", "source-image", source.type, debouncedSourceUrl] as const,
  });
  const resolvedImageUrl = sourceImageUrl(imageQuery.data);

  if (manualImageUrl !== "") {
    return manualImageUrl;
  }

  return resolvedImageUrl;
};

const SourceHeaderImage = ({ imageUrl, label }: { imageUrl: string; label: string }) => {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const canShowImage = imageUrl !== "" && imageUrl !== failedImageUrl;

  if (canShowImage) {
    return (
      <span className="source-header-image">
        <img src={imageUrl} alt="" loading="lazy" onError={() => setFailedImageUrl(imageUrl)} />
      </span>
    );
  }

  return (
    <span className="source-header-image fallback" aria-hidden="true">
      {sourceInitial(label)}
    </span>
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

const SourceCoreFields = ({
  dispatch,
  source,
}: {
  dispatch: DraftDispatch;
  source: InterestSource;
}) => (
  <>
    <label>
      Label
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
    <label>
      URL
      <input
        name={`source-${source.id}-url`}
        onChange={(event) =>
          dispatch({
            id: source.id,
            type: "setSourceUrl",
            url: event.currentTarget.value,
          })
        }
        placeholder="Feed URL, page, @handle, or show URI"
        required
        value={source.url}
      />
      <span className="field-hint">
        Paste a feed, page, account handle, channel ID, or podcast URI.
      </span>
    </label>
    <label>
      Type
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
  </>
);

const SourceOptionFields = ({
  dispatch,
  source,
}: {
  dispatch: DraftDispatch;
  source: InterestSource;
}) => (
  <details className="source-options">
    <summary>Options</summary>
    <div className="source-options-fields">
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
        <span className="field-hint">Leave blank to let the engine find an image.</span>
      </label>
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
        <span className="field-hint">Comma-separated terms to skip during collection.</span>
      </label>
    </div>
  </details>
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
}) => {
  const [isExpanded, setIsExpanded] = useState(source.url.trim() === "");
  const headerImageUrl = useSourceHeaderImageUrl({ isOffline, source });
  const sourceName = sourceDisplayName(source, index);
  const fieldsId = `source-${source.id}-fields`;

  return (
    <section className={isExpanded ? "source-editor-card expanded" : "source-editor-card"}>
      <button
        aria-controls={fieldsId}
        aria-expanded={isExpanded}
        className="source-editor-title"
        type="button"
        onClick={() => setIsExpanded((expanded) => !expanded)}
      >
        <SourceHeaderImage imageUrl={headerImageUrl} label={sourceName} />
        <span className="source-editor-copy">
          <strong>{sourceName}</strong>
          <span className="source-editor-meta">
            {sourceTypeLabel(source.type)} · {source.enabled ? "Enabled" : "Paused"}
          </span>
        </span>
      </button>
      <div
        aria-hidden={!isExpanded}
        className="source-editor-collapse"
        id={fieldsId}
        inert={isExpanded ? undefined : true}
      >
        <div className="source-editor-fields">
          <SourceCoreFields dispatch={dispatch} source={source} />
          <SourceOptionFields dispatch={dispatch} source={source} />
          <button
            className="button danger compact"
            disabled={sourcesCount === 1}
            type="button"
            onClick={() => dispatch({ id: source.id, type: "removeSource" })}
          >
            Remove
          </button>
        </div>
      </div>
    </section>
  );
};

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
        <h3>Sources</h3>
        <p>
          {sources.length} {sources.length === 1 ? "endpoint" : "endpoints"}
        </p>
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
          <h2>{isEditing ? "Edit interest" : "Add interest"}</h2>
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
          {isOffline ? "Connect to save" : isEditing ? "Save changes" : "Add interest"}
        </button>
      </form>
    </aside>
  );
};
