import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useReducer } from "react";

import { fetchInterests, fetchTechnologyUpdates, saveInterests } from "./api";
import { readInterestForm, slugify } from "./interestForm";
import { type Interest, type LearningEnginePageActions, type ToastState } from "./types";

const interestsQueryKey = ["learning-engine", "interests"] as const;
const technologyUpdatesQueryKey = ["learning-engine", "technology-updates"] as const;
const emptyToast: ToastState = { message: "Saved locally", visible: false };

type ToastAction = { type: "hideToast" } | { type: "showToast"; message: string };

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

const createInterest = (form: HTMLFormElement): Interest | null => {
  const formValues = readInterestForm(form);

  if (!formValues.name) {
    return null;
  }

  return {
    deletedAt: null,
    enabled: true,
    id: `${slugify(formValues.name)}-${String(Date.now())}`,
    ignore_keywords: formValues.ignoreKeywords,
    name: formValues.name,
    notes: formValues.notes,
    official_feed_url: formValues.officialFeedUrl,
    official_site_url: formValues.officialSiteUrl,
    priority: formValues.priority,
    type: "technology",
    watch_keywords: formValues.watchKeywords,
  };
};

export const useLearningEnginePageState = () => {
  const queryClient = useQueryClient();
  const [toast, dispatchToast] = useReducer(toastReducer, emptyToast);

  const interestsQuery = useQuery({
    queryFn: fetchInterests,
    queryKey: interestsQueryKey,
  });

  const technologyUpdatesQuery = useQuery({
    enabled: false,
    queryFn: fetchTechnologyUpdates,
    queryKey: technologyUpdatesQueryKey,
  });

  const saveInterestsMutation = useMutation({
    mutationFn: saveInterests,
    onError: (error, _nextInterests, context: { previousInterests: Interest[] } | undefined) => {
      queryClient.setQueryData(interestsQueryKey, context?.previousInterests ?? []);
      dispatchToast({ type: "showToast", message: errorMessage(error, "Failed to save") });
    },
    onMutate: async (nextInterests: Interest[]) => {
      await queryClient.cancelQueries({ queryKey: interestsQueryKey });
      const previousInterests = queryClient.getQueryData<Interest[]>(interestsQueryKey);

      queryClient.setQueryData(interestsQueryKey, nextInterests);

      return { previousInterests: previousInterests ?? [] };
    },
    onSuccess: (savedInterests) => {
      queryClient.setQueryData(interestsQueryKey, savedInterests);
      dispatchToast({ type: "showToast", message: "Saved locally" });
    },
  });

  const interests = interestsQuery.data ?? [];
  const updates = technologyUpdatesQuery.data ?? null;
  const visibleInterests = interests.filter((interest) => interest.deletedAt == null);
  const enabledInterests = visibleInterests.filter((interest) => interest.enabled).length;
  const feedsWithUpdates = visibleInterests.filter((interest) => interest.official_feed_url).length;
  const loadError =
    interestsQuery.error === null
      ? null
      : errorMessage(interestsQuery.error, "Failed to load interests");

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

  const saveNextInterests = (nextInterests: Interest[]): void => {
    saveInterestsMutation.mutate(nextInterests);
  };

  const actions: LearningEnginePageActions = {
    addInterest: (form) => {
      const newInterest = createInterest(form);

      if (newInterest === null) {
        return;
      }

      saveNextInterests([newInterest, ...interests]);
      form.reset();
    },
    checkTechnologyUpdates: () => {
      void technologyUpdatesQuery.refetch().then((result) => {
        if (result.error !== null) {
          const updatesError = {
            errors: [errorMessage(result.error, "Failed to fetch updates")],
            interests_checked: 0,
            updates: [],
          };

          queryClient.setQueryData(technologyUpdatesQueryKey, updatesError);
          return;
        }

        dispatchToast({ type: "showToast", message: "Technology updates checked" });
      });
    },
    removeInterest: (id) => {
      const nextInterests = interests.map((interest) =>
        interest.id === id ? { ...interest, deletedAt: new Date().toISOString() } : interest,
      );

      saveNextInterests(nextInterests);
    },
    saveInterests: () => {
      saveNextInterests(interests);
    },
    toggleInterest: (id) => {
      const nextInterests = interests.map((interest) =>
        interest.id === id ? { ...interest, enabled: !interest.enabled } : interest,
      );

      saveNextInterests(nextInterests);
    },
  };

  return {
    actions,
    state: {
      enabledInterests,
      feedsWithUpdates,
      interests: visibleInterests,
      isChecking: technologyUpdatesQuery.isFetching,
      isSaving: saveInterestsMutation.isPending,
      loadError,
      toast,
      updates,
    },
  };
};
