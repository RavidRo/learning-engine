import { useQueries } from "@tanstack/react-query";

import { resolveSourceImage } from "./api";
import { type Interest, type InterestSource } from "./types";

type SourceLinksProps = {
  interest: Interest;
};

const trimmed = (value: string | null | undefined): string => value?.trim() ?? "";

const canResolveSourceImage = (source: InterestSource): boolean =>
  trimmed(source.imageUrl) === "" && source.url.trim() !== "";

const sourceImageQueryKey = (source: InterestSource) =>
  ["learning-engine", "source-image", source.type, source.url.trim()] as const;

const visibleSources = (interest: Interest): InterestSource[] =>
  interest.sources.filter((source) => source.deletedAt == null);

const sourceImageUrl = (
  source: InterestSource,
  resolvedImageUrl: string | null | undefined,
): string => trimmed(source.imageUrl) || trimmed(resolvedImageUrl);

const useSourceImages = (sources: InterestSource[]): Record<string, string> => {
  const imageQueries = useQueries({
    queries: sources.map((source) => ({
      enabled: canResolveSourceImage(source),
      queryFn: () => resolveSourceImage({ type: source.type, url: source.url.trim() }),
      queryKey: sourceImageQueryKey(source),
    })),
  });

  return Object.fromEntries(
    sources.map((source, index) => [
      source.id,
      sourceImageUrl(source, imageQueries[index]?.data?.imageUrl),
    ]),
  );
};

const SourceLinkImage = ({ imageUrl }: { imageUrl: string }) =>
  imageUrl === "" ? null : <img src={imageUrl} alt="" loading="lazy" />;

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
