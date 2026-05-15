import { z } from "zod";

const prioritySchema = z.enum(["high", "medium", "low"]).catch("medium");

const interestSchema = z.object({
  deletedAt: z.string().nullable().optional(),
  enabled: z.boolean().catch(true),
  id: z
    .string()
    .nullable()
    .transform((id) => id ?? crypto.randomUUID()),
  ignore_keywords: z.array(z.string()).catch([]),
  name: z.string().catch("Technology"),
  notes: z.string().nullable().catch(null),
  official_feed_url: z.string().nullable().catch(null),
  official_site_url: z.string().nullable().catch(null),
  priority: prioritySchema,
  type: z.literal("technology").catch("technology"),
  watch_keywords: z.array(z.string()).catch([]),
});

export const interestsPayloadSchema = z.object({
  interests: z.array(interestSchema).catch([]),
});

const technologyUpdateSchema = z.object({
  interest_name: z.string().catch("Technology"),
  published: z.string().optional(),
  title: z.string().optional(),
  url: z.string(),
});

export const technologyUpdatesPayloadSchema = z.object({
  error: z.string().optional(),
  errors: z.array(z.string()).catch([]),
  interests_checked: z.number().catch(0),
  updates: z.array(technologyUpdateSchema).catch([]),
});

export const saveInterestsResponseSchema = z.object({
  saved: interestsPayloadSchema,
});

export type Interest = z.infer<typeof interestSchema>;

export type TechnologyUpdate = z.infer<typeof technologyUpdateSchema>;

export type TechnologyUpdatesPayload = z.infer<typeof technologyUpdatesPayloadSchema>;
