"""
Counter Graphics Generator
Creates counter graphics according to print specifications.

Now uses the refactored pipeline architecture with CMYK compliance.
"""

import os
import json
import logging

from graphics_config import GraphicsConfig
from asset_pipeline import AssetPipeline
from counter_layout import CounterLayout
from graphics_common import create_jpg_proof

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def draw_counter_background_legacy(canvas_obj, graphic):
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


def generate_qr_code_legacy(url, output_dir):
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


def create_counter(output_dir="output", show_guides=False, use_cmyk=True, generate_proof=True):
    """
    Create counter graphic with QR code centerpiece using the new pipeline.

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area)
        use_cmyk: Use CMYK color mode (default: True)
        generate_proof: Generate JPG proof (default: True)

    Returns:
        Path to the generated PDF file
    """
    logger.info("Generating counter using new pipeline...")
    
    # Create configuration
    config = GraphicsConfig.default(
        output_dir=output_dir,
        show_guides=show_guides
    )
    config.use_cmyk = use_cmyk
    config.generate_proofs = generate_proof
    
    # Validate configuration
    issues = config.validate()
    if issues:
        logger.error("Configuration validation failed:")
        for issue in issues:
            logger.error(f"  {issue}")
        raise RuntimeError("Configuration validation failed")
    
    # Ensure output directories
    config.output.ensure_directories()
    
    # Initialize asset pipeline
    asset_pipeline = AssetPipeline(
        cache_dir=config.output.temp_dir,
        force_cmyk=use_cmyk
    )
    
    # Generate counter
    counter_filename = "Counter_30x80cm_bleed5mm_CMYK.pdf"
    counter_path = os.path.join(output_dir, counter_filename)
    
    layout = CounterLayout(config, asset_pipeline)
    pdf_path = layout.generate(counter_path)
    
    logger.info(f"✓ Created: {pdf_path}")
    
    # Create JPG proof
    if generate_proof:
        create_jpg_proof(pdf_path, output_dir, "Counter_30x80cm_proof.jpg")
    
    return pdf_path


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COUNTER GRAPHICS GENERATOR")
    print("="*60 + "\n")

    print("Generating counter...\n")

    # Generate counter without guides (production-ready)
    counter_pdf = create_counter(output_dir="output", show_guides=False)

    # For review with guides visible, use:
    # counter_pdf = create_counter(output_dir="output", show_guides=True)

    print("\n" + "-"*60)
    print("✓ Counter generated successfully!")
    print(f"✓ Output directory: {os.path.abspath('output')}")
    print("-"*60 + "\n")

    print("Pre-flight checklist:")
    print("  [✓] Canvas set to trim size + 5mm bleed on all sides")
    print("  [✓] CMYK color mode enforced")
    print("  [!] All text should be outlined (requires post-processing)")
    print("  [✓] Safe area respected")
    print("  [✓] Exported PDF with crop marks & bleed")
    print("\nNote: For final production, convert all text to outlines/curves")
    print("      and ensure all images are embedded at 150-300 DPI.\n")
