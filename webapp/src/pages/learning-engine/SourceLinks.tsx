import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { resolveSourceImages } from "./api";
import { type Interest, type InterestSource } from "./types";

type SourceLinksProps = {
  interest: Interest;
};

const trimmed = (value: string | null | undefined): string => value?.trim() ?? "";

/**
 * Indicates whether a source should use automatic image resolution.
 *
 * @param source - Interest source to inspect.
 * @returns True when the source has no manual image URL and has a non-empty URL.
 */
const canResolveSourceImage = (source: InterestSource): boolean =>
  trimmed(source.imageUrl) === "" && source.url.trim() !== "";

/**
 * Builds the stable React Query key for resolving a batch of source images.
 *
 * @param sources - Interest sources whose type and trimmed URL identify the lookup.
 * @returns A query key scoped to Signal Garden source-image resolution.
 */
const sourceImagesQueryKey = (sources: InterestSource[]) =>
  [
    "signal-garden",
    "source-images",
    sources.map((source) => [source.id, source.type, source.url.trim()]),
  ] as const;

const visibleSources = (interest: Interest): InterestSource[] =>
  interest.sources.filter((source) => source.deletedAt == null);

/**
 * Selects the image URL to display for a source.
 *
 * @param source - Interest source that may include a manual image URL.
 * @param resolvedImageUrl - Optional image URL returned by automatic resolution.
 * @returns The trimmed manual image URL when present, otherwise the trimmed resolved URL.
 */
const sourceImageUrl = (
  source: InterestSource,
  resolvedImageUrl: string | null | undefined,
): string => trimmed(source.imageUrl) || trimmed(resolvedImageUrl);

/**
 * Resolves display image URLs for visible sources.
 *
 * @param sources - Interest sources to map by source ID.
 * @returns A record from source.id to the manual or resolved image URL.
 *
 * Uses one React Query request for sources that need automatic lookup; manual
 * image URLs are returned without resolution.
 */
const useSourceImages = (sources: InterestSource[]): Record<string, string> => {
  const automaticSources = sources.filter(canResolveSourceImage);
  const imageQuery = useQuery({
    enabled: automaticSources.length > 0,
    queryFn: () =>
      resolveSourceImages(
        automaticSources.map((source) => ({
          id: source.id,
          type: source.type,
          url: source.url.trim(),
        })),
      ),
    queryKey: sourceImagesQueryKey(automaticSources),
  });
  const resolvedImages = Object.fromEntries(
    (imageQuery.data?.images ?? []).map((image) => [image.sourceId, image.imageUrl]),
  );

  return Object.fromEntries(
    sources.map((source) => [source.id, sourceImageUrl(source, resolvedImages[source.id])]),
  );
};

const SourceLinkImage = ({ imageUrl }: { imageUrl: string }) => {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);

  if (imageUrl === "" || imageUrl === failedImageUrl) {
    return null;
  }

  return <img src={imageUrl} alt="" loading="lazy" onError={() => setFailedImageUrl(imageUrl)} />;
};

export const SourceLinks = ({ interest }: SourceLinksProps) => {
  const sources = visibleSources(interest);
  const sourceImages = useSourceImages(sources);

  return (
    <div className="source-links">
      {sources.map((source) => {
        const imageUrl = sourceImages[source.id] ?? "";

        return (
          <a href={source.url} key={source.id} target="_blank" rel="noreferrer">
            <SourceLinkImage imageUrl={imageUrl} />
            <span className="source-link-label">{source.label}</span>
            <span className="source-link-type">{source.type}</span>
          </a>
        );
      })}
    </div>
  );
};
