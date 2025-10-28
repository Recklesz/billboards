# Project Scaffold Plan

## Overview
We will maintain a single source of truth for exhibit graphics specs and generate both an interactive preview and production-ready print outputs.

```
skylar-marketing/
├── requirements.md                 # Original spec
├── new.md                          # This plan
├── spec/
│   └── graphics.json               # Shared geometry + print settings
├── apps/
│   └── preview/                    # React + Vite preview client
└── tools/
    └── export_pdf.py               # ReportLab-based PDF exporter
```

## Shared specification (`spec/graphics.json`)
1. Copy the JSON block from `requirements.md` @requirements.md#56-80.
2. Add optional keys for background assets, color themes, and text blocks you plan to render.
3. Keep units in millimeters to match print expectations.

## Interactive preview (`apps/preview`)
1. In the repo root, run:
   ```bash
   npm create vite@latest apps/preview -- --template react-ts
   ```
2. `cd apps/preview` and install helpers:
   ```bash
   npm install d3-scale clsx
   ```
   *`d3-scale` simplifies proportional scaling from mm to viewport pixels.*
3. Create `src/spec.ts` that loads the JSON via `fetch('/spec/graphics.json')`.
4. Replace the default `App.tsx` with an SVG-driven layout:
   - Draw trim rectangles, bleed outline, safe inset, and backwall no-text zone using mm → px scaling.
   - Provide toggles (checkboxes) for overlays.
   - Render measurement labels along axes.
5. Add `src/components/GuideLayer.tsx`, `src/hooks/useSpec.ts`, and `src/utils/geometry.ts` for clean separation.
6. Configure Vite dev server proxy:
   - In `vite.config.ts`, expose `/spec` directory (use `fs.readFileSync` via plugin or simple static copy).
   - During development, symlink or copy `spec/graphics.json` into `apps/preview/public/spec/graphics.json`.
7. For production build, ensure `spec/graphics.json` ships inside `dist/spec/` for static hosting.

## PDF exporter (`tools/export_pdf.py`)
1. Create Python virtual environment in repo root (e.g., `python -m venv .venv`).
2. Activate it and install ReportLab + Pillow:
   ```bash
   pip install reportlab pillow
   ```
3. Implement exporter structure:
   - Parse `spec/graphics.json`.
   - Convert mm → points (`mm * 72 / 25.4`).
   - For each deliverable (backwall, counter):
     1. Create `BaseDocTemplate` at bleed dimensions.
     2. Draw crop marks, safe area, and no-text zone using `canvas` primitives.
     3. Embed background imagery (if any) with `drawImage`, forcing CMYK via Pillow conversion.
     4. Add metadata and save as `Backwall_100x217cm_bleed5mm_CMYK.pdf`, etc.
   - Optionally export low-res proofs using `canvas` preview layer or convert via `wand` later.
4. Provide CLI parameters using `argparse`:
   ```bash
   python tools/export_pdf.py --spec spec/graphics.json --assets assets/
   ```
5. Document run instructions in `README.md` once script is ready.

## Shared utilities
- Create `utils/mm.py` (or similar) with constants for conversions to avoid duplication.
- Consider TypeScript declaration for JSON shape to keep preview in sync with Python dataclass model.

## Optional enhancements
1. **Storybook integration:** Embed the SVG preview inside Storybook for design reviews.
2. **Automated proofs:** After PDF export, call `pdftoppm` to generate quick JPG previews.
3. **Templated backgrounds:** Store AI/SVG templates in `assets/templates/` and let the exporter place dynamic text.
4. **CI linting:** Add GitHub Action to validate JSON schema and run `npm test`/`pytest` once you introduce tests.

## Next manual steps
1. Run the Vite scaffolding command (already completed), then install the extra preview dependencies (Step 2 above).
2. Create `spec/graphics.json` and copy the existing YAML block into it.
3. Set up the React components and utilities outlined above.
4. Initialize the Python tooling and stub out `export_pdf.py` with simple rectangles to validate dimensions.
5. Commit early: `git add .` then `git commit -m "chore: scaffold graphics tooling"` once the basics are in place.
