import { z } from "zod";

const prioritySchema = z.enum(["high", "medium", "low"]).catch("medium");
const sourceTypeSchema = z.enum([
  "feed",
  "page",
  "youtube_channel",
  "twitter_account",
  "spotify_podcast",
]);

const sourceSchema = z.object({
  deletedAt: z.string().nullable().optional(),
  enabled: z.boolean().catch(true),
  id: z
    .string()
    .nullish()
    .transform((id) => id ?? crypto.randomUUID()),
  imageUrl: z.string().nullable().optional().catch(null),
  ignoreKeywords: z.array(z.string()).catch([]),
  label: z.string().catch("Source"),
  type: sourceTypeSchema,
  url: z.string(),
});

const interestSchema = z.object({
  deletedAt: z.string().nullable().optional(),
  description: z.string().catch(""),
  enabled: z.boolean().catch(true),
  id: z
    .string()
    .nullish()
    .transform((id) => id ?? crypto.randomUUID()),
  name: z.string().catch("Interest"),
  priority: prioritySchema,
  sources: z.array(sourceSchema).catch([]),
});

export const interestsPayloadSchema = z.object({
  interests: z.array(interestSchema).catch([]),
});

const sourceInterestSchema = z.object({
  interest_name: z.string().catch("Interest"),
  source_image_url: z.string().nullable().optional().catch(null),
  source_label: z.string().catch("Source"),
  source_type: sourceTypeSchema.catch("feed"),
  source_url: z.string(),
});

const updateSchema = z.object({
  published: z.string().optional(),
  source_interest: sourceInterestSchema,
  title: z.string().optional(),
  url: z.string(),
});

const collectionErrorSchema = z.object({
  error: z.string(),
  interest_name: z.string().catch("Interest"),
  source_label: z.string().catch("Source"),
  source_url: z.string(),
});

export const updatesPayloadSchema = z.object({
  error: z.string().optional(),
  errors: z.array(collectionErrorSchema).catch([]),
  sources_checked: z.number().catch(0),
  updates: z.array(updateSchema).catch([]),
});

export const saveInterestsResponseSchema = z.object({
  saved: interestsPayloadSchema,
});

export const sourceImageResponseSchema = z.object({
  imageUrl: z.string().nullable().catch(null),
});

export type Interest = z.infer<typeof interestSchema>;

export type Update = z.infer<typeof updateSchema>;

export type UpdatesPayload = z.infer<typeof updatesPayloadSchema>;

export type SourceImagePayload = z.infer<typeof sourceImageResponseSchema>;
