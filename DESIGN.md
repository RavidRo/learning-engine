---
name: Signal Garden
description: A quiet product interface for organizing interest-based updates into useful signals.
colors:
  background: "#f8faf8"
  surface: "#ffffff"
  surface-muted: "#f3f6f3"
  text: "#111816"
  text-soft: "#3f4f49"
  muted: "#66736e"
  faint: "#a1a1aa"
  border: "#dfe7df"
  border-strong: "#cfdacf"
  accent: "#165a2b"
  accent-hover: "#0f4d27"
  accent-soft: "#eaf3ec"
  accent-border: "#cfe0d1"
  signal: "#d1992a"
  danger: "#dc2626"
  danger-soft: "#fef2f2"
  success: "#1d7a45"
typography:
  display:
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "0"
  headline:
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "0"
  title:
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0"
  body:
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0"
  mono:
    fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    height: "40px"
  button-ghost:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    height: "40px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "11px 12px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "18px"
  badge:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.text-soft}"
    rounded: "{rounded.pill}"
    padding: "4px 8px"
---

# Design System: Signal Garden

## 1. Overview

**Creative North Star: "Signal Workshop"**

Signal Garden is a precise workbench for turning noisy source streams into usable updates. The interface should feel calm, technical, and daily-use ready: a place where technical users can define interests, inspect fresh updates, save useful items, and leave clean structure behind for AI agents.

The visual system is restrained by design. Light garden-tinted neutrals carry most of the surface area, deep green marks primary action and active state, and amber appears only as a small signal accent. The system rejects marketing-page theatrics, decorative garden theming, social-feed engagement patterns, and dashboard chrome that competes with update content.

Components are precise and quiet: compact type, 8px control radii, visible borders, stable spacing, and clear status treatments. Depth exists, but only as layered restraint: borders, tonal surfaces, and focus rings do the work; shadows are reserved for transient feedback.

**Key Characteristics:**
- Restrained product shell with one primary green accent.
- Dense but readable information hierarchy for interests, sources, updates, and collections.
- Borders, tonal surfaces, and focus rings first; shadows only where depth clarifies transient feedback.
- Human-readable states for loading, empty, saved, offline, warning, and error moments.
- Explicit source and interest language that works for both humans and AI agents.

## 2. Colors

The palette is a restrained garden-neutral system: near-white surfaces, cool green-tinted backgrounds, deep ink text, garden green action states, and rare amber signal points.

### Primary
- **Garden Action**: Primary action color for buttons, active navigation, source links, focus borders, and fallback source avatars.
- **Garden Action Hover**: Darker green for hover and pressed action states. Use it only as a state response, never as a second brand accent.
- **Signal Amber**: Tiny highlight color for ranked signal moments, unread markers, or special badges. It must stay rare.

### Secondary
- **Sage Support**: Supporting metadata and low-emphasis brand detail should use muted green-gray text and border treatments, not saturated secondary colors.

### Neutral
- **Quiet Field**: The app background. It is nearly white with a garden tint and should carry most full-page surfaces.
- **White Surface**: Primary content panels, cards, controls, and popovers.
- **Muted Surface**: Secondary panels, metric boxes, empty states, and nested editor areas.
- **Ink Text**: Primary text on light surfaces.
- **Soft Text**: Secondary explanatory text, labels, and subtitles.
- **Muted Text**: Low-emphasis metadata, timestamps, and helper copy.
- **Garden Border**: Default border for panels, cards, and controls.
- **Strong Border**: Stronger border for controls, ghost buttons, and form fields.

### Named Rules

**The One Green Rule.** Garden green is the single primary action voice. Do not introduce another saturated action color for routine commands.

**The Amber Is A Pin Rule.** Amber marks a signal point or important status. It must never become a broad warning palette or decorative wash.

**The Surface First Rule.** Most contrast should come from text, borders, and tonal surfaces. Large color fields are reserved for future onboarding or explicit brand moments, not daily app screens.

## 3. Typography

**Display Font:** Inter with system sans fallbacks.
**Body Font:** Inter with system sans fallbacks.
**Label/Mono Font:** JetBrains Mono for source identifiers, prompts, and technical snippets.

**Character:** Typography is compact, operational, and stable. It should read like a capable product tool, not an editorial article or marketing page.

### Hierarchy
- **Display** (600, 32px, 1.1): App title and rare page-level identity moments. Do not use fluid display type in routine product panels.
- **Headline** (500, 24px, 1.25): Primary panel headings and page section titles.
- **Title** (600, 17px, 1.35): Card titles, group headers, and compact content headings.
- **Body** (400, 14px, 1.5): Main descriptive copy. Keep prose around 65-75ch when it becomes explanatory rather than data-like.
- **Label** (600, 13px, 1.35): Buttons, field labels, status labels, and compact control text.
- **Mono** (500, 11-13px, 1.5): Source URLs, source types, prompt cards, and technical diagnostics.

### Named Rules

**The Product Type Rule.** One sans family carries the interface. Do not add display fonts, tightened letter spacing, or dramatic type contrast for ordinary app UI.

