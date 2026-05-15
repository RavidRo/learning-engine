import { type SubmitEvent } from "react";

type AddInterestFormProps = {
  onAddInterest: (form: HTMLFormElement) => void;
};

export const AddInterestForm = ({ onAddInterest }: AddInterestFormProps) => {
  const handleSubmit = (event: SubmitEvent<HTMLFormElement>): void => {
    event.preventDefault();
    onAddInterest(event.currentTarget);
  };

  return (
    <aside id="add" className="panel add-panel">
      <div className="panel-header">
        <p className="section-label">Quick add</p>
        <h2>Add a technology</h2>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Name
          <input name="name" placeholder="Distributed Systems" required />
        </label>
        <div className="split-fields">
          <label>
            Type
            <select name="type" defaultValue="technology" disabled>
              <option value="technology">technology</option>
            </select>
          </label>
          <label>
            Priority
            <select name="priority" defaultValue="medium">
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </label>
        </div>
        <label>
          Official website URL
          <input name="officialSiteUrl" type="url" placeholder="https://www.typescriptlang.org/" />
        </label>
        <label>
          Official updates/feed URL
          <input
            name="officialFeedUrl"
            type="url"
            placeholder="https://devblogs.microsoft.com/typescript/feed/"
          />
        </label>
        <div className="split-fields">
          <label>
            Watch keywords
            <input name="watchKeywords" placeholder="release, beta, compiler" />
          </label>
          <label>
            Ignore keywords
            <input name="ignoreKeywords" placeholder="webinar, case study" />
          </label>
        </div>
        <label>
          Notes
          <textarea name="notes" placeholder="What should count as useful signal?" />
        </label>
        <button className="button primary" type="submit">
          Save interest
        </button>
      </form>
    </aside>
  );
};
