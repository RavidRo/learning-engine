---
name: ui-ux-foundations-review
description: Review or redesign web and app interfaces using foundational UI/UX concepts: signifiers, affordances, hierarchy, contrast, whitespace, responsive grids, typography, semantic color, dark mode depth, shadows, icons, component states, forms, micro-interactions, overlays, and visual density. Use when the user asks whether a page uses space well, feels cluttered or empty, has weak hierarchy, needs layout critique, or needs practical design improvements without focusing primarily on implementation mechanics.
---

# UI/UX Foundations Review

## Source Lens

This skill distills the practical concepts from Kole Jain's "Every UI/UX Concept Explained in Under 10 Minutes" into an interface review workflow. Treat the video as a foundation, not a rigid checklist: diagnose how the page communicates, scans, groups, and responds.

## When to Use

Use this skill for:

- Layout, spacing, visual density, and page-space utilization critique.
- UI reviews where the question is "does this design work?" rather than "is this code correct?"
- Redesign guidance for cards, dashboards, landing pages, forms, navigation, overlays, and repeated content.
- Feedback that should produce concrete visual changes without requiring a full design-system rewrite.

Do not use it as a primary accessibility, performance, or code architecture audit, though those issues may be noted if they affect the design.

## Review Workflow

1. Establish context.
   - Identify the page type: landing page, dashboard, content list, form flow, settings page, detail page, marketing section, etc.
   - Identify the primary user task and the most important item on the screen.
   - If screenshots or a running app are available, inspect the actual rendered UI before relying on code.

2. Check signifiers and affordances.
   - Interactive elements should look interactive without explanatory copy.
   - Selected, inactive, disabled, hover, pressed, loading, success, warning, and error states should be visually distinct.
   - Grouping should make relationships obvious through containers, proximity, alignment, and state.
   - Icons should clarify meaning or motion, not merely decorate.

3. Diagnose hierarchy.
   - The most important content should be near the top or dominant in size, weight, color, contrast, or imagery.
   - Secondary metadata should be smaller, quieter, or lower in the composition.
   - Repeated cards should avoid spreadsheet-like sameness by using contrast, image/media, position, and color.
   - If everything has equal emphasis, identify the one or two elements that should lead.

4. Evaluate space and grouping.
   - Prefer meaningful whitespace over filling every gap.
   - Group related items closer together; separate unrelated groups with larger gaps.
   - Use spacing scales consistently, commonly multiples of 4, but do not treat grids as dogma.
   - For structured repeated content, use grids to support responsive behavior; for expressive pages, composition can break the grid when it improves scanning.
   - Call out empty space that is not doing useful work: dead margins, overly narrow columns, isolated controls, or content that forces excessive scrolling.

5. Review typography.
   - Most interfaces need one strong sans-serif family, not many fonts.
   - Limit font-size count. Landing pages can have broader scale; dashboards and dense tools should use a tighter range.
   - Large headings usually benefit from tighter line height and slightly tighter tracking, but avoid viewport-scaled type and ensure text wraps cleanly.
   - Body, label, metadata, and button text should support the hierarchy rather than compete with it.

6. Review color and depth.
   - Start from one primary/brand color and build purposeful tints/shades.
   - Use semantic colors for meaning: success, warning, danger, trust, active, focus, and disabled.
   - In dark mode, create depth by making foreground surfaces lighter than the background; avoid harsh bright borders or oversaturated chips.
   - In light mode, use shadows subtly. If the shadow is the first thing noticed, it is too strong.
   - Reserve stronger elevation for popovers, dialogs, menus, and content that floats above other content.

7. Review components and interaction feedback.
   - Buttons should have clear variants: primary, secondary, ghost, destructive, icon-only where appropriate.
   - Icon size should harmonize with the text line height.
   - Inputs need focus, error, warning, disabled, and helper-message treatment where relevant.
   - Every user action should produce feedback: visual state, loading indicator, confirmation, success message, or micro-interaction.
   - Micro-interactions should confirm action or guide attention before adding playfulness.

8. Review overlays and media-backed text.
   - Text over imagery must have a reliable readable region.
   - Prefer gradients or progressive blur overlays when preserving image quality matters.
   - Do not let overlays destroy the image or leave text contrast dependent on unpredictable image content.

## Output Format

Lead with the highest-impact findings, not a general essay.

For each finding include:

- `Issue`: What is visually or experientially wrong.
- `Why it matters`: The UI/UX concept being violated.
- `Fix`: A concrete layout, spacing, hierarchy, state, or styling change.

When useful, include a short priority plan:

1. Fix hierarchy and primary task visibility.
2. Rebalance whitespace and grouping.
3. Tighten typography and color semantics.
4. Add missing states and feedback.
5. Polish depth, overlays, and micro-interactions.

## Biases

- Prefer better composition over adding more decoration.
- Prefer meaningful density over both cramped dashboards and empty marketing-page sprawl.
- Prefer visible state and feedback over explanatory text.
- Prefer patterns proven in real products over novelty.
- Preserve the product's existing design system unless it is causing the problem.
