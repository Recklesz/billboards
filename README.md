# Exhibit Graphics Generator

Automated tool for generating exhibition backwall and counter graphics according to print specifications.

## Overview

This tool generates two print-ready graphics:
- **Backwall**: 100 × 217 cm (with 5mm bleed)
- **Counter**: 30 × 80 cm (with 5mm bleed)

All graphics follow professional print specifications including:
- CMYK color mode
- Proper bleed (5mm on all sides)
- Safe areas (50mm inset from trim)
- Crop/trim marks
- No-text zone on backwall (bottom-left 30×80cm)

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) For JPG proof generation

Install pdf2image and poppler:

**macOS:**
```bash
pip install pdf2image
brew install poppler
```

**Linux:**
```bash
pip install pdf2image
sudo apt-get install poppler-utils
```

**Windows:**
```bash
pip install pdf2image
# Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases
# Add to PATH
```

## Usage

### Quick Start

Generate all graphics with guide lines (for review):

```bash
python graphics_generator.py
```

This will create:
- `output/Backwall_100x217cm_bleed5mm_CMYK.pdf`
- `output/Counter_30x80cm_bleed5mm_CMYK.pdf`
- JPG proofs (if pdf2image is installed)

### Customize Your Graphics

Edit the `graphics_generator.py` file:

1. **Modify colors**: Change the background colors in `create_sample_backwall()` and `create_sample_counter()`

2. **Add content**: Add text, logos, and graphics in the safe area sections

3. **Add images**: Use `c.drawImage()` to place embedded images

Example:
```python
# Add an image
c.drawImage("logo.png", x, y, width=200*mm, height=100*mm, mask='auto')
```

### Production Mode

For final print-ready files without guide lines:

```python
generate_all_graphics(output_dir="output", show_guides=False)
```

## Specifications

```json
{
  "units": "mm",
  "backwall": {
    "trim": { "width": 1000, "height": 2170 },
    "bleed": { "all_sides": 5 },
    "safe_inset": 50,
    "no_text_zone": { "x": 0, "y": 0, "width": 300, "height": 800 }
  },
  "counter": {
    "trim": { "width": 300, "height": 800 },
    "bleed": { "all_sides": 5 },
    "safe_inset": 50
  },
  "print": {
    "color_mode": "CMYK",
    "min_effective_dpi": 150,
    "preferred_effective_dpi": 300,
    "outline_all_text": true,
    "embed_images": true
  }
}
```

## Key Layout Rules

### Safe Area
- Keep all text/logos **≥50mm inside** from every trimmed edge
- Content in safe area will definitely be visible after trimming

### Backwall No-Text Zone
- **30×80cm rectangle** flush to bottom-left corner
- Background color/pattern may continue
- **No copy or logos** in this zone

### Color Guidelines
- Use **CMYK** color mode
- Rich black: C60 M40 Y40 K100
- Images: 150-300 DPI at full size minimum

## Pre-flight Checklist

Before sending to print:

- [x] Canvas set to trim size + 5mm bleed on all sides
- [x] CMYK document
- [ ] **All text converted to outlines** (requires Adobe Illustrator or similar)
- [x] All images embedded
- [x] Safe area respected
- [x] No-text zone on backwall respected
- [ ] Image resolution ≥150 DPI at final size
- [x] Exported PDF with crop marks & bleed

## File Output

Generated files:
- `Backwall_100x217cm_bleed5mm_CMYK.pdf`
- `Counter_30x80cm_bleed5mm_CMYK.pdf`
- `Backwall_100x217cm_proof.jpg` (for quick review)
- `Counter_30x80cm_proof.jpg` (for quick review)

## Advanced Usage

### Using the Classes Directly

```python
from graphics_generator import BackwallGraphic, CounterGraphic

# Create custom backwall
graphic = BackwallGraphic()
c = graphic.create_canvas("my_backwall.pdf")

# Add your content
graphic.draw_background()
c.setFillColor(colors.blue)
# ... add more content ...

graphic.draw_crop_marks()
graphic.save()
```

### Adding Custom Images

```python
# In create_sample_backwall() or create_sample_counter()
from reportlab.lib.utils import ImageReader

# Load and embed image
img = ImageReader("your_logo.png")
c.drawImage(img, x, y, width=200*mm, height=100*mm, preserveAspectRatio=True)
```

## Notes

- **Text to outlines**: ReportLab PDFs use fonts. For final production, open PDFs in Adobe Illustrator or Inkscape and convert text to outlines/paths.
- **High-res images**: Ensure all images are at least 150 DPI at their final printed size (300 DPI preferred).
- **Color profiles**: For professional printing, discuss CMYK color profiles with your printer.

## Troubleshooting

**JPG proofs not generating:**
- Install pdf2image: `pip install pdf2image`
- Install poppler (see installation instructions above)

**Text looks wrong:**
- Fonts may differ across systems
- For final production, use Adobe Illustrator to refine typography
- Convert all text to outlines before sending to printer

**Colors look different:**
- Screen displays use RGB, printers use CMYK
- Colors will appear more muted in CMYK
- Request a proof print from your printer

## Support

See full specifications in: `requirements.md`

## License

This tool is for internal use for creating exhibition graphics.
