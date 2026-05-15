import { type Interest } from "./types";

type OfficialLinksProps = {
  interest: Interest;
};

export const OfficialLinks = ({ interest }: OfficialLinksProps) => (
  <div className="official-links">
    {interest.official_site_url ? (
      <a href={interest.official_site_url} target="_blank" rel="noreferrer">
        official site
      </a>
    ) : null}
    {interest.official_feed_url ? (
      <a href={interest.official_feed_url} target="_blank" rel="noreferrer">
        updates feed
      </a>
    ) : null}
    {interest.watch_keywords.map((keyword) => (
      <span className="source" key={`watch-${keyword}`}>
        watch:{keyword}
      </span>
    ))}
    {interest.ignore_keywords.map((keyword) => (
      <span className="source" key={`ignore-${keyword}`}>
        ignore:{keyword}
      </span>
    ))}
  </div>
);
