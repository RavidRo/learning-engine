import { type PageView } from "./types";

type TopNavigationProps = {
  onChangeView: (view: PageView) => void;
  view: PageView;
};

export const TopNavigation = ({ onChangeView, view }: TopNavigationProps) => (
  <nav className="topbar" aria-label="Main navigation">
    <a className="brand" href="/updates" aria-label="Learning Engine updates">
      <img
        className="brand-mark"
        src="/favicon.svg"
        width="30"
        height="30"
        alt=""
        aria-hidden="true"
      />
      <span>Learning Engine</span>
    </a>
    <div className="navlinks" aria-label="Sections">
      <button
        className={view === "updates" ? "nav-button active" : "nav-button"}
        type="button"
        onClick={() => onChangeView("updates")}
      >
        Updates
      </button>
      <button
        className={view === "interests" ? "nav-button active" : "nav-button"}
        type="button"
        onClick={() => onChangeView("interests")}
      >
        Manage interests
      </button>
      <a href="#briefing">Briefing</a>
    </div>
  </nav>
);
