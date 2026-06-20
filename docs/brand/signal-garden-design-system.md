# Signal Garden Design System

Signal Garden is a calm product brand for turning noisy update streams into
useful, cultivated signals. Use
`docs/brand/signal-garden-selected-concept.png` as the visual source of truth
until production logo assets are exported.

## Brand Principles

- Clear signal over decoration: interfaces should help users scan, compare, and
  act on updates without ornamental noise.
- Cultivated, not cute: the garden metaphor should feel organized and useful,
  not playful or rustic.
- Quiet confidence: prefer restrained surfaces, direct labels, and calm motion
  over marketing-style composition.
- Human-readable intelligence: AI-assisted moments should explain outcomes and
  next actions plainly.

## Palette

| Token | Hex | Use |
| --- | --- | --- |
| `--color-garden-900` | `#102018` | Primary text on light surfaces, logo ink |
| `--color-garden-800` | `#204828` | Primary brand green, active states |
| `--color-garden-700` | `#285830` | Hover states, selected borders |
| `--color-sage-600` | `#507870` | Secondary brand accent, icon details |
| `--color-sage-100` | `#E0E8E0` | Soft brand backgrounds |
| `--color-signal-500` | `#C89040` | Small signal accent, badges, focus moments |
| `--color-paper` | `#FAFAF7` | Warm app background when brand theming is needed |
| `--color-white` | `#FFFFFF` | Primary surfaces |

Keep neutrals close to the existing app scale. Use amber sparingly; it should
mark a signal point or important status, not become a general-purpose warning
color.

## Typography

- Use the existing app font stack unless there is a strong product reason to
  change it. The current Inter/system stack matches the geometric wordmark and
  keeps text dense and readable.
- Use medium and semibold weights for headings and controls. Avoid extra-bold
  display typography outside the logo.
- Keep letter spacing at `0`; do not tighten headings.
- Prefer compact, scannable type scales for product screens. Signal Garden
  should feel operational, not editorial.

## Logo Usage

- Preserve the relationship between the rounded-square mark, leaf form, signal
  arcs, amber dot, and wordmark.
- Use the full horizontal lockup when there is enough width. Use the icon-only
  mark for favicons, app icons, compact navigation, and small empty states.
- Maintain clear space around the mark at least equal to the amber dot diameter.
- Do not recolor individual logo parts independently, rotate the icon, add
  shadows, or place the full-color mark on saturated backgrounds.
- On dark or image backgrounds, use an approved one-color export instead of
  improvising effects in CSS.

## Component Tone

- Components should feel precise, quiet, and work-focused: small radii, clear
  hierarchy, visible affordances, and stable spacing.
- Primary actions should use garden green. Secondary actions should remain
  neutral with green hover or selected states.
- Use sage for supporting metadata, source indicators, and low-emphasis brand
  details.
- Use amber for tiny highlights: unread signal dots, ranked insight markers, or
  a single high-value badge.
- Avoid large green gradients, decorative blobs, leaf-pattern backgrounds, or
  nested card compositions.

## CSS Variable Notes

When implementing brand/theme changes, extend the existing `:root` variable
pattern in `webapp/src/styles.css` instead of hard-coding colors in components.
Map brand tokens into semantic variables so component code stays stable:

```css
:root {
  --brand-primary: #204828;
  --brand-primary-hover: #285830;
  --brand-secondary: #507870;
  --brand-accent: #c89040;
  --brand-soft: #e0e8e0;
}
```

Then assign semantic app tokens such as `--accent`, `--accent-hover`,
`--surface-muted`, or status-specific tokens from those brand values. Keep
contrast checks part of the implementation review, especially for sage and amber
text on light backgrounds.
