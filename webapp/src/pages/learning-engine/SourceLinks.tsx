import { type Interest } from "./types";

type SourceLinksProps = {
  interest: Interest;
};

export const SourceLinks = ({ interest }: SourceLinksProps) => (
  <div className="source-links">
    {interest.sources
      .filter((source) => source.deletedAt == null)
      .map((source) => (
        <a href={source.url} key={source.id} target="_blank" rel="noreferrer">
          {source.label}
          <span>{source.type}</span>
        </a>
      ))}
  </div>
);
