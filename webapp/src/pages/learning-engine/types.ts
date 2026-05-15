import { type Interest, type TechnologyUpdatesPayload } from "./schemas";

export type { Interest, TechnologyUpdatesPayload };

export type Priority = "high" | "medium" | "low";

export type ToastState = {
  message: string;
  visible: boolean;
};

export type InterestFormValues = {
  name: string;
  priority: Priority;
  officialSiteUrl: string;
  officialFeedUrl: string;
  watchKeywords: string[];
  ignoreKeywords: string[];
  notes: string;
};

export type LearningEnginePageActions = {
  addInterest: (form: HTMLFormElement) => void;
  checkTechnologyUpdates: () => void;
  removeInterest: (id: string) => void;
  saveInterests: () => void;
  toggleInterest: (id: string) => void;
};
