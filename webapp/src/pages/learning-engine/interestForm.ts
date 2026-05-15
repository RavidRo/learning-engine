import { type InterestFormValues, type Priority } from "./types";

/** Converts a free-text label into a stable URL-safe identifier fragment. */
export const slugify = (text: string): string => {
  const slug = text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || crypto.randomUUID();
};

/** Reads a comma-separated form field into trimmed entries. */
const parseList = (value: FormDataEntryValue | null): string[] => {
  const rawValue = typeof value === "string" ? value : "";
  return rawValue
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
};

/** Reads a string form field while treating missing fields as empty content. */
const getString = (formData: FormData, name: string): string => {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
};

/** Parses the add-interest form into the page's domain shape. */
export const readInterestForm = (form: HTMLFormElement): InterestFormValues => {
  const formData = new FormData(form);

  return {
    name: getString(formData, "name"),
    priority: getString(formData, "priority") as Priority,
    officialSiteUrl: getString(formData, "officialSiteUrl"),
    officialFeedUrl: getString(formData, "officialFeedUrl"),
    watchKeywords: parseList(formData.get("watchKeywords")),
    ignoreKeywords: parseList(formData.get("ignoreKeywords")),
    notes: getString(formData, "notes"),
  };
};
