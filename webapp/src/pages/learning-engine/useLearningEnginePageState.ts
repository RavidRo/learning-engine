import { type QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";

import { fetchInterests, fetchUpdates, saveInterests } from "./api";
import { createInterest, updateInterestFromDraft } from "./interestForm";
import { navigateToView, usePageRoute } from "./usePageRoute";
import {
  type Interest,
  type LearningEnginePageActions,
  type PageView,
  type SaveStatus,
  type UpdatesPayload,
  type ToastState,
} from "./types";

const interestsQueryKey = ["learning-engine", "interests"] as const;
const defaultUpdateDays = 2;
const updatesQueryKey = (days: number) => ["learning-engine", "updates", days] as const;
const emptyToast: ToastState = { message: "Saved locally", visible: false };

type ToastAction = { type: "hideToast" } | { type: "showToast"; message: string };
type ShowToast = (message: string) => void;
type SaveInterestsContext = { previousInterests: Interest[] };

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

const useSaveInterestsMutation = (queryClient: QueryClient, showToast: ShowToast) =>
  useMutation<Interest[], Error, Interest[], SaveInterestsContext>({
    mutationFn: saveInterests,
    onError: (error, _nextInterests, context) => {
      queryClient.setQueryData(interestsQueryKey, context?.previousInterests ?? []);
      showToast(errorMessage(error, "Failed to save"));
    },
    onMutate: async (nextInterests: Interest[]) => {
      await queryClient.cancelQueries({ queryKey: interestsQueryKey });
      const previousInterests = queryClient.getQueryData<Interest[]>(interestsQueryKey);

      queryClient.setQueryData(interestsQueryKey, nextInterests);

      return { previousInterests: previousInterests ?? [] };
    },
    onSuccess: (savedInterests) => {
      queryClient.setQueryData(interestsQueryKey, savedInterests);
      showToast("Saved locally");
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

const createLearningEngineActions = (
  interests: Interest[],
  setView: (view: PageView) => void,
  saveNextInterests: (nextInterests: Interest[]) => void,
  checkUpdates: () => void,
): LearningEnginePageActions => ({
  addInterest: (draft) => {
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
    checkUpdates();
  },
  removeInterest: (id) => {
    const nextInterests = interests.map((interest) =>
      interest.id === id ? { ...interest, deletedAt: new Date().toISOString() } : interest,
    );

    saveNextInterests(nextInterests);
  },
  toggleInterest: (id) => {
    const nextInterests = interests.map((interest) =>
      interest.id === id ? { ...interest, enabled: !interest.enabled } : interest,
    );

    saveNextInterests(nextInterests);
  },
  updateInterest: (draft) => {
    const nextInterests = interests.map((interest) => {
      if (interest.id !== draft.id) {
        return interest;
      }

      return updateInterestFromDraft(interest, draft) ?? interest;
    });

    saveNextInterests(nextInterests);
  },
});

// fallow-ignore-next-line complexity
export const useLearningEnginePageState = () => {
  const queryClient = useQueryClient();
  const [toast, showToast] = useAutoDismissToast();
  const view = usePageRoute();
  const [updateDays, setUpdateDays] = useState(defaultUpdateDays);
  const currentUpdatesQueryKey = updatesQueryKey(updateDays);

  const interestsQuery = useQuery({
    queryFn: fetchInterests,
    queryKey: interestsQueryKey,
  });

  const updatesQuery = useQuery({
    enabled: view === "updates",
    queryFn: () => fetchUpdates(updateDays),
    queryKey: currentUpdatesQueryKey,
  });

  const saveInterestsMutation = useSaveInterestsMutation(queryClient, showToast);
  const interests = interestsQuery.data ?? [];
  const visibleInterests = interests.filter((interest) => interest.deletedAt == null);
  const actions = createLearningEngineActions(
    interests,
    navigateToView,
    saveInterestsMutation.mutate,
    () => {
      void updatesQuery.refetch().then((result) => {
        if (result.error !== null) {
          const updatesError: UpdatesPayload = {
            errors: [],
            error: errorMessage(result.error, "Failed to fetch updates"),
            sources_checked: 0,
            updates: [],
          };

          queryClient.setQueryData(currentUpdatesQueryKey, updatesError);
          return;
        }

        showToast("Updates refreshed");
      });
    },
  );

  return {
    actions,
    state: {
      enabledInterests: visibleInterests.filter((interest) => interest.enabled).length,
      sourcesTracked: visibleInterests.reduce(
        (count, interest) =>
          count + interest.sources.filter((source) => source.deletedAt == null).length,
        0,
      ),
      interests: visibleInterests,
      isChecking: updatesQuery.isFetching,
      isSaving: saveInterestsMutation.isPending,
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
