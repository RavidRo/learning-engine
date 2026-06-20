import { useAuth } from "@clerk/react";
import { type QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useReducer, useState } from "react";

import { type LearningEngineApi, createLearningEngineApi } from "./api";
import { createInterest, updateInterestFromDraft } from "./interestForm";
import { navigateToView, usePageRoute } from "./usePageRoute";
import {
  type Interest,
  type SignalGardenPageActions,
  type PageView,
  type SaveStatus,
  type Update,
  type UpdatesPayload,
  type ToastState,
} from "./types";

const defaultUpdateDays = 2;
const historyCollectionId = "history";
const interestsQueryKey = (authScope: string) => ["signal-garden", authScope, "interests"] as const;
const collectionsQueryKey = (authScope: string) =>
  ["signal-garden", authScope, "collections"] as const;
const updatesQueryKey = (authScope: string, days: number) =>
  ["signal-garden", authScope, "updates", days] as const;
const emptyToast: ToastState = { message: "Saved locally", visible: false };

type ToastAction = { type: "hideToast" } | { type: "showToast"; message: string };
type ShowToast = (message: string) => void;
type SaveInterestsContext = { previousInterests: Interest[] };
type SaveUpdateToCollectionInput = { collectionId: string; update: Update };
type RemoveSavedUpdateInput = { collectionId: string; updateKey: string };

const toastReducer = (state: ToastState, action: ToastAction): ToastState => {
  switch (action.type) {
    case "hideToast":
      return { ...state, visible: false };
    case "showToast":
      return { message: action.message, visible: true };
  }
};

const errorMessage = (error: unknown, fallback: string): string =>
  error instanceof Error ? error.message : fallback;

const useAutoDismissToast = (): [ToastState, ShowToast] => {
  const [toast, dispatchToast] = useReducer(toastReducer, emptyToast);

  useEffect(() => {
    if (!toast.visible) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      dispatchToast({ type: "hideToast" });
    }, 1400);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [toast.visible]);

  const showToast = (message: string): void => {
    dispatchToast({ type: "showToast", message });
  };

  return [toast, showToast];
};

const useSaveInterestsMutation = (
  api: LearningEngineApi,
  queryClient: QueryClient,
  showToast: ShowToast,
  authScope: string,
) =>
  useMutation<Interest[], Error, Interest[], SaveInterestsContext>({
    mutationFn: api.saveInterests,
    onError: (error, _nextInterests, context) => {
      queryClient.setQueryData(interestsQueryKey(authScope), context?.previousInterests ?? []);
      showToast(errorMessage(error, "Failed to save"));
    },
    onMutate: async (nextInterests: Interest[]) => {
      await queryClient.cancelQueries({ queryKey: interestsQueryKey(authScope) });
      const previousInterests = queryClient.getQueryData<Interest[]>(interestsQueryKey(authScope));

      queryClient.setQueryData(interestsQueryKey(authScope), nextInterests);

      return { previousInterests: previousInterests ?? [] };
    },
    onSuccess: (savedInterests) => {
      queryClient.setQueryData(interestsQueryKey(authScope), savedInterests);
      showToast("Saved locally");
    },
  });

const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

const interestExportFilename = (): string =>
  `signal-garden-interests-${new Date().toISOString().slice(0, 10)}.json`;

const useExportInterestsMutation = (api: LearningEngineApi, showToast: ShowToast) =>
  useMutation<Blob, Error>({
    mutationFn: api.downloadInterestExport,
    onError: (error) => {
      showToast(errorMessage(error, "Failed to export interests"));
    },
    onSuccess: (blob) => {
      downloadBlob(blob, interestExportFilename());
      showToast("Export downloaded");
    },
  });

const useImportInterestsMutation = (
  api: LearningEngineApi,
  queryClient: QueryClient,
  showToast: ShowToast,
  authScope: string,
) =>
  useMutation<Interest[], Error, File>({
    mutationFn: api.uploadInterestExport,
    onError: (error) => {
      showToast(errorMessage(error, "Failed to import interests"));
    },
    onSuccess: (savedInterests) => {
      queryClient.setQueryData(interestsQueryKey(authScope), savedInterests);
      showToast("Interests imported");
    },
  });

const useSaveUpdateToCollectionMutation = (
  api: LearningEngineApi,
  queryClient: QueryClient,
  showToast: ShowToast,
  authScope: string,
) =>
  useMutation({
    mutationFn: ({ collectionId, update }: SaveUpdateToCollectionInput) =>
      api.saveUpdateToCollection(collectionId, update),
    onError: (error) => {
      showToast(errorMessage(error, "Failed to save update"));
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collectionsQueryKey(authScope) });
      showToast("Update saved");
    },
  });

