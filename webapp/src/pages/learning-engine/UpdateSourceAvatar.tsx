import { useState } from "react";

import { type Update } from "./types";

const sourceInitial = (label: string): string => label.trim().charAt(0).toUpperCase() || "•";

const presentImageUrl = (imageUrl: string | null | undefined): string | undefined => {
  const trimmedImageUrl = imageUrl?.trim();
  return trimmedImageUrl === "" ? undefined : trimmedImageUrl;
};

const updateThumbnailUrl = (update: Update): string | undefined =>
  [update.image_url, update.source_interest.source_image_url]
    .map(presentImageUrl)
    .find((imageUrl) => imageUrl !== undefined);

export const UpdateSourceAvatar = ({ update }: { update: Update }) => {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);
  const imageUrl = updateThumbnailUrl(update);
  const showImage = imageUrl !== undefined && imageUrl !== failedImageUrl;

  if (!showImage) {
    return (
      <span className="source-avatar fallback" aria-hidden="true">
        {sourceInitial(update.source_interest.source_label)}
      </span>
    );
  }

  return (
    <img
      alt=""
      className="source-avatar"
      loading="lazy"
      onError={() => setFailedImageUrl(imageUrl)}
      src={imageUrl}
    />
  );
};