**The Source Precision Rule.** Use mono only where the content is technical or identifier-like. Mono is for source clarity, not decoration.

## 4. Elevation

Signal Garden uses layered restraint: borders and tonal backgrounds create almost all separation. Shell panels, update rows, collection rows, and repeated cards should stay border-led so dense content remains scannable. Shadows are acceptable for transient feedback and tiny anchored details, not as a default card treatment.

### Shadow Vocabulary
- **Keyline Rest** (`0 1px 2px rgba(17, 24, 22, 0.04)`): Tiny anchored depth for brand marks and small floating details.
- **Focus Ring** (`0 0 0 4px rgba(22, 90, 43, 0.1)`): Accessible focus emphasis for fields and controls.
- **Toast Lift** (`0 20px 60px rgba(24, 24, 27, 0.18)`): Transient system feedback.

### Named Rules

**The Border-Led Shell Rule.** The app shell is defined by keylines, spacing, and tonal surfaces. Do not pair 1px borders with broad decorative shadows on panels, cards, or buttons.

**The No Decorative Glass Rule.** Backdrop blur is not part of the core component language. Use opaque or near-opaque surfaces for panels and navigation unless a specific overlay needs it.

## 5. Components

Components are precise and quiet. They use small radii, clear borders, readable density, and consistent state language across interests, sources, updates, and collections.

### Buttons
- **Shape:** Gently curved rectangles (8px radius), minimum 40px height for standard buttons and 34px for compact inline actions.
- **Primary:** Garden Action background with white text, 1px green border, and semibold 14px label.
- **Hover / Focus:** Hover moves up by 1px and darkens the green. Focus should use the same green focus ring vocabulary as fields.
- **Ghost:** White surface, strong border, ink text, and only a border shift on hover.
- **Danger:** Soft red background, red border, red text. Use for destructive actions only.

### Chips
- **Style:** Pills with muted surface fill, garden border, soft text, and 12px semibold labels.
- **State:** Priority chips may use semantic low-saturation fills. Source links use the green soft background and accent text because they navigate to primary source material.

### Cards / Containers
- **Corner Style:** Standard 8px radius. Source avatars may use 10px when image content benefits from slightly more softness.
- **Background:** Panels use white or muted surface with borders. Inner cards and update rows use white or muted surface with borders.
- **Shadow Strategy:** Panels, repeated cards, and rows should not use broad shadows.
- **Border:** Default Garden Border; Strong Border for controls and ghost actions.
- **Internal Padding:** 18px for panels, 16px for interest cards, 14px for update groups and collection panels, 12px for compact nested editor cards.

### Inputs / Fields
- **Style:** White background, Strong Border, 8px radius, ink text, 11px/12px padding.
- **Focus:** Green border shift plus 4px low-opacity green focus ring.
- **Error / Disabled:** Use explicit status callouts and disabled opacity; do not silently hide unavailable actions.

### Navigation
- **Style:** Sticky topbar with bottom border and an opaque or near-opaque garden background.
- **Typography:** 13px medium labels; active navigation becomes ink and bold.
- **States:** Hover and active states change color only. Do not add pills, tabs, or heavy backgrounds unless the navigation model changes.
- **Mobile:** Topbar stacks, nav links wrap, and content controls become full-width where needed.

### Update Cards
- **Style:** Grid rows with source avatar, content, metadata, and collection actions. Use muted surface fill inside bordered update groups.
- **Behavior:** Titles wrap aggressively, descriptions clamp to two lines, and collection actions remain icon buttons with tooltips.
- **State:** Saved collection buttons use soft green fill, green border, and a small saved marker. Keep the marker tiny; the title content remains the focus.

### Callouts and Status
- **Style:** Bordered, 8px radius, muted surface fill, compact heading and explanatory text.
- **States:** Error uses red, warning uses amber, loading/info uses blue, and saved/success uses green. State colors must remain low-saturation fills with readable text.

## 6. Do's and Don'ts

### Do:
- **Do** preserve the product register: restrained, task-first, and familiar to technical users.
- **Do** use Garden Action for primary actions, selected states, focus moments, and source affordances.
- **Do** keep component radii near 8px and use 999px only for badges, chips, and dots.
- **Do** expose loading, empty, saved, offline, warning, and error states with clear recovery text.
- **Do** keep source and interest concepts visually explicit so humans and AI agents can understand the same structure.
- **Do** use borders, tonal backgrounds, and focus rings before reaching for shadows.

### Don't:
- **Don't** make the app feel like a marketing landing page, a social feed optimized for engagement, or a decorative garden-themed interface.
- **Don't** use large green gradients, leaf-pattern backgrounds, playful botanical illustrations, nested cards, or dashboard chrome that competes with the updates themselves.
- **Don't** hide failures behind quiet fallbacks. Collection, source, and agent-integration failures need clear states and recovery paths.
- **Don't** introduce decorative glassmorphism, gradient text, oversized rounded cards, or colored side-stripe borders.
- **Don't** add new saturated accent colors for routine UI states. The palette is restrained on purpose.
- **Don't** use display fonts, tightened heading letter spacing, or editorial typography inside product controls and data rows.
