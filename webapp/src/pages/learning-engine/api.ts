import {
  collectionsPayloadSchema,
  batchSourceImageResponseSchema,
  interestsPayloadSchema,
  removeCollectionUpdateResponseSchema,
  saveCollectionUpdateResponseSchema,
  saveInterestsResponseSchema,
  sourceImageResponseSchema,
  updatesDisplayErrorMessage,
  updatesPayloadSchema,
} from "./schemas";
import {
  type Interest,
  type InterestSource,
  type BatchSourceImagePayload,
  type Collection,
  type SavedCollectionUpdate,
  type SourceImagePayload,
  type Update,
  type UpdatesPayload,
} from "./types";

export type SessionTokenProvider = () => Promise<string | null>;

/** Reads the best available error message from a failed response. */
const readError = async (response: Response): Promise<string> => {
  const message = await response.text();
  return message || response.statusText;
};

const authorizationHeader = async (getToken: SessionTokenProvider): Promise<string> => {
  const token = await getToken();
  if (token === null) {
    throw new Error("Sign in again to continue.");
  }
  return `Bearer ${token}`;
};

const authenticatedFetch = async (
  getToken: SessionTokenProvider,
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> => {
  const headers = new Headers(init.headers);
  headers.set("Authorization", await authorizationHeader(getToken));
  return await fetch(input, { ...init, headers });
};

export type LearningEngineApi = ReturnType<typeof createLearningEngineApi>;

export const createLearningEngineApi = (getToken: SessionTokenProvider) => ({
  downloadInterestExport: () => downloadInterestExport(getToken),
  fetchCollections: () => fetchCollections(getToken),
  fetchInterests: () => fetchInterests(getToken),
  fetchUpdates: (days: number) => fetchUpdates(getToken, days),
  removeSavedUpdate: (collectionId: string, updateKey: string) =>
    removeSavedUpdate(getToken, collectionId, updateKey),
  saveInterests: (interests: Interest[]) => saveInterests(getToken, interests),
  saveUpdateToCollection: (collectionId: string, update: Update) =>
    saveUpdateToCollection(getToken, collectionId, update),
  uploadInterestExport: (file: File) => uploadInterestExport(getToken, file),
});

const fetchInterests = async (getToken: SessionTokenProvider): Promise<Interest[]> => {
  const response = await authenticatedFetch(getToken, "/api/interests");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = interestsPayloadSchema.parse(await response.json());
  return payload.interests;
};

const savedInterestsFromResponse = async (response: Response): Promise<Interest[]> => {
  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = saveInterestsResponseSchema.parse(await response.json());
  return payload.saved.interests;
};

const saveInterests = async (
  getToken: SessionTokenProvider,
  interests: Interest[],
): Promise<Interest[]> => {
  const response = await authenticatedFetch(getToken, "/api/interests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interests }, null, 2),
  });

  return await savedInterestsFromResponse(response);
};

const downloadInterestExport = async (getToken: SessionTokenProvider): Promise<Blob> => {
  const response = await authenticatedFetch(getToken, "/api/interests/export");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return await response.blob();
};

const uploadInterestExport = async (
  getToken: SessionTokenProvider,
  file: File,
): Promise<Interest[]> => {
  const response = await authenticatedFetch(getToken, "/api/interests/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await file.text(),
  });

  return await savedInterestsFromResponse(response);
};

const parseUpdatesPayload = (responsePayload: unknown): UpdatesPayload => {
  const payload = updatesPayloadSchema.safeParse(responsePayload);

  if (!payload.success) {
    throw new Error(updatesDisplayErrorMessage);
  }

  return payload.data;
};

const updatesRequestErrorMessage = (responsePayload: unknown, fallback: string): string => {
  const payload = updatesPayloadSchema.safeParse(responsePayload);
  return payload.success ? (payload.data.error ?? "Failed to fetch updates") : fallback;
};

const fetchUpdates = async (
  getToken: SessionTokenProvider,
  days: number,
): Promise<UpdatesPayload> => {
  const response = await authenticatedFetch(getToken, `/api/updates?days=${days}`);
  const responsePayload = await response.json();

  if (!response.ok) {
    throw new Error(updatesRequestErrorMessage(responsePayload, response.statusText));
  }

  return parseUpdatesPayload(responsePayload);
};

const fetchCollections = async (getToken: SessionTokenProvider): Promise<Collection[]> => {
  const response = await authenticatedFetch(getToken, "/api/collections");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = collectionsPayloadSchema.parse(await response.json());
  return payload.collections;
};

const saveUpdateToCollection = async (
  getToken: SessionTokenProvider,
  collectionId: string,
  update: Update,
): Promise<SavedCollectionUpdate> => {
  const response = await authenticatedFetch(getToken, `/api/collections/${collectionId}/updates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ update }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return saveCollectionUpdateResponseSchema.parse(await response.json()).saved_update;
};

const removeSavedUpdate = async (
  getToken: SessionTokenProvider,
  collectionId: string,
  updateKey: string,
): Promise<void> => {
  const response = await authenticatedFetch(
    getToken,
    `/api/collections/${collectionId}/updates/${updateKey}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  removeCollectionUpdateResponseSchema.parse(await response.json());
};

export const resolveSourceImage = async (
  source: Pick<InterestSource, "type" | "url">,
): Promise<SourceImagePayload> => {
  const response = await fetch("/api/source-image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(source),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return sourceImageResponseSchema.parse(await response.json());
};

export const resolveSourceImages = async (
  sources: Pick<InterestSource, "id" | "type" | "url">[],
): Promise<BatchSourceImagePayload> => {
  const response = await fetch("/api/source-images", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sources),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return batchSourceImageResponseSchema.parse(await response.json());
};
