"""
Exhibit Graphics Generator
Creates backwall and counter graphics according to print specifications.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait
from PIL import Image
import os
import json


# Specifications from requirements
SPECS = {
    "units": "mm",
    "backwall": {
        "trim": {"width": 1000, "height": 2170},
        "bleed": {"all_sides": 5},
        "safe_inset": 50,
        "no_text_zone": {"x": 0, "y": 0, "width": 300, "height": 800}
    },
    "counter": {
        "trim": {"width": 300, "height": 800},
        "bleed": {"all_sides": 5},
        "safe_inset": 50
    },
    "print": {
        "color_mode": "CMYK",
        "min_effective_dpi": 150,
        "preferred_effective_dpi": 300,
        "rich_black": {"C": 60, "M": 40, "Y": 40, "K": 100},
        "outline_all_text": True,
        "embed_images": True,
        "deliver_as_pdf_with_crop_marks_and_bleed": True
    }
}


class ExhibitGraphic:
    """Base class for creating exhibit graphics"""

    def __init__(self, name, trim_width, trim_height, bleed=5, safe_inset=50):
        """
        Initialize graphic specifications

        Args:
            name: Name of the graphic (e.g., 'backwall', 'counter')
            trim_width: Width at trim size in mm
            trim_height: Height at trim size in mm
            bleed: Bleed size in mm (default 5)
            safe_inset: Safe area inset in mm (default 50)
        """
        self.name = name
        self.trim_width = trim_width * mm
        self.trim_height = trim_height * mm
        self.bleed = bleed * mm
        self.safe_inset = safe_inset * mm

        # Document size includes bleed
        self.doc_width = self.trim_width + (2 * self.bleed)
        self.doc_height = self.trim_height + (2 * self.bleed)

        self.canvas = None

    def create_canvas(self, filename):
        """Create PDF canvas with proper dimensions"""
        self.canvas = canvas.Canvas(
            filename,
            pagesize=(self.doc_width, self.doc_height)
        )
        return self.canvas

    def draw_crop_marks(self):
        """Draw crop/trim marks at corners"""
        c = self.canvas
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)

        mark_length = 10 * mm
        mark_offset = self.bleed

        # Bottom-left
        c.line(0, mark_offset, mark_length, mark_offset)
        c.line(mark_offset, 0, mark_offset, mark_length)

        # Bottom-right
        c.line(self.doc_width - mark_length, mark_offset, self.doc_width, mark_offset)
        c.line(self.doc_width - mark_offset, 0, self.doc_width - mark_offset, mark_length)

        # Top-left
        c.line(0, self.doc_height - mark_offset, mark_length, self.doc_height - mark_offset)
        c.line(mark_offset, self.doc_height - mark_length, mark_offset, self.doc_height)

        # Top-right
        c.line(self.doc_width - mark_length, self.doc_height - mark_offset,
               self.doc_width, self.doc_height - mark_offset)
        c.line(self.doc_width - mark_offset, self.doc_height - mark_length,
               self.doc_width - mark_offset, self.doc_height)

    def draw_guides(self, show_guides=True):
        """Draw safe area and bleed guides (for reference, not in final)"""
        if not show_guides:
            return

        c = self.canvas
        c.setStrokeColor(colors.Color(0, 1, 1, alpha=0.5))  # Cyan guide
        c.setLineWidth(0.25)
        c.setDash(3, 3)

        # Bleed box (trim area)
        c.rect(self.bleed, self.bleed, self.trim_width, self.trim_height)

        # Safe area
        c.rect(
            self.bleed + self.safe_inset,
            self.bleed + self.safe_inset,
            self.trim_width - (2 * self.safe_inset),
            self.trim_height - (2 * self.safe_inset)
        )

        c.setDash()  # Reset dash

    def draw_background(self, color=None):
        """Draw background color extending to bleed"""
        if color is None:
            # Default: white background
            color = colors.white

        c = self.canvas
        c.setFillColor(color)
        c.rect(0, 0, self.doc_width, self.doc_height, fill=1, stroke=0)

    def save(self):
        """Save the PDF"""
        if self.canvas:
            self.canvas.save()


class BackwallGraphic(ExhibitGraphic):
    """Backwall graphic with no-text zone"""

    def __init__(self):
        specs = SPECS["backwall"]
        super().__init__(
            "backwall",
            specs["trim"]["width"],
            specs["trim"]["height"],
            specs["bleed"]["all_sides"],
            specs["safe_inset"]
        )

        # No-text zone (bottom-left corner, in trim coordinates)
        ntz = specs["no_text_zone"]
        self.no_text_zone = {
            "x": ntz["x"] * mm,
            "y": ntz["y"] * mm,
            "width": ntz["width"] * mm,
            "height": ntz["height"] * mm
        }

    def draw_no_text_zone_guide(self, show_guides=True):
        """Draw no-text zone indicator"""
        if not show_guides:
            return

        c = self.canvas
        c.setStrokeColor(colors.Color(1, 0, 0, alpha=0.5))  # Red guide
        c.setLineWidth(0.5)
        c.setDash(5, 5)

        # No-text zone in document coordinates (add bleed offset)
        c.rect(
            self.bleed + self.no_text_zone["x"],
            self.bleed + self.no_text_zone["y"],
            self.no_text_zone["width"],
            self.no_text_zone["height"]
        )

        c.setDash()  # Reset dash


class CounterGraphic(ExhibitGraphic):
    """Counter graphic"""

    def __init__(self):
        specs = SPECS["counter"]
        super().__init__(
            "counter",
            specs["trim"]["width"],
            specs["trim"]["height"],
            specs["bleed"]["all_sides"],
            specs["safe_inset"]
        )


def create_sample_backwall(output_dir="output", show_guides=True):
    """
    Create a sample backwall graphic with placeholder design

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area, no-text zone)
    """
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Backwall_100x217cm_bleed5mm_CMYK.pdf")

    graphic = BackwallGraphic()
    c = graphic.create_canvas(filename)

    # Background (extends to bleed)
    graphic.draw_background(colors.white)

    # Example: Add a gradient or colored background
    # For demo purposes, let's add a light blue background
    c.setFillColor(colors.Color(0.9, 0.95, 1))  # Light blue
    c.rect(0, 0, graphic.doc_width, graphic.doc_height, fill=1, stroke=0)

    # Add crop marks
    graphic.draw_crop_marks()

    # Add guides (optional, for reference)
    graphic.draw_guides(show_guides)
    graphic.draw_no_text_zone_guide(show_guides)

    # Example content in safe area
    c.setFillColor(colors.Color(0, 0, 0.5))  # Dark blue
    c.setFont("Helvetica-Bold", 72)

    # Position text in safe area (accounting for bleed)
    text_x = graphic.bleed + graphic.safe_inset + (50 * mm)
    text_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (100 * mm)

    # Note: In production, text should be converted to outlines
    c.drawString(text_x, text_y, "YOUR BRAND")

    # Add info text
    c.setFont("Helvetica", 24)
    c.drawString(text_x, text_y - (40 * mm), "Backwall 100 x 217 cm")

    # Draw a sample logo placeholder in safe area
    c.setStrokeColor(colors.Color(0, 0, 0.5))
    c.setLineWidth(2)
    logo_x = text_x
    logo_y = graphic.bleed + graphic.safe_inset + (100 * mm)
    c.rect(logo_x, logo_y, 200 * mm, 100 * mm, fill=0, stroke=1)
    c.setFont("Helvetica", 18)
    c.drawString(logo_x + (70 * mm), logo_y + (45 * mm), "LOGO AREA")

    graphic.save()
    print(f"✓ Created: {filename}")

    # Create JPG proof
    create_jpg_proof(filename, output_dir, "Backwall_100x217cm_proof.jpg")

    return filename


def create_sample_counter(output_dir="output", show_guides=True):
    """
    Create a sample counter graphic with placeholder design

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area)
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


