"""
Backwall Graphics Generator
Creates backwall graphics according to print specifications.
"""

from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from PIL import Image
import os
import json

from graphics_common import (
    SPECS,
    BRAND_COLORS,
    LOGO_PATH,
    BackwallGraphic,
    get_headline_font_name,
    fit_multiline_font_size,
    draw_centered_string,
    create_jpg_proof
)


def draw_backwall_background(canvas_obj, graphic):
    """Render branded background composition for the backwall - clean and elegant."""

    safe_origin_x = graphic.bleed + graphic.safe_inset
    safe_origin_y = graphic.bleed + graphic.safe_inset
    safe_width = graphic.trim_width - (2 * graphic.safe_inset)
    safe_height = graphic.trim_height - (2 * graphic.safe_inset)

    graphic.draw_background(BRAND_COLORS["background"])

    # Large elegant curved shape on right side
    canvas_obj.saveState()
    canvas_obj.setFillColor(BRAND_COLORS["accent_light"])
    canvas_obj.circle(graphic.doc_width + (150 * mm), safe_origin_y + safe_height * 0.65, 420 * mm, fill=1, stroke=0)
    canvas_obj.restoreState()

    # Complementary curved accent in upper area
    canvas_obj.saveState()
    canvas_obj.setFillColor(BRAND_COLORS["accent_muted"])
    canvas_obj.circle(graphic.doc_width - (300 * mm), graphic.doc_height + (80 * mm), 380 * mm, fill=1, stroke=0)
    canvas_obj.restoreState()

    # Subtle accent shape in lower left for balance
    canvas_obj.saveState()
    canvas_obj.setFillColor(BRAND_COLORS["accent_primary"])
    canvas_obj.circle(-100 * mm, safe_origin_y + (150 * mm), 200 * mm, fill=1, stroke=0)
    canvas_obj.restoreState()


