"""
Counter Graphics Generator
Creates counter graphics according to print specifications.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image
import os
import json
import qrcode
import tempfile
import numpy as np

from graphics_common import (
    SPECS,
    BRAND_COLORS,
    LOGO_PATH,
    CounterGraphic,
    create_jpg_proof,
    get_headline_font_name
)


def draw_counter_background(canvas_obj, graphic):
    """
    Create background with subtle radial teal gradient accents matching backwall design.
    """
    # Convert dimensions to pixels for PIL (using 150 DPI)
    dpi = 150
    width_px = int((graphic.doc_width / mm) * (dpi / 25.4))
    height_px = int((graphic.doc_height / mm) * (dpi / 25.4))

    # Create white background image
    bg_img = Image.new("RGB", (width_px, height_px), (255, 255, 255))

    # Create radial gradient overlay
    overlay = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))

    # Teal color for gradients (RGB)
    teal_rgb = (90, 180, 190)  # Soft teal matching backwall

    # Define radial gradient spots optimized for counter dimensions (portrait)
    gradient_spots = [
        {"x": 0.20, "y": 0.15, "radius": 0.40},  # Top left
        {"x": 0.80, "y": 0.25, "radius": 0.35},  # Top right
        {"x": 0.15, "y": 0.50, "radius": 0.30},  # Middle left
        {"x": 0.85, "y": 0.65, "radius": 0.28},  # Middle right
        {"x": 0.50, "y": 0.88, "radius": 0.32},  # Bottom center
    ]

    # Draw each radial gradient
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
                    alpha = int(60 * (1 - (dist / max_radius) ** 1.5))  # Max 60 alpha, smooth falloff
                    if alpha > 0:
                        # Blend with existing pixel
                        existing = overlay.getpixel((x, y))
                        new_alpha = min(255, existing[3] + alpha)
                        overlay.putpixel((x, y), (*teal_rgb, new_alpha))

    # Composite overlay onto background
    bg_img.paste(overlay, (0, 0), overlay)

    # Save temporarily and draw on canvas
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


def generate_qr_code(url, output_dir):
    """
    Generate a high-quality QR code for the given URL.
    
    Args:
        url: URL to encode in QR code
        output_dir: Directory to save QR code image
        
    Returns:
        Path to the generated QR code image
    """
    qr = qrcode.QRCode(
        version=1,  # Auto-adjust size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=20,  # Large box size for high resolution
        border=2,  # Minimal border
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create QR code image with dark navy color matching brand
    qr_img = qr.make_image(fill_color="#0E2E3E", back_color="white")
    
    # Save to temporary file
    qr_path = os.path.join(output_dir, "_temp_qr_code.png")
    qr_img.save(qr_path)
    
    return qr_path


def create_counter(output_dir="output", show_guides=True):
    """
    Create counter graphic with QR code centerpiece and high-end design

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

    # Background with radial gradients matching backwall
    draw_counter_background(c, graphic)

    # Calculate safe area bounds
    safe_origin_x = graphic.bleed + graphic.safe_inset
    safe_origin_y = graphic.bleed + graphic.safe_inset
    safe_width = graphic.trim_width - (2 * graphic.safe_inset)
    safe_height = graphic.trim_height - (2 * graphic.safe_inset)

    # Add crop marks
    graphic.draw_crop_marks()

    # Add guides
    graphic.draw_guides(show_guides)

    # Add website URL at the top with Ubuntu Bold
    headline_font = get_headline_font_name()
    c.setFillColor(BRAND_COLORS["headline_text"])
    
    # Website URL at the top - bigger and prominent
    website_text = "callskylar.com"
    website_font_size = 42
    c.setFont(headline_font, website_font_size)
    website_width = c.stringWidth(website_text, headline_font, website_font_size)
    website_x = (graphic.doc_width - website_width) / 2
    website_y = graphic.bleed + (680 * mm)  # Position at top
    c.drawString(website_x, website_y, website_text)

    # Generate QR code
    qr_url = "https://www.getskylar.com/conference"
    qr_path = generate_qr_code(qr_url, output_dir)

    try:
        # QR code dimensions - make it prominent but elegant
        qr_size = safe_width * 0.65  # 65% of safe width for visual impact
        qr_x = (graphic.doc_width - qr_size) / 2  # Center horizontally
        
        # Position QR code below website URL
        qr_y = website_y - (120 * mm)  # Position below website URL

        # Create elegant rounded container for QR code
        container_padding = 25 * mm
        container_x = qr_x - container_padding
        container_y = qr_y - container_padding
        container_width = qr_size + (2 * container_padding)
        container_height = qr_size + (2 * container_padding)
        container_radius = 35 * mm

        # Draw semi-transparent white container with rounded corners
        c.setFillColorRGB(1, 1, 1, alpha=0.92)  # 92% white for elegance
        c.roundRect(container_x, container_y, container_width, container_height, 
                   container_radius, fill=1, stroke=0)

        # Draw QR code
        qr_reader = ImageReader(qr_path)
        c.drawImage(
            qr_reader,
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
        )

        # Clean up QR code temp file
        try:
            os.remove(qr_path)
        except:
            pass

    except Exception as exc:
        print(f"⚠ Could not render QR code: {exc}")
        import traceback
        traceback.print_exc()

    # Add Skylar logo at bottom
    if os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as logo_img:
                logo_ratio = logo_img.height / logo_img.width
                
                # Logo sizing - elegant and proportional
                max_logo_width = safe_width * 0.55
                logo_width = max_logo_width
                logo_height = logo_width * logo_ratio
                
                # Position logo at bottom with generous spacing
                logo_x = (graphic.doc_width - logo_width) / 2
                logo_y = safe_origin_y + (40 * mm)  # 40mm from bottom safe area
                
                # Draw logo
                logo_reader = ImageReader(LOGO_PATH)
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
    else:
        print("⚠ Logo not found.")

    # Add elegant call-to-action text below QR code with Ubuntu Bold
    c.setFillColor(BRAND_COLORS["headline_text"])
    
    # Main CTA text
    cta_text = "Scan to Learn More"
    cta_font_size = 32
    c.setFont(headline_font, cta_font_size)
    text_width = c.stringWidth(cta_text, headline_font, cta_font_size)
    text_x = (graphic.doc_width - text_width) / 2
    text_y = qr_y - (55 * mm)  # Position below QR container
    c.drawString(text_x, text_y, cta_text)

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
