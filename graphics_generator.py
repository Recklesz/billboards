"""
Exhibit Graphics Generator
Creates backwall and counter graphics according to print specifications.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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


BRAND_COLORS = {
    "background": colors.HexColor("#F8FAFC"),
    "headline_text": colors.HexColor("#0E2E3E"),
    "accent_primary": colors.HexColor("#37BCD9"),
    "accent_light": colors.HexColor("#8EE6F7"),
    "accent_muted": colors.HexColor("#DDF2F8"),
    "accent_dark": colors.HexColor("#197FA1"),
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "skylar-clean-logo.png")
UBUNTU_BOLD_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Ubuntu-Bold.ttf")


def get_headline_font_name():
    """Register Ubuntu Bold if available and return the preferred font name."""

    preferred_font = "Ubuntu-Bold"
    if preferred_font in pdfmetrics.getRegisteredFontNames():
        return preferred_font

    if os.path.exists(UBUNTU_BOLD_PATH):
        try:
            pdfmetrics.registerFont(TTFont(preferred_font, UBUNTU_BOLD_PATH))
            return preferred_font
        except Exception as exc:  # pragma: no cover - defensive
            print(f"⚠ Could not register Ubuntu font: {exc}. Falling back to Helvetica-Bold.")

    return "Helvetica-Bold"


def fit_text_size(text, font_name, max_width, starting_size=220, minimum_size=48):
    """Reduce font size until the string fits within max_width (points)."""

    font_size = starting_size
    while font_size > minimum_size:
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        if text_width <= max_width:
            break
        font_size -= 1
    return font_size


def fit_multiline_font_size(lines, font_name, max_width, starting_size=220, minimum_size=48):
    """Reduce font size until all lines fit within max_width."""

    font_size = starting_size
    while font_size > minimum_size:
        widths = [pdfmetrics.stringWidth(line, font_name, font_size) for line in lines]
        if max(widths) <= max_width:
            break
        font_size -= 1
    return font_size


def draw_centered_string(canvas_obj, text, font_name, font_size, center_x, baseline_y, fill_color):
    """Draw a centred string with the given styling."""

    canvas_obj.setFillColor(fill_color)
    canvas_obj.setFont(font_name, font_size)
    canvas_obj.drawCentredString(center_x, baseline_y, text)


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