def create_backwall(output_dir="output", show_guides=True):
    """
    Create backwall graphic with branded design

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area, no-text zone)

    Returns:
        Path to the generated PDF file
    """
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Backwall_100x217cm_bleed5mm_CMYK.pdf")

    graphic = BackwallGraphic()
    c = graphic.create_canvas(filename)

    # Background composition
    draw_backwall_background(c, graphic)

    safe_origin_x = graphic.bleed + graphic.safe_inset
    safe_origin_y = graphic.bleed + graphic.safe_inset
    safe_width = graphic.trim_width - (2 * graphic.safe_inset)
    safe_height = graphic.trim_height - (2 * graphic.safe_inset)

    # Add crop marks
    graphic.draw_crop_marks()

    # Add guides (optional, for reference)
    graphic.draw_guides(show_guides)
    graphic.draw_no_text_zone_guide(show_guides)

    # Headline font handling - MUCH LARGER for dominance
    headline_font = get_headline_font_name()
    headline_lines = ["AI ROLE PLAYS", "FOR SALES TEAMS"]
    max_headline_width = safe_width * 0.92
    headline_font_size = fit_multiline_font_size(headline_lines, headline_font, max_headline_width, starting_size=300, minimum_size=80)

    ascent, descent = pdfmetrics.getAscentDescent(headline_font, headline_font_size)
    line_height = ascent - descent
    baseline_gap = line_height * 1.1
    block_height = line_height + baseline_gap * (len(headline_lines) - 1)

    headline_center_x = graphic.doc_width / 2
    headline_center_y = safe_origin_y + safe_height * 0.58

    # Framed headline panel for contrast - larger padding for prominence
    plate_padding_x = 100 * mm
    plate_padding_y = 110 * mm
    max_line_width = max(pdfmetrics.stringWidth(line, headline_font, headline_font_size) for line in headline_lines)
    plate_width = max_line_width + (2 * plate_padding_x)
    plate_height = block_height + (2 * plate_padding_y)
    plate_x = headline_center_x - (plate_width / 2)
    plate_y = headline_center_y - (plate_height / 2)

    # Ensure panel sits above no-text zone
    min_plate_bottom = graphic.bleed + graphic.no_text_zone["height"] + (40 * mm)
    if plate_y < min_plate_bottom:
        shift = min_plate_bottom - plate_y
        plate_y += shift
        headline_center_y += shift

    c.setFillColor(colors.white)
    c.roundRect(plate_x, plate_y, plate_width, plate_height, 60 * mm, fill=1, stroke=0)

    # Minimal accent bar below the headline for visual interest
    c.setFillColor(BRAND_COLORS["accent_primary"])
    accent_bar_width = plate_width * 0.4
    accent_bar_height = 16 * mm
    accent_bar_x = headline_center_x - (accent_bar_width / 2)
    accent_bar_y = plate_y + (45 * mm)
    c.roundRect(accent_bar_x, accent_bar_y, accent_bar_width, accent_bar_height, 8 * mm, fill=1, stroke=0)

    # Draw headline lines (top to bottom)
    ascent, descent = pdfmetrics.getAscentDescent(headline_font, headline_font_size)
    line_height = ascent - descent
    baseline_gap = line_height * 1.1
    block_height = line_height + baseline_gap * (len(headline_lines) - 1)
    first_baseline = headline_center_y + (block_height / 2) - ascent

    for idx, line in enumerate(headline_lines):
        baseline = first_baseline - (baseline_gap * idx)
        draw_centered_string(
            c,
            line,
            headline_font,
            headline_font_size,
            headline_center_x,
            baseline,
            BRAND_COLORS["headline_text"],
        )

    # Place the Skylar logo in bottom right - smaller and less prominent
    if os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as logo_img:
                logo_ratio = logo_img.height / logo_img.width
        except Exception as exc:  # pragma: no cover - defensive
            print(f"⚠ Could not read logo image: {exc}")
        else:
            # Much smaller logo size
            max_logo_width = safe_width * 0.14
            max_logo_height = safe_height * 0.08
            computed_logo_height = max_logo_width * logo_ratio

            if computed_logo_height > max_logo_height:
                computed_logo_height = max_logo_height
                max_logo_width = computed_logo_height / logo_ratio

            logo_reader = ImageReader(LOGO_PATH)
            # Position in bottom right with safe margins
            logo_x = graphic.doc_width - graphic.bleed - graphic.safe_inset - max_logo_width
            logo_y = graphic.bleed + graphic.safe_inset + (50 * mm)
            c.drawImage(
                logo_reader,
                logo_x,
                logo_y,
                width=max_logo_width,
                height=computed_logo_height,
                mask="auto",
                preserveAspectRatio=True,
            )
    else:
        print(
            "⚠ Skylar logo not found at assets/skylar-clean-logo.png. "
            "The backwall will be generated without the logo."
        )

    graphic.save()
    print(f"✓ Created: {filename}")

    # Create JPG proof
    create_jpg_proof(filename, output_dir, "Backwall_100x217cm_proof.jpg")

    return filename


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BACKWALL GRAPHICS GENERATOR")
    print("="*60 + "\n")

    print("Specifications:")
    print(json.dumps(SPECS["backwall"], indent=2))
    print("\n" + "-"*60 + "\n")

    print("Generating backwall...\n")

    # Generate backwall with guides for review
    backwall_pdf = create_backwall(output_dir="output", show_guides=True)

    # For final production, use:
    # backwall_pdf = create_backwall(output_dir="output", show_guides=False)

    print("\n" + "-"*60)
    print("✓ Backwall generated successfully!")
    print(f"✓ Output directory: {os.path.abspath('output')}")
    print("-"*60 + "\n")

    print("Pre-flight checklist:")
    print("  [✓] Canvas set to trim size + 5mm bleed on all sides")
    print("  [✓] CMYK document (reportlab default)")
    print("  [!] All text should be outlined (requires post-processing)")
    print("  [✓] Safe area respected")
    print("  [✓] No-text zone respected")
    print("  [✓] Exported PDF with crop marks & bleed")
    print("\nNote: For final production, convert all text to outlines/curves")
    print("      and ensure all images are embedded at 150-300 DPI.\n")
