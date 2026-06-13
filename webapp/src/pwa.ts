import { registerSW } from "virtual:pwa-register";

type PwaUpdateSnapshot = {
  refreshUpdate: () => void;
  updateAvailable: boolean;
};

type PwaUpdateListener = () => void;

const pwaUpdateListeners = new Set<PwaUpdateListener>();

let updateServiceWorker: ((reloadPage?: boolean) => Promise<void>) | null = null;
let updateSnapshot: PwaUpdateSnapshot = {
  refreshUpdate: () => undefined,
  updateAvailable: false,
};
let isRegistered = false;

const emitPwaUpdate = (): void => {
  pwaUpdateListeners.forEach((listener) => listener());
};

const refreshUpdate = (): void => {
  if (updateServiceWorker === null) {
    return;
  }

  void updateServiceWorker(true);
};

const setUpdateAvailable = (updateAvailable: boolean): void => {
  updateSnapshot = { refreshUpdate, updateAvailable };
  emitPwaUpdate();
};

/** Registers the service worker and initializes update handling. */
export const registerPwa = (): void => {
  if (isRegistered) {
    return;
  }

  isRegistered = true;
  updateServiceWorker = registerSW({
    immediate: true,
    onNeedRefresh: () => setUpdateAvailable(true),
  });
};

/**
 * Subscribes to PWA update changes.
 * @param listener PwaUpdateListener called when update state changes.
 * @returns Unsubscribe function.
 */
export const subscribeToPwaUpdates = (listener: PwaUpdateListener): (() => void) => {
  pwaUpdateListeners.add(listener);

  return () => {
    pwaUpdateListeners.delete(listener);
  };
};

/** Returns the current PwaUpdateSnapshot. */
export const getPwaUpdateSnapshot = (): PwaUpdateSnapshot => updateSnapshot;