const useRemoveSavedUpdateMutation = (
  api: LearningEngineApi,
  queryClient: QueryClient,
  showToast: ShowToast,
  authScope: string,
) =>
  useMutation({
    mutationFn: ({ collectionId, updateKey }: RemoveSavedUpdateInput) =>
      api.removeSavedUpdate(collectionId, updateKey),
    onError: (error) => {
      showToast(errorMessage(error, "Failed to remove update"));
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collectionsQueryKey(authScope) });
      showToast("Update removed");
    },
  });

const mutationSaveStatus: Record<"idle" | "pending" | "error" | "success", SaveStatus> = {
  error: "failed",
  idle: "idle",
  pending: "saving",
  success: "saved",
};

const saveStatus = (status: "idle" | "pending" | "error" | "success"): SaveStatus =>
  mutationSaveStatus[status];

const updatesErrorPayload = (error: unknown): UpdatesPayload => ({
  errors: [],
  error: errorMessage(error, "Failed to fetch updates"),
  sources_checked: 0,
  updates: [],
});

const createSignalGardenActions = (
  interests: Interest[],
  isOffline: boolean,
  setView: (view: PageView) => void,
  showToast: ShowToast,
  saveNextInterests: (nextInterests: Interest[]) => void,
  checkUpdates: () => void,
  exportInterests: () => void,
  importInterests: (file: File) => void,
  saveUpdateToCollection: (collectionId: string, update: Update) => void,
  removeSavedUpdate: (collectionId: string, updateKey: string) => void,
): SignalGardenPageActions => ({
  addInterest: (draft) => {
    if (isOffline) {
      showToast("Connect to save interests");
      return;
    }

    const newInterest = createInterest(draft);

    if (newInterest === null) {
      return;
    }

    saveNextInterests([newInterest, ...interests]);
  },
  changeView: (view) => {
    setView(view);
  },
  checkUpdates: () => {
    if (isOffline) {
      showToast("Connect to refresh updates");
      return;
    }

    checkUpdates();
  },
  exportInterests: () => {
    if (isOffline) {
      showToast("Connect to export interests");
      return;
    }

    exportInterests();
  },
  importInterests: (file) => {
    if (isOffline) {
      showToast("Connect to import interests");
      return;
    }

    importInterests(file);
  },
  removeInterest: (id) => {
    if (isOffline) {
      showToast("Connect to save interests");
      return;
    }

    const nextInterests = interests.map((interest) =>
      interest.id === id ? { ...interest, deletedAt: new Date().toISOString() } : interest,
    );

    saveNextInterests(nextInterests);
  },
  removeSavedUpdate: (collectionId, updateKey) => {
    if (isOffline) {
      showToast("Connect to update collections");
      return;
    }

    removeSavedUpdate(collectionId, updateKey);
  },
  saveUpdateToCollection: (collectionId, update) => {
    if (isOffline) {
      showToast("Connect to update collections");
      return;
    }

    saveUpdateToCollection(collectionId, update);
  },
  trackUpdateCheckout: (update) => {
    if (isOffline) {
      return;
    }

    saveUpdateToCollection(historyCollectionId, update);
  },
  toggleInterest: (id) => {
    if (isOffline) {
      showToast("Connect to save interests");
      return;
    }

    const nextInterests = interests.map((interest) =>
      interest.id === id ? { ...interest, enabled: !interest.enabled } : interest,
    );

    saveNextInterests(nextInterests);
  },
  updateInterest: (draft) => {
    if (isOffline) {
      showToast("Connect to save interests");
      return;
    }

    const nextInterests = interests.map((interest) => {
      if (interest.id !== draft.id) {
        return interest;
      }

      return updateInterestFromDraft(interest, draft) ?? interest;
    });

    saveNextInterests(nextInterests);
  },
});

type UseSignalGardenPageStateOptions = {
  isBrowserOffline: boolean;
};

