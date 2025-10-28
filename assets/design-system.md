# Skylar Design System

## Purpose
This document explains the visual language of the Skylar platform so designers can deliver assets that align with the existing UI. It summarizes the tokens defined in our Material-UI theme alongside the styling patterns used across key screens such as Main Menu, Call View ("New View"), Assessment, and Welcome.

## Brand Foundations

### Color Palette
The palette balances calming teals with energetic accents. Core tokens are defined in the MUI theme and should be referenced by name during handoff.

| Token | Hex | Typical Usage |
| --- | --- | --- |
| primary.main | `#37bcd9` | Primary actions, highlights, icons |
| primary.light | `#8ee6f7` | Hover states, soft backgrounds |
| primary.dark | `#197fa1` | Pressed states, strong accents |
| secondary.main | `#8ee6f7` | Secondary actions, cards |
| tertiary.main | `#ffa0a3` | Celebration, alert banners |
| info.main | `#4a7aaf` | Informational chips, links |
| success.main | `#2A7D5F` | Positive feedback |
| warning.main | `#b78a2b` | Cautions, attention elements |
| error.main | `#9C4F60` | Errors, destructive actions |
| text.primary | `#0e2e3e` | Headings and body copy |
| background.default | `#F8FAFC` | App background |
| white.main | `#F9F9F9` | Card fills on dark surfaces |

Pastel variants (`pastel`, `light`) provide translucent washes used on cards, badges, and gradients. Each color family also includes a `shadow` tone for elevated elements.@apps/web/src/assets/theme/base/colors.js#15-330

### Gradients & Backgrounds
Gradients reinforce brand vibrancy. The primary gradient blends `#8ee6f7 → #37bcd9`; the secondary gradient deepens into `#197fa1`. Subtle background washes (`rgba(142, 230, 247, 0.15 → 0.05)`) soften large surfaces such as dashboards and hero sections.@apps/web/src/assets/theme/base/colors.js#151-208

### Typography
Skylar uses Ubuntu for headings and body text, with display weights for hero copy. Sizes are defined in rems for responsive scaling:

- Headings: `h1` 48px, `h2` 36px, `h3` 30px, `h4` 24px, `h5` 20px, `h6` 16px.
- Body: `body1` 20px regular, `body2` 16px light.
- Buttons: uppercase, 14px light.

Display styles (`d1–d6`) support large marketing statements such as the rotating hero headline on the Welcome page.@apps/web/src/assets/theme/base/typography.js#30-205

### Breakpoints & Spacing
We follow Material-UI’s breakpoint scale (xs 0, sm 576, md 768, lg 992, xl 1200, xxl 1400). Layouts often switch from stacked to split panels at `md`.@apps/web/src/assets/theme/base/breakpoints.js#22-31

Spacing respects the MUI 8px grid via the `pxToRem` helper; margin/padding props use integers that map to 0.25rem increments.

### Border Radius
Cards and interactive elements share rounded corners for approachability:
- `xs` 1.6px
- `sm` 2px
- `md` 6px
- `lg` 8px
- `xl` 12px
- `xxl` 16px
- `section` 160px (used for large hero sections)

Buttons or chips should align with these tokens.@apps/web/src/assets/theme/base/borders.js#30-51

### Shadows & Elevation
Shadow presets range from `xs` (subtle) to `xxl` (hero cards) with brand-colored overlays for accent buttons. Use `shadow="md"` for standard cards and `shadow="lg"` or `xl` for hero sections. Colored shadows (`primary`, `secondary`, etc.) reinforce brand hues on floating CTAs.@apps/web/src/assets/theme/base/boxShadows.js#30-117

### Global Treatments
Anchor links transition from dark navy to info blue on hover, and smooth scrolling is enabled globally.@apps/web/src/assets/theme/base/globals.js#21-39

## Component Styling Patterns

