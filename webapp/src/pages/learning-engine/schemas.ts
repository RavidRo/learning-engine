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
  interest_id: z.string().nullable().optional().catch(null),
  interest_name: z.string().catch("Interest"),
  source_id: z.string().nullable().optional().catch(null),
  source_image_url: z.string().nullable().optional().catch(null),
  source_label: z.string().catch("Source"),
  source_type: sourceTypeSchema.catch("feed"),
  source_url: z.string(),
});

export const updatesDisplayErrorMessage = "There was a problem showing the updates.";

const publishedSchema = z.iso.datetime().transform((published) => new Date(published));
const optionalPublishedSchema = publishedSchema
  .nullable()
  .optional()
  .transform((published) => published ?? undefined);

const updateSchema = z.object({
  image_url: z.string().nullable().optional().catch(null),
  published: optionalPublishedSchema,
  published_at: optionalPublishedSchema,
  source_interest: sourceInterestSchema,
  summary: z.string().nullable().optional(),
  title: z.string().nullable().optional(),
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

const savedCollectionUpdateSchema = z.object({
  saved_at: publishedSchema,
  update: updateSchema,
  update_key: z.string(),
});

const collectionSchema = z.object({
  id: z.enum(["see-later", "liked", "history"]),
  name: z.string(),
  saved_updates: z.array(savedCollectionUpdateSchema).catch([]),
});

export const collectionsPayloadSchema = z.object({
  collections: z.array(collectionSchema).catch([]),
});

export const saveCollectionUpdateResponseSchema = z.object({
  saved_update: savedCollectionUpdateSchema,
});

export const removeCollectionUpdateResponseSchema = z.object({
  ok: z.boolean(),
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

export type Collection = z.infer<typeof collectionSchema>;

export type SavedCollectionUpdate = z.infer<typeof savedCollectionUpdateSchema>;
