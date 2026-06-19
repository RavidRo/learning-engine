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

/** Reads the best available error message from a failed response. */
const readError = async (response: Response): Promise<string> => {
  const message = await response.text();
  return message || response.statusText;
};

export const fetchInterests = async (): Promise<Interest[]> => {
  const response = await fetch("/api/interests");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = interestsPayloadSchema.parse(await response.json());
  return payload.interests;
};

export const saveInterests = async (interests: Interest[]): Promise<Interest[]> => {
  const response = await fetch("/api/interests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interests }, null, 2),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = saveInterestsResponseSchema.parse(await response.json());
  return payload.saved.interests;
};

export const downloadInterestExport = async (): Promise<Blob> => {
  const response = await fetch("/api/interests/export");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return await response.blob();
};

export const uploadInterestExport = async (file: File): Promise<Interest[]> => {
  const response = await fetch("/api/interests/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await file.text(),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = saveInterestsResponseSchema.parse(await response.json());
  return payload.saved.interests;
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

export const fetchUpdates = async (days: number): Promise<UpdatesPayload> => {
  const response = await fetch(`/api/updates?days=${days}`);
  const responsePayload = await response.json();

  if (!response.ok) {
    throw new Error(updatesRequestErrorMessage(responsePayload, response.statusText));
  }

  return parseUpdatesPayload(responsePayload);
};

export const fetchCollections = async (): Promise<Collection[]> => {
  const response = await fetch("/api/collections");

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = collectionsPayloadSchema.parse(await response.json());
  return payload.collections;
};

export const saveUpdateToCollection = async (
  collectionId: string,
  update: Update,
): Promise<SavedCollectionUpdate> => {
  const response = await fetch(`/api/collections/${collectionId}/updates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ update }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return saveCollectionUpdateResponseSchema.parse(await response.json()).saved_update;
};

export const removeSavedUpdate = async (collectionId: string, updateKey: string): Promise<void> => {
  const response = await fetch(`/api/collections/${collectionId}/updates/${updateKey}`, {
    method: "DELETE",
  });

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
