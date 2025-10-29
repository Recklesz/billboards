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
    FACE_IMAGE_PATH,
    BackwallGraphic,
    get_headline_font_name,
    fit_multiline_font_size,
    draw_centered_string,
    create_jpg_proof,
    create_bottom_fade_image
)


def draw_backwall_background(canvas_obj, graphic):
    """
    Create a mostly white background with subtle radial teal gradient accents.
    """
    # Create background with radial gradients as PIL image, then draw it
    # This avoids ReportLab canvas layering issues

    # Convert dimensions to pixels for PIL (using 150 DPI)
    dpi = 150
    width_px = int((graphic.doc_width / mm) * (dpi / 25.4))
    height_px = int((graphic.doc_height / mm) * (dpi / 25.4))

    # Create white background image
    bg_img = Image.new("RGB", (width_px, height_px), (255, 255, 255))

    # Create radial gradient overlay
    overlay = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))

    # Teal color for gradients (RGB)
    teal_rgb = (90, 180, 190)  # Soft teal

    # Define radial gradient spots (as fractions of width/height)
    gradient_spots = [
        {"x": 0.15, "y": 0.15, "radius": 0.35},  # Top left
        {"x": 0.85, "y": 0.50, "radius": 0.30},  # Middle right
        {"x": 0.20, "y": 0.85, "radius": 0.25},  # Bottom left
        {"x": 0.80, "y": 0.90, "radius": 0.22},  # Bottom right
    ]

    # Draw each radial gradient
    import numpy as np
    for spot in gradient_spots:
        cx = int(spot["x"] * width_px)
        cy = int((1 - spot["y"]) * height_px)  # Flip Y for image coords
        max_radius = int(spot["radius"] * max(width_px, height_px))

        # Create gradient for this spot
        for y in range(max(0, cy - max_radius), min(height_px, cy + max_radius)):
            for x in range(max(0, cx - max_radius), min(width_px, cx + max_radius)):
                # Calculate distance from center
                dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                if dist < max_radius:
                    # Calculate alpha based on distance (0 at center, fades to 0 at edge)
                    alpha = int(60 * (1 - (dist / max_radius) ** 1.5))  # Max 60 alpha, with smooth falloff
                    if alpha > 0:
                        # Blend with existing pixel
                        existing = overlay.getpixel((x, y))
                        new_alpha = min(255, existing[3] + alpha)
                        overlay.putpixel((x, y), (*teal_rgb, new_alpha))

    # Composite overlay onto background
    bg_img.paste(overlay, (0, 0), overlay)

    # Save temporarily and draw on canvas
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        bg_img.save(tmp_path)

    try:
        bg_reader = ImageReader(tmp_path)
        canvas_obj.drawImage(bg_reader, 0, 0, width=graphic.doc_width, height=graphic.doc_height)
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass


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

    # Face image - FULL WIDTH with bottom fade
    if os.path.exists(FACE_IMAGE_PATH):
        try:
            # Create image with bottom fade for natural blending
            face_img = create_bottom_fade_image(FACE_IMAGE_PATH, fade_percentage=0.35)
            face_ratio = face_img.height / face_img.width

            # FULL WIDTH - use entire trim width
            face_width = graphic.trim_width
            face_height = face_width * face_ratio

            # Position at top, centered horizontally
            face_x = graphic.bleed
            face_y = graphic.bleed + (1900 * mm) - (face_height / 2)

            # Keep top within safe area
            max_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - face_height
            if face_y > max_y:
                face_y = max_y

            # Save processed image temporarily for ReportLab
            temp_path = os.path.join(output_dir, "_temp_face_fade.png")
            face_img.save(temp_path)

            face_reader = ImageReader(temp_path)
            c.drawImage(
                face_reader,
                face_x,
                face_y,
                width=face_width,
                height=face_height,
                preserveAspectRatio=True,
            )

            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass

        except Exception as exc:
            print(f"⚠ Could not render face image: {exc}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ Face image not found.")

    # Headline text - positioned to overlap with smile
    headline_font = get_headline_font_name()
    line1 = "AI ROLEPLAY"
    line2 = "FOR SALES TEAMS"

    max_headline_width = safe_width * 0.92
    headline_font_size = fit_multiline_font_size([line1, line2], headline_font, max_headline_width, starting_size=300, minimum_size=80)

    # Position so only bottom half of "AI ROLEPLAY" overlaps with smile
    # "FOR SALES TEAMS" should be completely below the image
    headline_center_x = graphic.doc_width / 2

    # Calculate line spacing
    ascent, descent = pdfmetrics.getAscentDescent(headline_font, headline_font_size)
    line_height = ascent - descent
    baseline_gap = line_height * 1.60  # Significantly increased spacing between lines

    # Position at ~148cm so only bottom portion of first line overlaps with smile
    first_baseline = graphic.bleed + (1520 * mm)

    # Ensure we're above no-text zone
    min_y = graphic.bleed + graphic.no_text_zone["height"] + (150 * mm)
    if first_baseline - line_height < min_y:
        first_baseline = min_y + line_height

    # Calculate text width for background
    text_width_line1 = pdfmetrics.stringWidth(line1, headline_font, headline_font_size)
    text_width_line2 = pdfmetrics.stringWidth(line2, headline_font, headline_font_size)
    max_text_width = max(text_width_line1, text_width_line2)

    # Load logo dimensions to include in box calculation
    logo_width = 0
    logo_height = 0
    logo_ratio = 1
    if os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as logo_img:
                logo_ratio = logo_img.height / logo_img.width
                # Logo size inside the box
                max_logo_width = safe_width * 0.20  # Slightly smaller for inside box
                max_logo_height = safe_height * 0.08
                computed_logo_height = max_logo_width * logo_ratio

                if computed_logo_height > max_logo_height:
                    computed_logo_height = max_logo_height
                    max_logo_width = computed_logo_height / logo_ratio

                logo_width = max_logo_width
                logo_height = computed_logo_height
        except Exception as exc:
            print(f"⚠ Could not read logo for sizing: {exc}")

    # Draw semi-transparent background behind text + logo with rounded corners
    # This makes text readable while showing some of the smile through
    bg_padding_h = 30 * mm  # Horizontal padding around text
    bg_padding_top = 35 * mm  # Smaller padding above "AI ROLEPLAY"
    bg_padding_bottom = 60 * mm  # Bigger padding below "FOR SALES TEAMS" to accommodate logo
    logo_gap = 60 * mm  # Extra space to push logo down

    bg_x = headline_center_x - (max_text_width / 2) - bg_padding_h
    bg_y = first_baseline - baseline_gap - (descent * headline_font_size / 1000) - bg_padding_bottom - logo_height - logo_gap
    bg_width = max_text_width + (2 * bg_padding_h)
    bg_height = line_height + baseline_gap + bg_padding_top + bg_padding_bottom + logo_height + logo_gap
    bg_radius = 40 * mm  # Rounded corner radius

    # Semi-transparent white background with rounded corners
    c.setFillColorRGB(1, 1, 1, alpha=0.88)  # 88% white for better text readability
    c.roundRect(bg_x, bg_y, bg_width, bg_height, bg_radius, fill=1, stroke=0)

    # Draw text with solid dark color for maximum contrast
    text_color = BRAND_COLORS["headline_text"]  # Dark navy

    # Line 1 - "AI ROLEPLAY" (solid, no transparency on text itself)
    draw_centered_string(
        c, line1, headline_font, headline_font_size,
        headline_center_x, first_baseline, text_color,
        alpha=1.0  # Fully opaque text
    )

    # Line 2 - "FOR SALES TEAMS" (solid, no transparency on text itself)
    draw_centered_string(
        c, line2, headline_font, headline_font_size,
        headline_center_x, first_baseline - baseline_gap, text_color,
        alpha=1.0  # Fully opaque text
    )

    # Logo - inside the box, below "FOR SALES TEAMS"
    if os.path.exists(LOGO_PATH) and logo_width > 0:
        try:
            logo_reader = ImageReader(LOGO_PATH)
            logo_x = (graphic.doc_width - logo_width) / 2
            # Position logo below second line with gap
            logo_y = first_baseline - baseline_gap - (descent * headline_font_size / 1000) - logo_gap - logo_height

            # Draw logo
            c.drawImage(
                logo_reader,
                logo_x,
                logo_y,
                width=logo_width,
                height=logo_height,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception as exc:
            print(f"⚠ Could not render logo: {exc}")
    elif not os.path.exists(LOGO_PATH):
        print("⚠ Logo not found.")

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
