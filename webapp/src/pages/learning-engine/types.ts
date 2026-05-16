import { type Interest, type UpdatesPayload } from "./schemas";

export type { Interest, UpdatesPayload };

export type Priority = "high" | "medium" | "low";
export type SourceType =
  | "feed"
  | "page"
  | "youtube_channel"
  | "twitter_account"
  | "spotify_podcast";

export type ToastState = {
  message: string;
  visible: boolean;
};

export type InterestFormValues = {
  name: string;
  priority: Priority;
  description: string;
  sourceLabel: string;
  sourceType: SourceType;
  sourceUrl: string;
};

export type LearningEnginePageActions = {
  addInterest: (form: HTMLFormElement) => void;
  checkUpdates: () => void;
  removeInterest: (id: string) => void;
  saveInterests: () => void;
  toggleInterest: (id: string) => void;
};
