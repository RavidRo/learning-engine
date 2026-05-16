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
        <h2>Add an interest</h2>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Name
          <input name="name" placeholder="TypeScript" required />
        </label>
        <div className="split-fields">
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
          Description
          <textarea
            name="description"
            placeholder="What information about this topic belongs in briefings?"
            required
          />
        </label>
        <div className="split-fields">
          <label>
            Source label
            <input name="sourceLabel" placeholder="Official dev blog" required />
          </label>
          <label>
            Source type
            <select name="sourceType" defaultValue="feed">
              <option value="feed">feed</option>
              <option value="page">page</option>
              <option value="youtube_channel">YouTube channel</option>
              <option value="twitter_account">Twitter account</option>
              <option value="spotify_podcast">Spotify podcast</option>
            </select>
          </label>
        </div>
        <label>
          Source URL
          <input
            name="sourceUrl"
            placeholder="URL, @handle, channel ID, or Spotify show URI"
            required
          />
        </label>
        <button className="button primary" type="submit">
          Save interest
        </button>
      </form>
    </aside>
  );
};
