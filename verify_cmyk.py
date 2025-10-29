#!/usr/bin/env python3
"""
CMYK Verification Script

Verifies that PDFs and intermediate assets use CMYK color mode.
"""

import os
import sys
from PIL import Image
from pathlib import Path


def verify_image_cmyk(image_path: str) -> tuple[bool, str]:
    """
    Verify an image is in CMYK mode.

    Returns:
        (is_cmyk, details)
    """
    try:
        img = Image.open(image_path)
        mode = img.mode
        size = img.size

        if mode == 'CMYK':
            return True, f"✓ CMYK mode, size: {size[0]}x{size[1]}"
        else:
            return False, f"✗ {mode} mode (expected CMYK), size: {size[0]}x{size[1]}"
    except Exception as e:
        return False, f"✗ Error: {e}"


def verify_pdf_images(pdf_path: str) -> tuple[bool, list[str]]:
    """
    Extract and verify images from PDF using reportlab.

    Returns:
        (all_cmyk, details)
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import fitz  # PyMuPDF

        details = []
        pdf_doc = fitz.open(pdf_path)

        all_cmyk = True
        image_count = 0

        for page_num, page in enumerate(pdf_doc, 1):
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                image_count += 1
                xref = img_info[0]

                # Extract image
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                colorspace = base_image.get("colorspace", "unknown")

                # Try to determine color space
                if colorspace in [8, "DeviceCMYK", "/DeviceCMYK"]:
                    details.append(f"  Image {image_count} (page {page_num}): ✓ CMYK")
                else:
                    details.append(f"  Image {image_count} (page {page_num}): ✗ {colorspace} (not CMYK)")
                    all_cmyk = False

        pdf_doc.close()

        if image_count == 0:
            return True, ["  No images found in PDF"]

        return all_cmyk, details

    except ImportError:
        return None, ["  ⚠ PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF"]
    except Exception as e:
        return None, [f"  ✗ Error analyzing PDF: {e}"]


def verify_temp_assets(temp_dir: str = "output/temp") -> tuple[int, int, list[str]]:
    """
    Verify intermediate assets in temp directory.

    Returns:
        (cmyk_count, total_count, details)
    """
    if not os.path.exists(temp_dir):
        return 0, 0, ["  Temp directory not found"]

    details = []
    cmyk_count = 0
    total_count = 0

    # Check common image formats
    for ext in ['*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg']:
        for img_path in Path(temp_dir).glob(ext):
            total_count += 1
            is_cmyk, msg = verify_image_cmyk(str(img_path))

            if is_cmyk:
                cmyk_count += 1
                details.append(f"  {img_path.name}: {msg}")
            else:
                details.append(f"  {img_path.name}: {msg}")

    return cmyk_count, total_count, details


def main():
    """Run CMYK verification on generated assets."""
    print("=" * 60)
    print("CMYK COLOR MODE VERIFICATION")
    print("=" * 60)
    print()

    # Check backwall PDF
    backwall_pdf = "output/Backwall_100x217cm_bleed5mm_CMYK.pdf"
    if os.path.exists(backwall_pdf):
        print(f"Checking PDF: {backwall_pdf}")
        all_cmyk, details = verify_pdf_images(backwall_pdf)

        if all_cmyk is None:
            print("  ⚠ Could not verify PDF images")
        elif all_cmyk:
            print("  ✓ All images in PDF use CMYK color space")
        else:
            print("  ✗ Some images in PDF are NOT CMYK")

        for detail in details:
            print(detail)
        print()
    else:
        print(f"✗ Backwall PDF not found: {backwall_pdf}")
        print()

    # Check counter PDF
    counter_pdf = "output/Counter_30x80cm_bleed5mm_CMYK.pdf"
    if os.path.exists(counter_pdf):
        print(f"Checking PDF: {counter_pdf}")
        all_cmyk, details = verify_pdf_images(counter_pdf)

        if all_cmyk is None:
            print("  ⚠ Could not verify PDF images")
        elif all_cmyk:
            print("  ✓ All images in PDF use CMYK color space")
        else:
            print("  ✗ Some images in PDF are NOT CMYK")

        for detail in details:
            print(detail)
        print()
    else:
        print(f"⚠ Counter PDF not found: {counter_pdf}")
        print()

    # Check temp assets
    print("Checking intermediate assets (output/temp/):")
    cmyk_count, total_count, details = verify_temp_assets()

    if total_count == 0:
        print("  No intermediate assets found")
    else:
        print(f"  Found {cmyk_count}/{total_count} CMYK images")

        for detail in details[:10]:  # Show first 10
            print(detail)

        if len(details) > 10:
            print(f"  ... and {len(details) - 10} more")

    print()
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

    # Return exit code
    if total_count > 0 and cmyk_count < total_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