// fallow-ignore-next-line complexity
export const useSignalGardenPageState = ({ isBrowserOffline }: UseSignalGardenPageStateOptions) => {
  const queryClient = useQueryClient();
  const { getToken, isLoaded, isSignedIn, sessionId, userId } = useAuth();
  const isAuthenticated = isLoaded && isSignedIn === true;
  const authScope = isAuthenticated
    ? `${userId ?? "unknown"}:${sessionId ?? "no-session"}`
    : "signed-out";
  const api = useMemo(() => createLearningEngineApi(getToken), [getToken]);
  const [toast, showToast] = useAutoDismissToast();
  const view = usePageRoute();
  const [updateDays, setUpdateDays] = useState(defaultUpdateDays);
  const currentInterestsQueryKey = interestsQueryKey(authScope);
  const currentCollectionsQueryKey = collectionsQueryKey(authScope);
  const currentUpdatesQueryKey = updatesQueryKey(authScope, updateDays);

  const interestsQuery = useQuery({
    enabled: isAuthenticated,
    queryFn: api.fetchInterests,
    queryKey: currentInterestsQueryKey,
  });

  const updatesQuery = useQuery({
    enabled: isAuthenticated && view === "updates",
    queryFn: () => api.fetchUpdates(updateDays),
    queryKey: currentUpdatesQueryKey,
  });

  const collectionsQuery = useQuery({
    enabled: isAuthenticated && (view === "collections" || view === "updates"),
    queryFn: api.fetchCollections,
    queryKey: currentCollectionsQueryKey,
  });

  const saveInterestsMutation = useSaveInterestsMutation(api, queryClient, showToast, authScope);
  const exportInterestsMutation = useExportInterestsMutation(api, showToast);
  const importInterestsMutation = useImportInterestsMutation(
    api,
    queryClient,
    showToast,
    authScope,
  );
  const saveUpdateToCollectionMutation = useSaveUpdateToCollectionMutation(
    api,
    queryClient,
    showToast,
    authScope,
  );
  const removeSavedUpdateMutation = useRemoveSavedUpdateMutation(
    api,
    queryClient,
    showToast,
    authScope,
  );
  const isConnectionUnavailable =
    !isAuthenticated || isBrowserOffline || interestsQuery.isError || updatesQuery.isError;
  const interests = interestsQuery.data ?? [];
  const visibleInterests = interests.filter((interest) => interest.deletedAt == null);
  const actions = createSignalGardenActions(
    interests,
    isConnectionUnavailable,
    navigateToView,
    showToast,
    saveInterestsMutation.mutate,
    async () => {
      try {
        const result = await updatesQuery.refetch();

        if (result.error !== null) {
          queryClient.setQueryData(currentUpdatesQueryKey, updatesErrorPayload(result.error));
          return;
        }

        showToast("Updates refreshed");
      } catch (error) {
        queryClient.setQueryData(currentUpdatesQueryKey, updatesErrorPayload(error));
      }
    },
    exportInterestsMutation.mutate,
    importInterestsMutation.mutate,
    (collectionId, update) => saveUpdateToCollectionMutation.mutate({ collectionId, update }),
    (collectionId, updateKey) => removeSavedUpdateMutation.mutate({ collectionId, updateKey }),
  );

  return {
    actions,
    state: {
      enabledInterests: visibleInterests.filter((interest) => interest.enabled).length,
      isAuthLoaded: isLoaded,
      isAuthenticated,
      sourcesTracked: visibleInterests.reduce(
        (count, interest) =>
          count + interest.sources.filter((source) => source.deletedAt == null).length,
        0,
      ),
      interests: visibleInterests,
      collections: collectionsQuery.data ?? [],
      collectionsError:
        collectionsQuery.error === null
          ? null
          : errorMessage(collectionsQuery.error, "Failed to load collections"),
      isChecking: updatesQuery.isFetching,
      isConnectionUnavailable,
      isExporting: exportInterestsMutation.isPending,
      isImporting: importInterestsMutation.isPending,
      isLoadingCollections: collectionsQuery.isLoading,
      isSaving: saveInterestsMutation.isPending,
      isRemovingSavedUpdate: removeSavedUpdateMutation.isPending,
      isSavingToCollection: saveUpdateToCollectionMutation.isPending,
      saveError:
        saveInterestsMutation.error === null
          ? null
          : errorMessage(saveInterestsMutation.error, "Failed to save"),
      saveStatus: saveStatus(saveInterestsMutation.status),
      loadError:
        interestsQuery.error === null
          ? null
          : errorMessage(interestsQuery.error, "Failed to load interests"),
      toast,
      updateDays,
      setUpdateDays,
      updatesError:
        updatesQuery.error === null
          ? null
          : errorMessage(updatesQuery.error, "Failed to fetch updates"),
      updates: updatesQuery.data ?? null,
      view,
    },
  };
};
