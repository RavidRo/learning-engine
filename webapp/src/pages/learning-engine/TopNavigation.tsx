import { type PageView } from "./types";

type TopNavigationProps = {
  onChangeView: (view: PageView) => void;
  view: PageView;
};

export const TopNavigation = ({ onChangeView, view }: TopNavigationProps) => (
  <nav className="topbar" aria-label="Main navigation">
    <a className="brand" href="/updates" aria-label="Signal Garden updates">
      <img
        className="brand-mark"
        src="/pwa-192x192.png"
        width="30"
        height="30"
        alt=""
        aria-hidden="true"
      />
      <span>Signal Garden</span>
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
        className={view === "collections" ? "nav-button active" : "nav-button"}
        type="button"
        onClick={() => onChangeView("collections")}
      >
        Collections
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
