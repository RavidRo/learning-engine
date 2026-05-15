import { type TechnologyUpdate, type TechnologyUpdatesPayload } from "./schemas";

type TechnologyUpdatesProps = {
  payload: TechnologyUpdatesPayload;
};

const CheckedFeedCount = ({ checked }: { checked: number }) => (
  <p>
    {checked} technology {checked === 1 ? "feed" : "feeds"} checked
  </p>
);

const UpdateItem = ({ update }: { update: TechnologyUpdate }) => (
  <article className="update-item" key={`${update.url}-${update.title ?? ""}`}>
    <strong>{update.interest_name}</strong>
    <a href={update.url} target="_blank" rel="noreferrer">
      {update.title ?? "Untitled update"}
    </a>
    {update.published ? <span>{update.published}</span> : null}
  </article>
);

const UpdatesList = ({ updates }: { updates: TechnologyUpdate[] }) =>
  updates.length === 0 ? (
    <p>No matching updates found.</p>
  ) : (
    updates.slice(0, 8).map((update) => <UpdateItem key={update.url} update={update} />)
  );

const FeedErrors = ({ errors }: { errors: string[] }) =>
  errors.length > 0 ? (
    <p className="updates-error">
      {errors.length} feed {errors.length === 1 ? "error" : "errors"} while checking updates.
    </p>
  ) : null;

export const TechnologyUpdates = ({ payload }: TechnologyUpdatesProps) => {
  const updates = payload.updates ?? [];
  const errors = payload.errors ?? [];
  const checked = payload.interests_checked ?? 0;

  return (
    <div className="updates-panel">
      <h3>Technology updates</h3>
      <CheckedFeedCount checked={checked} />
      <UpdatesList updates={updates} />
      <FeedErrors errors={errors} />
    </div>
  );
};
