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

export const subscribeToPwaUpdates = (listener: PwaUpdateListener): (() => void) => {
  pwaUpdateListeners.add(listener);

  return () => {
    pwaUpdateListeners.delete(listener);
  };
};

export const getPwaUpdateSnapshot = (): PwaUpdateSnapshot => updateSnapshot;
