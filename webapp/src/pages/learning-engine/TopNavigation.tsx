import { type PageView } from "./types";

type TopNavigationProps = {
  onChangeView: (view: PageView) => void;
  view: PageView;
};

export const TopNavigation = ({ onChangeView, view }: TopNavigationProps) => (
  <nav className="topbar" aria-label="Main navigation">
    <a className="brand" href="#top" aria-label="Learning Engine home">
      <span className="brand-mark">LE</span>
      <span>Learning Engine</span>
    </a>
    <div className="navlinks" aria-label="Sections">
      <button
        className={view === "interests" ? "nav-button active" : "nav-button"}
        type="button"
        onClick={() => onChangeView("interests")}
      >
        Interests
      </button>
      <button
        className={view === "updates" ? "nav-button active" : "nav-button"}
        type="button"
        onClick={() => onChangeView("updates")}
      >
        Weekly updates
      </button>
      <a href="#briefing">Briefing</a>
    </div>
  </nav>
);
