import {
  interestsPayloadSchema,
  saveInterestsResponseSchema,
  updatesPayloadSchema,
} from "./schemas";
import { type Interest, type UpdatesPayload } from "./types";

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

export const fetchUpdates = async (): Promise<UpdatesPayload> => {
  const response = await fetch("/api/updates");
  const payload = updatesPayloadSchema.parse(await response.json());

  if (!response.ok) {
    throw new Error(payload.error ?? "Failed to fetch updates");
  }

  return payload;
};
