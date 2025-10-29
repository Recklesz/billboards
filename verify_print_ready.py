#!/usr/bin/env python3
"""
Pre-flight verification script for print-ready PDFs.
Checks compliance with requirements.md specifications.
"""

import sys
from pathlib import Path
try:
    import PyPDF2
    import pdfplumber
    from PIL import Image
except ImportError:
    print("⚠️  Missing dependencies. Install with:")
    print("   pip install PyPDF2 pdfplumber Pillow")
    sys.exit(1)


def check_text_outlined(pdf_path):
    """Verify text has been converted to paths (not extractable)."""
    print("\n📝 Checking text conversion...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ''
            text_length = len(text.strip())
            
            if text_length == 0:
                print("   ✅ Text converted to paths (no extractable text)")
                return True
            else:
                print(f"   ❌ FAIL: Found {text_length} characters of extractable text")
                print(f"   Sample: {text[:100]}")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not verify text: {e}")
        return None


def check_fonts_embedded(pdf_path):
    """Check if any fonts are still embedded (should be none after outlining)."""
    print("\n🔤 Checking font embedding...")
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            # Check for font references in the PDF
            fonts_found = []
            for page in pdf.pages:
                if '/Font' in page.get('/Resources', {}):
                    fonts = page['/Resources']['/Font']
                    fonts_found.extend(fonts.keys())
            
            if not fonts_found:
                print("   ✅ No fonts embedded (text properly outlined)")
                return True
            else:
                print(f"   ⚠️  Found font references: {fonts_found}")
                print("   (May be acceptable if text is still outlined)")
                return None
    except Exception as e:
        print(f"   ⚠️  Could not check fonts: {e}")
        return None


def check_pdf_metadata(pdf_path):
    """Extract and display PDF metadata."""
    print("\n📋 PDF Metadata:")
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            # Page count
            print(f"   Pages: {len(pdf.pages)}")
            
            # Page size (in points, 1 point = 1/72 inch)
            page = pdf.pages[0]
            box = page.mediabox
            width_pt = float(box.width)
            height_pt = float(box.height)
            width_mm = width_pt * 25.4 / 72
            height_mm = height_pt * 25.4 / 72
            
            print(f"   Page size: {width_mm:.1f} × {height_mm:.1f} mm")
            print(f"              ({width_pt:.1f} × {height_pt:.1f} pt)")
            
            # Check if size matches expected dimensions
            if "Backwall" in str(pdf_path):
                expected = (1000 + 10, 2170 + 10)  # 100cm + bleed
                tolerance = 5
                if abs(width_mm - expected[0]) < tolerance and abs(height_mm - expected[1]) < tolerance:
                    print(f"   ✅ Dimensions match backwall spec (100×217cm + 5mm bleed)")
                else:
                    print(f"   ⚠️  Expected ~{expected[0]}×{expected[1]}mm")
            elif "Counter" in str(pdf_path):
                expected = (300 + 10, 800 + 10)  # 30cm + bleed
                tolerance = 5
                if abs(width_mm - expected[0]) < tolerance and abs(height_mm - expected[1]) < tolerance:
                    print(f"   ✅ Dimensions match counter spec (30×80cm + 5mm bleed)")
                else:
                    print(f"   ⚠️  Expected ~{expected[0]}×{expected[1]}mm")
            
            # Metadata
            if pdf.metadata:
                print(f"   Creator: {pdf.metadata.get('/Creator', 'N/A')}")
                print(f"   Producer: {pdf.metadata.get('/Producer', 'N/A')}")
            
            return True
    except Exception as e:
        print(f"   ❌ Could not read metadata: {e}")
        return False


def check_color_space(pdf_path):
    """Check color space information."""
    print("\n🎨 Color Space Check:")
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            page = pdf.pages[0]
            
            # Look for color space info
            resources = page.get('/Resources', {})
            colorspace = resources.get('/ColorSpace', {})
            
            if colorspace:
                print(f"   Color spaces found: {list(colorspace.keys())}")
            else:
                print("   ℹ️  No explicit color space metadata")
            
            print("   ⚠️  Manual verification recommended:")
            print("      - Open in Adobe Acrobat Pro")
            print("      - Check Output Preview (Shift+Cmd+Y)")
            print("      - Verify CMYK mode")
            
            return None
    except Exception as e:
        print(f"   ⚠️  Could not check color space: {e}")
        return None


def check_file_integrity(pdf_path):
    """Basic file integrity checks."""
    print("\n🔍 File Integrity:")
    try:
        file_size = Path(pdf_path).stat().st_size
        print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        if file_size < 1000:
            print("   ❌ File suspiciously small")
            return False
        
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            if pdf.is_encrypted:
                print("   ⚠️  PDF is encrypted")
                return None
            
            # Try to read first page
            page = pdf.pages[0]
            _ = page.mediabox
            
            print("   ✅ PDF structure valid")
            return True
            
    except Exception as e:
        print(f"   ❌ File integrity issue: {e}")
        return False


def check_images_embedded(pdf_path):
    """Check for embedded images."""
    print("\n🖼️  Image Embedding:")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            images = page.images
            
            if images:
                print(f"   Found {len(images)} image(s)")
                for i, img in enumerate(images[:3], 1):  # Show first 3
                    print(f"   Image {i}: {img.get('width', '?')}×{img.get('height', '?')}px")
                print("   ℹ️  Images appear to be embedded")
                return True
            else:
                print("   ℹ️  No images detected (or fully converted to vectors)")
                return True
    except Exception as e:
        print(f"   ⚠️  Could not check images: {e}")
        return None


def print_manual_checklist():
    """Print manual verification steps."""
    print("\n" + "="*60)
    print("📋 MANUAL VERIFICATION CHECKLIST")
    print("="*60)
    print("""
1. ✓ Open PDF in Adobe Acrobat Pro or professional PDF viewer
   
2. ✓ Try to select text with cursor
   → Should NOT be able to select any text
   → Text should behave like vector graphics
   
3. ✓ Check Output Preview (Acrobat: Shift+Cmd+Y / Shift+Ctrl+Y)
   → Verify color mode is CMYK
   → Check for RGB or spot colors (should be none)
   → Verify rich black uses C:60 M:40 Y:40 K:100
   
4. ✓ Check crop marks and bleed
   → Crop marks visible at corners
   → Content extends to bleed edge (5mm beyond trim)
   → No critical content in bleed area
   
5. ✓ Verify safe areas (requirements.md)
   → 50mm margin from trim on all sides
   → Backwall: 30×80cm no-text zone at bottom-right
   
6. ✓ Check image resolution
   → All images should be 150-300 DPI minimum
   → No pixelation when zoomed to 100%
   
7. ✓ Font check
   → Document Properties → Fonts
   → Should show no embedded fonts (all outlined)
   
8. ✓ Preflight check (if available)
   → Run printer's preflight profile
   → Resolve any warnings/errors
   
9. ✓ Print test
   → Print to office printer at reduced scale
   → Verify colors, layout, and text clarity
   
10. ✓ Final review with requirements.md
    → Cross-reference all specifications
    → Confirm compliance before submission
""")


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_print_ready.py <pdf_path>")
        print("\nExample:")
        print("  python verify_print_ready.py output/Backwall_100x217cm_bleed5mm_CMYK_PRINT_READY.pdf")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    print("="*60)
    print(f"🔍 PRINT-READY PDF VERIFICATION")
    print("="*60)
    print(f"File: {pdf_path.name}")
    print(f"Path: {pdf_path}")
    
    # Run all checks
    results = []
    results.append(("File Integrity", check_file_integrity(pdf_path)))
    results.append(("PDF Metadata", check_pdf_metadata(pdf_path)))
    results.append(("Text Outlined", check_text_outlined(pdf_path)))
    results.append(("Fonts Embedded", check_fonts_embedded(pdf_path)))
    results.append(("Images Embedded", check_images_embedded(pdf_path)))
    results.append(("Color Space", check_color_space(pdf_path)))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    warnings = sum(1 for _, r in results if r is None)
    
    for check, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️  MANUAL"
        print(f"{status:12} {check}")
    
    print(f"\nPassed: {passed} | Failed: {failed} | Manual: {warnings}")
    
    if failed > 0:
        print("\n❌ PDF has issues that must be resolved before printing")
        print_manual_checklist()
        sys.exit(1)
    elif warnings > 0:
        print("\n⚠️  PDF requires manual verification (see checklist below)")
        print_manual_checklist()
        sys.exit(0)
    else:
        print("\n✅ All automated checks passed!")
        print_manual_checklist()
        sys.exit(0)


if __name__ == "__main__":
    main()
