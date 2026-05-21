import { useSyncExternalStore } from "react";

import { type PageView } from "./types";

const routeChangeEvent = "learning-engine-routechange";
const pathByView: Record<PageView, string> = {
  interests: "/interests",
  updates: "/updates",
};

const viewFromPathname = (pathname: string): PageView => {
  if (pathname === pathByView.interests) {
    return "interests";
  }

  return "updates";
};

const routeSnapshot = (): PageView => viewFromPathname(window.location.pathname);

const emitRouteChange = (): void => {
  window.dispatchEvent(new Event(routeChangeEvent));
};

const subscribeToRoute = (onStoreChange: () => void): (() => void) => {
  window.addEventListener("popstate", onStoreChange);
  window.addEventListener(routeChangeEvent, onStoreChange);

  return () => {
    window.removeEventListener("popstate", onStoreChange);
    window.removeEventListener(routeChangeEvent, onStoreChange);
  };
};

const serverRouteSnapshot = (): PageView => "updates";

export const navigateToView = (view: PageView): void => {
  const nextPath = pathByView[view];

  if (window.location.pathname === nextPath) {
    return;
  }

  window.history.pushState(null, "", nextPath);
  emitRouteChange();
};

export const usePageRoute = (): PageView =>
  useSyncExternalStore(subscribeToRoute, routeSnapshot, serverRouteSnapshot);
