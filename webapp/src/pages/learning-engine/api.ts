import {
  interestsPayloadSchema,
  saveInterestsResponseSchema,
  sourceImageResponseSchema,
  updatesDisplayErrorMessage,
  updatesPayloadSchema,
} from "./schemas";
import {
  type Interest,
  type InterestSource,
  type SourceImagePayload,
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
