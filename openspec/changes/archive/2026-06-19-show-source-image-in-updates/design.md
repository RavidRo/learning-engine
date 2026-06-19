## Context

The Updates page currently renders a single large image slot per update through `UpdateSourceAvatar`. That slot intentionally uses `update.image_url` first, then `source_interest.source_image_url`, then a source-label initial. RAV-29 asks for the source's own image to appear near the source name as well, so users can identify both the update artwork and the source identity.

The update payload already carries `source_interest.source_image_url`, populated from manual source images or dynamically resolved source metadata during update collection. Source metadata is treated as derived data and is not persisted automatically.

## Goals / Non-Goals

**Goals:**

- Show a small source image adjacent to the source label in each update card when the update payload includes a usable source image URL.
- Preserve the large thumbnail's existing update-image-first fallback behavior.
- Keep metadata readable and responsive on phone-width layouts.
- Avoid broken image icons if the small source image fails to load.

**Non-Goals:**

- Do not add or change backend API fields.
- Do not persist automatically resolved source image URLs.
- Do not change update grouping, collection refresh, or save-to-collection behavior.
- Do not add a new source image lookup from the Updates page.

## Decisions

- Reuse `source_interest.source_image_url` for the small source image.
  - Rationale: update collection already resolves the source identity image and sends it with each update.
  - Alternative considered: fetch source images from the Updates page. That would duplicate collection-time resolution, add network work during render, and blur the established boundary that source metadata is supplied with collected updates.

- Keep `UpdateSourceAvatar` responsible for the large thumbnail and add a separate small metadata image.
  - Rationale: the large thumbnail and small source identity have different semantics and sizing. Separating them keeps update-specific artwork visible without changing existing thumbnail fallbacks.
  - Alternative considered: change the large thumbnail to always show source imagery. That would regress the update-specific thumbnail behavior added previously.

- Hide failed or missing small source images instead of showing an initial fallback in the metadata row.
  - Rationale: the adjacent source label already identifies the source, and adding a second fallback initial would create visual noise beside the existing text.
  - Alternative considered: show a tiny source initial. That adds little information and makes update cards busier on narrow screens.

## Risks / Trade-offs

- Some updates will not show a source image beside the source name if the collection payload lacks `source_interest.source_image_url` -> The source label and type remain visible as the fallback identity.
- The same source image can appear twice when an update has no update-specific image and the large thumbnail falls back to the source image -> This preserves existing thumbnail behavior while satisfying the request to show the source image near the name.
- Long source labels plus a new image could crowd mobile cards -> Use fixed small image dimensions, wrapping metadata layout, and existing responsive card rules.
