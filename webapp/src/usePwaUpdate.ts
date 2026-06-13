import { useSyncExternalStore } from "react";

import { getPwaUpdateSnapshot, subscribeToPwaUpdates } from "./pwa";

export const usePwaUpdate = () =>
  useSyncExternalStore(subscribeToPwaUpdates, getPwaUpdateSnapshot, getPwaUpdateSnapshot);
