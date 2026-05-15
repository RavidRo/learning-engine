import { type Update, type UpdatesPayload } from "./schemas";

type UpdatesPanelProps = {
  payload: UpdatesPayload;
};

const CheckedSourceCount = ({ checked }: { checked: number }) => (
  <p>
    {checked} {checked === 1 ? "source" : "sources"} checked
  </p>
);

const UpdateItem = ({ update }: { update: Update }) => (
  <article className="update-item" key={`${update.url}-${update.title ?? ""}`}>
    <strong>{update.interest_name}</strong>
    <span>
      {update.source_label} · {update.source_type}
    </span>
    <a href={update.url} target="_blank" rel="noreferrer">
      {update.title ?? "Untitled update"}
    </a>
    {update.published ? <span>{update.published}</span> : null}
  </article>
);

const UpdatesList = ({ updates }: { updates: Update[] }) =>
  updates.length === 0 ? (
    <p>No updates found.</p>
  ) : (
    updates.slice(0, 8).map((update) => <UpdateItem key={update.url} update={update} />)
  );

const SourceErrors = ({ errors }: { errors: UpdatesPayload["errors"] }) =>
  errors.length > 0 ? (
    <p className="updates-error">
      {errors.length} source {errors.length === 1 ? "error" : "errors"} while checking updates.
    </p>
  ) : null;

const RequestError = ({ error }: { error: string | undefined }) =>
  error === undefined ? null : <p className="updates-error">{error}</p>;

export const UpdatesPanel = ({ payload }: UpdatesPanelProps) => {
  const updates = payload.updates ?? [];
  const errors = payload.errors ?? [];
  const checked = payload.sources_checked ?? 0;

  return (
    <div className="updates-panel">
      <h3>Updates</h3>
      <RequestError error={payload.error} />
      <CheckedSourceCount checked={checked} />
      <UpdatesList updates={updates} />
      <SourceErrors errors={errors} />
    </div>
  );
};
