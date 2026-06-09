## 1. Updates Page Layout

- [x] 1.1 Move `UpdatesSummary` out of the side-column layout so it renders above the updates feed whenever an updates payload is available.
- [x] 1.2 Simplify the updates content wrapper so source errors, empty state, and grouped updates can use the full panel width below the summary.

## 2. Responsive Styling

- [x] 2.1 Update `.updates-layout`, `.updates-summary`, and related summary box styles so the summary appears as a top row on wide screens.
- [x] 2.2 Ensure the summary boxes wrap or stack cleanly on tablet and mobile widths without overlapping header controls or feed content.

## 3. Verification

- [x] 3.1 Run the narrowest useful webapp check for the layout change.
- [x] 3.2 Review the Updates page visually at desktop and mobile widths, or document why local visual verification was not possible.

  Local visual verification was not possible in this session because the repo does not include browser screenshot tooling, the sandbox blocked binding the Vite dev server to `127.0.0.1:5173`, and the escalated dev-server approval request timed out twice. Verification performed: `task web:check`.

## 4. Compact Follow-up

- [x] 4.1 Remove the redundant visible time-window heading and grouping description from the Updates panel header.
- [x] 4.2 Compress summary statistics into a lower-height inline metric row.
- [x] 4.3 Re-run the narrowest useful webapp check after the compact layout adjustment.

## 5. Header Summary Follow-up

- [x] 5.1 Move loaded summary statistics into the Updates panel header row opposite the time-window and refresh controls.
- [x] 5.2 Remove the separate summary row from the updates content flow.
- [x] 5.3 Re-run the narrowest useful webapp check after the header summary adjustment.
