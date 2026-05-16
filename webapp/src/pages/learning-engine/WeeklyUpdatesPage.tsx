import { type Update } from "./schemas";
import { type UpdatesPayload } from "./types";

type WeeklyUpdatesPageProps = {
  days: number;
  isChecking: boolean;
  onRefresh: () => void;
  updates: UpdatesPayload | null;
  updatesError: string | null;
};

type UpdateGroup = {
  interestName: string;
  updates: Update[];
};

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

const UpdateItem = ({ update }: { update: Update }) => (
  <article className="weekly-update-item">
    <div>
      <span>
        {update.source_label} · {update.source_type}
      </span>
      {update.published ? <span>{update.published}</span> : null}
    </div>
    <a href={update.url} target="_blank" rel="noreferrer">
      {update.title ?? "Untitled update"}
    </a>
  </article>
);

const UpdateGroupCard = ({ group }: { group: UpdateGroup }) => (
  <section className="weekly-update-group">
    <div className="weekly-group-header">
      <div>
        <h3>{group.interestName}</h3>
        <p>
          {group.updates.length} {group.updates.length === 1 ? "update" : "updates"}
        </p>
      </div>
    </div>
    <div className="weekly-update-items">
      {group.updates.map((update) => (
        <UpdateItem key={updateKey(update)} update={update} />
      ))}
    </div>
  </section>
);

const UpdatesSummary = ({ payload }: { payload: UpdatesPayload }) => (
  <aside className="weekly-summary">
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

const SourceErrors = ({ payload }: { payload: UpdatesPayload }) =>
  payload.errors.length === 0 ? null : (
    <div className="updates-callout warning">
      <strong>
        {payload.errors.length} source {payload.errors.length === 1 ? "error" : "errors"}
      </strong>
      <span>Successful sources still appear below. Review source settings if this repeats.</span>
    </div>
  );

const RequestError = ({ updatesError }: { updatesError: string | null }) =>
  updatesError === null ? null : (
    <div className="updates-callout error">
      <strong>Could not load weekly updates</strong>
      <span>{updatesError}</span>
    </div>
  );

const EmptyUpdates = () => (
  <div className="updates-callout empty">
    <strong>No updates found</strong>
    <span>The enabled sources did not publish matching updates in the last week.</span>
  </div>
);

// fallow-ignore-next-line complexity
export const WeeklyUpdatesPage = ({
  days,
  isChecking,
  onRefresh,
  updates,
  updatesError,
}: WeeklyUpdatesPageProps) => {
  const groups = groupUpdates(updates?.updates ?? []);

  return (
    <section id="updates" className="panel weekly-updates-page">
      <div className="panel-header row">
        <div>
          <p className="section-label">Weekly updates</p>
          <h2>Last {days} days</h2>
          <p className="panel-copy">
            A focused view of all updates grouped by interest. Refreshing checks the enabled sources
            with <code>/api/updates?days={days}</code>.
          </p>
        </div>
        <button className="button primary" type="button" onClick={onRefresh} disabled={isChecking}>
          {isChecking ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {isChecking && updates === null ? (
        <div className="updates-callout loading">
          <strong>Checking sources...</strong>
          <span>Collecting updates from enabled sources for the last week.</span>
        </div>
      ) : null}

      <RequestError updatesError={updatesError} />

      {updates === null ? null : (
        <div className="weekly-layout">
          <UpdatesSummary payload={updates} />
          <div className="weekly-feed">
            <SourceErrors payload={updates} />
            {groups.length === 0 ? (
              <EmptyUpdates />
            ) : (
              groups.map((group) => <UpdateGroupCard group={group} key={group.interestName} />)
            )}
          </div>
        </div>
      )}
    </section>
  );
};
