# Inkscape Post-Processing for Print-Ready PDFs

## Overview
After generating PDFs with the Python scripts, use Inkscape CLI to:
- **Convert all text to paths** (no fonts needed for printing)
- **Embed all images** (no external dependencies)

This satisfies the production requirements from `requirements.md` for outlining text and embedding assets.

## Prerequisites

### macOS Installation
```bash
brew install --cask inkscape
```

### Verify Installation
```bash
inkscape --version
# Should show: Inkscape 1.4.2 or later
```

## Manual Post-Processing Commands

### Process Backwall PDF
```bash
inkscape output/Backwall_100x217cm_bleed5mm_CMYK.pdf \
  --actions="select-all;object-to-path;object-stroke-to-path;org.inkscape.filter.selected.embed-image;export-filename:output/Backwall_100x217cm_bleed5mm_CMYK.pdf;export-text-to-path;export-do"
```

### Process Counter PDF
```bash
inkscape output/Counter_30x80cm_bleed5mm_CMYK.pdf \
  --actions="select-all;object-to-path;object-stroke-to-path;org.inkscape.filter.selected.embed-image;export-filename:output/Counter_30x80cm_bleed5mm_CMYK.pdf;export-text-to-path;export-do"
```

### Generic Template
```bash
inkscape <PDF_PATH> \
  --actions="select-all;object-to-path;object-stroke-to-path;org.inkscape.filter.selected.embed-image;export-filename:<PDF_PATH>;export-text-to-path;export-do"
```

## What Each Action Does

| Action | Purpose |
|--------|---------|
| `select-all` | Select all objects in the document |
| `object-to-path` | Convert shapes to paths |
| `object-stroke-to-path` | Convert strokes to paths |
| `org.inkscape.filter.selected.embed-image` | Embed all selected images |
| `export-filename:<path>` | Set output filename |
| `export-text-to-path` | Convert text to paths in the export |
| `export-do` | Execute the export |

## Verification

### Check Text Was Converted
```bash
# Install pdfplumber if needed
pip install pdfplumber

# Test text extraction (should return 0 if properly converted)
python3 -c "
import pdfplumber
pdf = pdfplumber.open('output/Backwall_100x217cm_bleed5mm_CMYK.pdf')
text = pdf.pages[0].extract_text() or ''
print(f'Extractable text length: {len(text)}')
print('✓ Text converted to paths' if len(text) == 0 else '⚠ Text still extractable')
"
```

### Visual Inspection
Open the processed PDF in Adobe Acrobat or Preview:
- Try selecting text - you should NOT be able to select any text
- All text should appear as vector paths
- Images should be embedded (no missing image warnings)

## Backup Strategy

Always create backups before processing:
```bash
cp output/Backwall_100x217cm_bleed5mm_CMYK.pdf output/Backwall_backup.pdf
# Then run Inkscape processing
```

## Workflow

1. **Generate PDFs** using Python scripts:
   ```bash
   python graphics_generator.py
   ```

2. **Create backups**:
   ```bash
   cp output/Backwall_100x217cm_bleed5mm_CMYK.pdf output/Backwall_backup.pdf
   cp output/Counter_30x80cm_bleed5mm_CMYK.pdf output/Counter_backup.pdf
   ```

3. **Post-process with Inkscape** (run both commands):
   ```bash
   inkscape output/Backwall_100x217cm_bleed5mm_CMYK.pdf \
     --actions="select-all;object-to-path;object-stroke-to-path;org.inkscape.filter.selected.embed-image;export-filename:output/Backwall_100x217cm_bleed5mm_CMYK.pdf;export-text-to-path;export-do"

   inkscape output/Counter_30x80cm_bleed5mm_CMYK.pdf \
     --actions="select-all;object-to-path;object-stroke-to-path;org.inkscape.filter.selected.embed-image;export-filename:output/Counter_30x80cm_bleed5mm_CMYK.pdf;export-text-to-path;export-do"
   ```

4. **Verify** text is outlined (see verification section above)

5. **Review** PDFs in viewer to confirm quality

6. **Deliver** to printer

## Expected Output

- Processing typically takes 10-60 seconds per PDF depending on complexity
- You may see warnings like "No pages selected" - these are normal
- File sizes may increase slightly due to embedded images
- All text should be converted to vector paths
- All images should be embedded in the PDF

## Troubleshooting

### Inkscape Not Found
Make sure Inkscape is installed and in your PATH:
```bash
which inkscape
# Should return: /opt/homebrew/bin/inkscape
```

If not found, install with Homebrew (macOS):
```bash
brew install --cask inkscape
```

### Processing Fails or Hangs
- Check disk space (processing may require temporary space)
- Try processing one PDF at a time
- Verify the source PDF is not corrupted (try opening in Preview/Acrobat first)

### Text Still Extractable After Processing
- Ensure you're checking the correct file (not the backup)
- Try running the Inkscape command again
- Verify Inkscape version is 1.2 or later

## Notes

- **Manual process**: This is currently a manual step after PDF generation
- **Automation possible**: Could be integrated into Python scripts in the future
- **Quality**: Visual quality is preserved - this is a lossless conversion
- **Fonts not needed**: After processing, no fonts are required for printing
