import {
  interestsPayloadSchema,
  saveInterestsResponseSchema,
  sourceImageResponseSchema,
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

export const fetchUpdates = async (days: number): Promise<UpdatesPayload> => {
  const response = await fetch(`/api/updates?days=${days}`);
  const payload = updatesPayloadSchema.parse(await response.json());

  if (!response.ok) {
    throw new Error(payload.error ?? "Failed to fetch updates");
  }

  return payload;
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
