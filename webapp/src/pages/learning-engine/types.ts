import {
  type Collection,
  type Interest,
  type BatchSourceImagePayload,
  type SavedCollectionUpdate,
  type SourceImagePayload,
  type Update,
  type UpdatesPayload,
} from "./schemas";

export type {
  BatchSourceImagePayload,
  Collection,
  Interest,
  SavedCollectionUpdate,
  SourceImagePayload,
  Update,
  UpdatesPayload,
};
export type InterestSource = Interest["sources"][number];

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

export type PageView = "collections" | "interests" | "updates";

export type SaveStatus = "idle" | "saving" | "saved" | "failed";

export type InterestDraft = {
  description: string;
  enabled: boolean;
  id: string | null;
  name: string;
  priority: Priority;
  sources: InterestSource[];
};

export type InterestFormValues = {
  name: string;
  priority: Priority;
  description: string;
  sources: InterestSource[];
};

export type LearningEnginePageActions = {
  addInterest: (draft: InterestDraft) => void;
  changeView: (view: PageView) => void;
  checkUpdates: () => void;
  exportInterests: () => void;
  importInterests: (file: File) => void;
  removeInterest: (id: string) => void;
  removeSavedUpdate: (collectionId: string, updateKey: string) => void;
  saveUpdateToCollection: (collectionId: string, update: Update) => void;
  toggleInterest: (id: string) => void;
  updateInterest: (draft: InterestDraft) => void;
};