### MK Component Library
We wrap Material-UI with MK components (e.g., `MKBox`, `MKTypography`, `MKButton`) so design tokens are applied consistently. Always prefer component props (`color`, `variant`, `borderRadius`) before using ad-hoc styles.@apps/web/src/components/MKBox/index.js#1-66 @apps/web/src/components/MKButton/index.js#1-76 @apps/web/src/components/MKTypography/index.js#1-84

### Dashboard Cards (Main Menu)
Primary cards use gradient backgrounds, 12–16px radii, and medium shadows. Subtle motion enhances interactivity (fade & slide on load, hover scale). Typography contrasts with white/pastel overlays for legibility.@apps/web/src/pages/MainMenu/components/ResumeRoleplayCard.js#30-255 @apps/web/src/pages/MainMenu/index.js#41-107

Use this recipe for analytics widgets: gradient or pastel background, layered light texture, bold headline, supporting copy, and rounded contained button.

### Call Experience Surface (New View)
The Call View lives inside the dashboard shell with modal overlays, FAB settings button, and bottom control bar. Primary actions stay teal; dialogs lean on white surfaces with navy text. Keep controls spacious and avoid dense clustering to mirror the existing hierarchy.@apps/web/src/pages/NewView/NewView.js#292-390

### Assessment Results
Assessment cards appear on white surfaces with `xl` radius, `lg` shadow, and centered content. Tabs and conversation panels alternate between white cards and light backgrounds to create hierarchy. Maintain generous whitespace to highlight performance metrics.@apps/web/src/pages/Assessment/index.js#158-268

### Welcome Hero
Marketing entry points use dark navy backgrounds with animated gradients and floating typography. White buttons (outlined or contained with translucency) sit on top. Designers should ensure hero illustrations respect the teal gradient palette and include gentle motion where possible.@apps/web/src/pages/Welcome/index.js#58-205

## Interaction & Motion

- Framer Motion handles entrance animations (fade + slide) for dashboard cards and CTA buttons. Use 0.5s ease-out for load-in, 1.05 scale for hover, and subtle translateY wave animations for hero copy.@apps/web/src/pages/MainMenu/index.js#17-39 @apps/web/src/pages/MainMenu/components/ResumeRoleplayCard.js#30-255
- MUI transitions (`Fade`, `Grow`, `Zoom`) provide progressive disclosure on marketing pages. Favor staged delays (400–1500ms) to guide attention without overwhelming.@apps/web/src/pages/Welcome/index.js#87-196
- Floating action buttons (FAB) appear only during active calls and should be single-color teal with white iconography.@apps/web/src/pages/NewView/NewView.js#353-385

## Layout Guidelines

1. **Page Shells**: Core screens use `DashboardLayout` with card-based content sections stacked vertically on mobile and split across two columns on desktop. Maintain 24–32px gutters and 32px vertical spacing between sections.@apps/web/src/pages/MainMenu/index.js#41-107 @apps/web/src/pages/NewView/NewView.js#292-390
2. **Hero & Marketing Pages**: Use `PageLayout` with full-bleed backgrounds, centered stacks, and large display typography. Buttons should contrast strongly against the background (white on navy hero).@apps/web/src/pages/Welcome/index.js#58-205
3. **Modals & Overlays**: Keep surfaces white with 12px radius, `md` shadow, and accent buttons in primary teal. Icons should follow Material Design guidelines for clarity.

## Asset Handoff Tips

- Provide SVG or PNG assets that can sit on teal gradients without clashing; favor line-drawn or soft-shaded illustrations.
- When supplying button states, define default, hover, and disabled using the primary palette and translucent overlays described above.
- Supply typography styles referencing token names (e.g., `h4`, `body2`) rather than fixed pixel sizes so developers can map them directly to MK components.
- Indicate whether sections require motion; note duration/easing so we can replicate them with Framer Motion or MUI transitions.

This guide should give designers the context needed to craft visuals consistent with Skylar’s established aesthetic while allowing room for evolution.
