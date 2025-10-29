# Skylar Marketing Agents Guide

## Purpose
- Serve as the single source of truth for how we generate print-ready exhibit graphics and plan complementary tooling.
- Capture current capabilities, outstanding work, and key references so agents can quickly orient and contribute.

## Repository Layout
- `graphics_generator.py` — primary script that produces backwall & counter PDFs plus JPG proofs. @graphics_generator.py#1-485
- `graphics_common.py` — shared geometry, color palette, and helpers used by all generators. @graphics_common.py#1-295
- `backwall_generator.py`, `counter_generator.py` — focused entry points for individual deliverables. @backwall_generator.py#1-223 @counter_generator.py#1-76
- `assets/` — branded imagery (logo) and supporting design artifacts.
- `output/` — generated PDFs/JPG proofs checked into the repo for reference. @README.md#145-149
- `apps/preview/` — React + Vite scaffold for an interactive spec preview (currently template-only). @apps/preview/README.md#1-74
- `requirements.md` — authoritative production specifications supplied by the event team. @requirements.md#4-93
- `backwall_brief.md` — narrative creative brief summarizing messaging priorities (keep handy when updating layouts).

## Print Graphics Toolkit
### Overview
The Python tooling centers on `ExhibitGraphic`, which sets up trim + bleed geometry, safe areas, and crop marks for any deliverable. `BackwallGraphic` extends it with the required no-text zone, while `CounterGraphic` handles the counter panel. Supporting helpers register fonts, fit text to widths, and export optional JPG proofs. @graphics_generator.py#18-421

### Python Environment
```bash
pip install -r requirements.txt
```
(`reportlab`, `Pillow`, and optional `pdf2image` are already listed.). @README.md#18-63

Optional JPG proof generation needs:
```bash
pip install pdf2image
brew install poppler  # macOS example
```
@README.md#26-40

### Running the generator
```bash
python graphics_generator.py
```
This creates the production PDFs (guides disabled by default for clean output) inside `output/` and, if `pdf2image` is available, matching JPG proofs. @README.md#49-63

Both `backwall_generator.py` and `counter_generator.py` expose standalone `create_*` functions when you need per-piece control or want to disable guides. @backwall_generator.py#55-205 @counter_generator.py#18-76

### Customizing layouts
- Colors and background geometry live in `draw_backwall_background` and the counter section; adjust the color tokens in `BRAND_COLORS` for brand updates. @graphics_generator.py#44-134
- Headline typography uses `get_headline_font_name`, `fit_multiline_font_size`, and `draw_centered_string`. These helpers ensure text stays inside safe bounds and adapts if Ubuntu Bold is unavailable. @graphics_generator.py#59-383
- The Skylar logo is read from `assets/skylar-clean-logo.png`; confirm the asset exists before running new exports. @graphics_generator.py#384-418

After customizing, review the live PDFs in `output/` and complete pre-flight checks outlined below.

## Production Specifications
`requirements.md` is the contract: keep all work compliant. Key highlights:
- Deliverables: Backwall (100 × 217 cm) and Counter (30 × 80 cm) with +5 mm bleed. @requirements.md#6-19
- Layout rules: 50 mm safe area on every edge; backwall also reserves a 30 × 80 cm no-text zone at the bottom-right of the trim. @requirements.md#20-25
- Color & imagery: CMYK only, embed everything, target 150–300 dpi, rich black recipe provided. @requirements.md#26-32
- Typography: outline fonts before handoff; prefer vectors. @requirements.md#33-37
- Deliverables & packaging: export print PDFs per piece, include crop marks + bleed, ship JPG proofs. @requirements.md#38-51
- Pre-flight checklist doubles as QA before any submission. @requirements.md#84-92

## Assets & Output Management
- Store brand imagery (logos, templates) inside `assets/`. If you introduce fonts, follow the existing pattern (`assets/fonts/YourFont.ttf`). @graphics_generator.py#54-72
- Generated files stay in `output/` for quick reference; prune or archive large historical renders as needed to keep the repo lightweight.

## Interactive Preview App (React + Vite)
The `apps/preview` directory currently contains the stock Vite scaffold and lint config. @apps/preview/README.md#1-74 Roadmap items from the scaffold plan (`new.md`) outline how we intend to evolve this into an interactive layout preview:
1. Load a shared JSON spec (mirrors `requirements.md`) and expose toggles for bleed, safe area, and no-text zone overlays.
2. Use D3 scale helpers to translate millimeters to viewport pixels for SVG rendering.
3. Ship the spec JSON with the build so non-technical reviewers can interactively inspect measurements.
@new.md#1-81

Treat these steps as upcoming work; no preview features are live yet. Align implementation details with the Python geometry to avoid drift.

## Roadmap & Coordination Notes
- **Unify specs:** Once the spec JSON lands, ensure both the Python generator and preview app read from the same source to prevent discrepancies. @new.md#18-62
- **Proof automation:** Optional pipeline to auto-generate proofs via `pdf2image` or `pdftoppm` after exports. @new.md#69-73
- **Tooling hygiene:** Add TypeScript types for the spec, create shared mm-to-point utilities, and wire up lightweight CI checks when the preview app and exporter mature. @new.md#65-74

## Additional References
- Creative direction & messaging cues: `backwall_brief.md`
- Original README (deprecated for live instructions) — retain for historical context.
- Requirements spec (`requirements.md`) — cite directly in reviews to show compliance.

Keep this guide updated as we modify generators, add preview capabilities, or adjust specs from the design team.
