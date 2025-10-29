# Skylar Marketing Agents Guide

## Purpose
- Serve as the single source of truth for how we generate print-ready exhibit graphics and plan complementary tooling.
- Capture current capabilities, outstanding work, and key references so agents can quickly orient and contribute.

## Repository Layout

### New Pipeline Architecture
- `backwall_generator.py` / `counter_generator.py` — **primary entry points** for generating each deliverable
- `graphics_config.py` — dataclass-based configuration and specifications (replaces hard-coded dicts)
- `color_management.py` — CMYK color utilities, brand palette, and conversion functions
- `asset_pipeline.py` — asset generation with caching (gradients, vignettes, QR codes)
- `canvas_utils.py` — CMYK-aware canvas operations and drawing primitives
- `backwall_layout.py` / `counter_layout.py` — layout orchestrators for each deliverable
- `PIPELINE_README.md` — comprehensive technical documentation for the new pipeline

### Optional/Utility Scripts
- `generate_graphics.py` — unified CLI orchestrator with CMYK verification and Inkscape integration (optional)
- `graphics_generator.py` — original combined generator (legacy, deprecated)
- `graphics_common.py` — shared geometry, color palette, and helpers (still used for compatibility)

### Supporting Files
- `assets/` — branded imagery (logo) and supporting design artifacts
- `output/` — generated PDFs/JPG proofs with organized subdirectories (raw/, temp/, proofs/)
- `apps/preview/` — React + Vite scaffold for an interactive spec preview (currently template-only)
- `requirements.md` — authoritative production specifications supplied by the event team
- `backwall_brief.md` — narrative creative brief summarizing messaging priorities

## Print Graphics Toolkit

### Overview
The **new pipeline** uses a modular architecture with CMYK enforcement at every stage:

1. **Configuration Layer**: `GraphicsConfig` provides dataclass-based specs that can load from JSON
2. **Color Management**: `CMYKColor` and utilities ensure all colors are CMYK-compliant
3. **Asset Pipeline**: `AssetPipeline` generates and caches intermediate assets (CMYK gradients, vignetted images, QR codes)
4. **Canvas Layer**: `ExhibitGraphicV2` and `CMYKCanvas` provide CMYK-aware drawing operations
5. **Layout Modules**: `BackwallLayout` and `CounterLayout` orchestrate deliverable generation
6. **CLI Orchestration**: `generate_graphics.py` provides unified interface with verification

See `PIPELINE_README.md` for detailed technical documentation.

### Python Environment
```bash
pip install -r requirements.txt
```

Dependencies: `reportlab`, `Pillow`, `qrcode`, `numpy`, and optional `pdf2image`, `pypdfium2`

Optional tools:
```bash
pip install pdf2image pypdfium2
brew install poppler inkscape  # macOS
```

### Running the Generators
```bash
# Generate backwall (production-ready, no guides)
python backwall_generator.py

# Generate counter
python counter_generator.py

# For review with guides visible, edit the scripts to use show_guides=True
```

Output structure:
```
output/
├── temp/                         # Cached intermediate assets
├── proofs/                       # JPG proofs for review
└── *.pdf                         # Final production PDFs
```

Both generators now use the new pipeline internally with CMYK enforcement.

### Customizing Layouts
**New Pipeline:**
- Brand colors: Edit `BRAND_COLORS_CMYK` in `color_management.py` (CMYK values)
- Layout parameters: Edit `BackwallLayout` / `CounterLayout` class attributes
- Specifications: Modify `GraphicsSpec.from_requirements_md()` or load custom JSON

**Legacy:**
- Colors: Edit `BRAND_COLORS` in `graphics_common.py`
- Layout: Modify `draw_backwall_background()` and layout functions

After customizing, review PDFs in `output/` and complete pre-flight checks.

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