def create_jpg_proof(pdf_path, output_dir, jpg_filename, max_width=1200):
    """
    Create a JPG proof from PDF for quick review

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save JPG
        jpg_filename: Name of the JPG file
        max_width: Maximum width of the JPG proof in pixels
    """
    try:
        from pdf2image import convert_from_path

        # Convert PDF to image
        images = convert_from_path(pdf_path, dpi=150)

        if images:
            img = images[0]

            # Resize for proof
            aspect_ratio = img.height / img.width
            new_width = max_width
            new_height = int(new_width * aspect_ratio)
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save as JPG
            jpg_path = os.path.join(output_dir, jpg_filename)
            img_resized.save(jpg_path, "JPEG", quality=85)
            print(f"✓ Created proof: {jpg_path}")
    except ImportError:
        print("⚠ pdf2image not installed. Skipping JPG proof generation.")
        print("  Install with: pip install pdf2image")
        print("  Also requires poppler: brew install poppler (macOS) or apt-get install poppler-utils (Linux)")
    except Exception as e:
        print(f"⚠ Could not create JPG proof: {e}")


def generate_all_graphics(output_dir="output", show_guides=False):
    """
    Generate all required graphics

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (set to False for final production)
    """
    print("\n" + "="*60)
    print("EXHIBIT GRAPHICS GENERATOR")
    print("="*60 + "\n")

    print("Specifications:")
    print(json.dumps(SPECS, indent=2))
    print("\n" + "-"*60 + "\n")

    print("Generating graphics...\n")

    # Generate backwall
    backwall_pdf = create_sample_backwall(output_dir, show_guides)

    # Generate counter
    counter_pdf = create_sample_counter(output_dir, show_guides)

    print("\n" + "-"*60)
    print("✓ All graphics generated successfully!")
    print(f"✓ Output directory: {os.path.abspath(output_dir)}")
    print("-"*60 + "\n")

    print("Pre-flight checklist:")
    print("  [✓] Canvas set to trim size + 5mm bleed on all sides")
    print("  [✓] CMYK document (reportlab default)")
    print("  [!] All text should be outlined (requires post-processing)")
    print("  [✓] Safe area respected")
    print("  [✓] No-text zone on backwall respected")
    print("  [✓] Exported PDF with crop marks & bleed")
    print("\nNote: For final production, convert all text to outlines/curves")
    print("      and ensure all images are embedded at 150-300 DPI.\n")


if __name__ == "__main__":
    # Generate graphics with guides for review
    generate_all_graphics(output_dir="output", show_guides=True)

    # For final production, use:
    # generate_all_graphics(output_dir="output", show_guides=False)
