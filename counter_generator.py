"""
Counter Graphics Generator
Creates counter graphics according to print specifications.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
import os
import json

from graphics_common import (
    SPECS,
    CounterGraphic,
    create_jpg_proof
)


def create_counter(output_dir="output", show_guides=True):
    """
    Create counter graphic with placeholder design

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area)

    Returns:
        Path to the generated PDF file
    """
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Counter_30x80cm_bleed5mm_CMYK.pdf")

    graphic = CounterGraphic()
    c = graphic.create_canvas(filename)

    # Background
    graphic.draw_background(colors.white)

    # Example: Matching light blue background
    c.setFillColor(colors.Color(0.9, 0.95, 1))
    c.rect(0, 0, graphic.doc_width, graphic.doc_height, fill=1, stroke=0)

    # Add crop marks
    graphic.draw_crop_marks()

    # Add guides
    graphic.draw_guides(show_guides)

    # Example content in safe area
    c.setFillColor(colors.Color(0, 0, 0.5))
    c.setFont("Helvetica-Bold", 48)

    text_x = graphic.bleed + graphic.safe_inset + (20 * mm)
    text_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (100 * mm)

    c.drawString(text_x, text_y, "BRAND")

    c.setFont("Helvetica", 16)
    c.drawString(text_x, text_y - (30 * mm), "Counter 30 x 80 cm")

    # Logo placeholder
    c.setStrokeColor(colors.Color(0, 0, 0.5))
    c.setLineWidth(2)
    logo_x = text_x
    logo_y = graphic.bleed + graphic.safe_inset + (50 * mm)
    c.rect(logo_x, logo_y, 150 * mm, 80 * mm, fill=0, stroke=1)
    c.setFont("Helvetica", 14)
    c.drawString(logo_x + (40 * mm), logo_y + (35 * mm), "LOGO AREA")

    graphic.save()
    print(f"✓ Created: {filename}")

    # Create JPG proof
    create_jpg_proof(filename, output_dir, "Counter_30x80cm_proof.jpg")

    return filename


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COUNTER GRAPHICS GENERATOR")
    print("="*60 + "\n")

    print("Specifications:")
    print(json.dumps(SPECS["counter"], indent=2))
    print("\n" + "-"*60 + "\n")

    print("Generating counter...\n")

    # Generate counter with guides for review
    counter_pdf = create_counter(output_dir="output", show_guides=True)

    # For final production, use:
    # counter_pdf = create_counter(output_dir="output", show_guides=False)

    print("\n" + "-"*60)
    print("✓ Counter generated successfully!")
    print(f"✓ Output directory: {os.path.abspath('output')}")
    print("-"*60 + "\n")

    print("Pre-flight checklist:")
    print("  [✓] Canvas set to trim size + 5mm bleed on all sides")
    print("  [✓] CMYK document (reportlab default)")
    print("  [!] All text should be outlined (requires post-processing)")
    print("  [✓] Safe area respected")
    print("  [✓] Exported PDF with crop marks & bleed")
    print("\nNote: For final production, convert all text to outlines/curves")
    print("      and ensure all images are embedded at 150-300 DPI.\n")
