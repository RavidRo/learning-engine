import {
  type QueryClient,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useEffect, useReducer } from "react";

import { fetchInterests, fetchUpdates, saveInterests } from "./api";
import { readInterestForm, slugify } from "./interestForm";
import {
  type Interest,
  type LearningEnginePageActions,
  type UpdatesPayload,
  type ToastState,
} from "./types";

const interestsQueryKey = ["learning-engine", "interests"] as const;
const updatesQueryKey = ["learning-engine", "updates"] as const;
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

const sourceLabel = (label: string): string => label || "Source";

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

const createInterest = (form: HTMLFormElement): Interest | null => {
  const formValues = readInterestForm(form);

  if (!formValues.name) {
    return null;
  }

  const now = String(Date.now());

  return {
    deletedAt: null,
    description: formValues.description,
    enabled: true,
    id: `${slugify(formValues.name)}-${now}`,
    name: formValues.name,
    priority: formValues.priority,
    sources: [
      {
        deletedAt: null,
        enabled: true,
        id: `${slugify(sourceLabel(formValues.sourceLabel))}-${now}`,
        label: sourceLabel(formValues.sourceLabel),
        type: formValues.sourceType,
        url: formValues.sourceUrl,
      },
    ],
  };
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

const createCheckUpdatesAction =
  (
    queryClient: QueryClient,
    updatesQuery: UseQueryResult<UpdatesPayload, Error>,
    showToast: ShowToast,
  ): (() => void) =>
  () => {
    void updatesQuery.refetch().then((result) => {
      if (result.error !== null) {
        const updatesError = {
          errors: [],
          error: errorMessage(result.error, "Failed to fetch updates"),
          sources_checked: 0,
          updates: [],
        };

        queryClient.setQueryData(updatesQueryKey, updatesError);
        return;
      }

      showToast("Updates checked");
    });
  };

const createLearningEngineActions = (
  interests: Interest[],
  saveNextInterests: (nextInterests: Interest[]) => void,
  checkUpdates: () => void,
): LearningEnginePageActions => ({
  addInterest: (form) => {
    const newInterest = createInterest(form);

    if (newInterest === null) {
      return;
    }

    saveNextInterests([newInterest, ...interests]);
    form.reset();
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
  saveInterests: () => {
    saveNextInterests(interests);
  },
  toggleInterest: (id) => {
    const nextInterests = interests.map((interest) =>
      interest.id === id ? { ...interest, enabled: !interest.enabled } : interest,
    );

    saveNextInterests(nextInterests);
  },
});

export const useLearningEnginePageState = () => {
  const queryClient = useQueryClient();
  const [toast, showToast] = useAutoDismissToast();

  const interestsQuery = useQuery({
    queryFn: fetchInterests,
    queryKey: interestsQueryKey,
  });

  const updatesQuery = useQuery({
    enabled: false,
    queryFn: fetchUpdates,
    queryKey: updatesQueryKey,
  });

  const saveInterestsMutation = useSaveInterestsMutation(queryClient, showToast);
  const interests = interestsQuery.data ?? [];
  const visibleInterests = interests.filter((interest) => interest.deletedAt == null);
  const checkUpdates = createCheckUpdatesAction(queryClient, updatesQuery, showToast);
  const actions = createLearningEngineActions(
    interests,
    saveInterestsMutation.mutate,
    checkUpdates,
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
      loadError:
        interestsQuery.error === null
          ? null
          : errorMessage(interestsQuery.error, "Failed to load interests"),
      toast,
      updates: updatesQuery.data ?? null,
    },
  };
};
