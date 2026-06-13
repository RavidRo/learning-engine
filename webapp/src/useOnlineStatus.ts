import { useSyncExternalStore } from "react";

type OnlineStatusListener = () => void;

const subscribeToOnlineStatus = (listener: OnlineStatusListener): (() => void) => {
  window.addEventListener("online", listener);
  window.addEventListener("offline", listener);

  return () => {
    window.removeEventListener("online", listener);
    window.removeEventListener("offline", listener);
  };
};

const getOnlineStatusSnapshot = (): boolean => navigator.onLine;

const getServerOnlineStatusSnapshot = (): boolean => true;

export const useIsOffline = (): boolean =>
  !useSyncExternalStore(
    subscribeToOnlineStatus,
    getOnlineStatusSnapshot,
    getServerOnlineStatusSnapshot,
  );
