import { useSyncExternalStore } from "react";

import { type PageView } from "./types";

const routeChangeEvent = "learning-engine-routechange";
const pathByView: Record<PageView, string> = {
  interests: "/interests",
  updates: "/updates",
};

/** Removes a trailing slash so route comparisons accept canonical equivalents. */
const normalizePathname = (pathname: string): string => {
  if (pathname === "/") {
    return pathname;
  }

  if (pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }

  return pathname;
};

/** Maps a URL pathname to the matching PageView, defaulting to updates. */
const viewFromPathname = (pathname: string): PageView => {
  const normalizedPathname = normalizePathname(pathname);

  if (normalizedPathname === pathByView.interests) {
    return "interests";
  }

  return "updates";
};

/** Reads window.location and returns the current page route snapshot. */
const routeSnapshot = (): PageView => viewFromPathname(window.location.pathname);

/** Dispatches the custom route-change event after history state changes. */
const emitRouteChange = (): void => {
  window.dispatchEvent(new Event(routeChangeEvent));
};

/** Subscribes onStoreChange to popstate and routeChangeEvent, returning cleanup. */
const subscribeToRoute = (onStoreChange: () => void): (() => void) => {
  window.addEventListener("popstate", onStoreChange);
  window.addEventListener(routeChangeEvent, onStoreChange);

  return () => {
    window.removeEventListener("popstate", onStoreChange);
    window.removeEventListener(routeChangeEvent, onStoreChange);
  };
};

/** Returns the default server snapshot before browser location is available. */
const serverRouteSnapshot = (): PageView => "updates";

/** Navigates to a page view and notifies route subscribers when it changes. */
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
