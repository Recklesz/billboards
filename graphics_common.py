"""
Common utilities and base classes for exhibit graphics generation.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import os


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
FACE_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "b7255f53-8368-4d30-bc18-698d6a1ac0df.png")
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


def create_bottom_fade_image(image_path, fade_percentage=0.35):
    """
    Create a version of the image with a gradient fade at the bottom
    so it blends naturally into the background.

    Args:
        image_path: Path to source image
        fade_percentage: What percentage of height should fade (0.0 to 1.0)

    Returns:
        PIL Image with bottom fade applied
    """
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size

    # Create alpha gradient mask
    mask = Image.new("L", (width, height), 255)

    # Calculate fade region
    fade_height = int(height * fade_percentage)
    fade_start = height - fade_height

    # Draw gradient in the fade region
    for y in range(fade_start, height):
        # Alpha goes from 255 (opaque) at fade_start to 0 (transparent) at bottom
        alpha = int(255 * (1 - (y - fade_start) / fade_height))
        for x in range(width):
            mask.putpixel((x, y), alpha)

    # Apply the mask to the alpha channel
    img.putalpha(mask)

    return img


def create_vignette_fade_image(image_path, edge_fade=0.25, bottom_fade=0.45, top_fade=0.05):
    """
    Create a high-end vignette effect with smooth edge fading for premium blending.

    Uses radial distance from edges with cubic easing for a sophisticated,
    magazine-quality fade that integrates naturally with gradient backgrounds.

    Args:
        image_path: Path to source image
        edge_fade: Percentage of width to fade on left/right sides (0.0 to 1.0)
        bottom_fade: Percentage of height to fade on bottom (0.0 to 1.0)
        top_fade: Percentage of height to fade on top (0.0 to 1.0)

    Returns:
        PIL Image with vignette fade applied
    """
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size

    # Create alpha mask
    mask = Image.new("L", (width, height), 255)

    # Calculate fade distances
    side_fade_dist = int(width * edge_fade)
    bottom_fade_dist = int(height * bottom_fade)
    top_fade_dist = int(height * top_fade)

    # Apply vignette with smooth cubic easing
    for y in range(height):
        for x in range(width):
            # Calculate distance from each edge
            # In image coords: y=0 is top, y=height-1 is bottom
            dist_left = x
            dist_right = width - x - 1
            dist_from_top = y  # Distance from top edge
            dist_from_bottom = height - y - 1  # Distance from bottom edge

            # Start with full opacity
            alpha = 1.0

            # Apply side fades (left and right) with cubic easing
            if dist_left < side_fade_dist:
                t = dist_left / side_fade_dist
                alpha *= t * t * (3 - 2 * t)  # Smoothstep easing
            if dist_right < side_fade_dist:
                t = dist_right / side_fade_dist
                alpha *= t * t * (3 - 2 * t)

            # Apply top fade (fade from top edge down)
            if dist_from_top < top_fade_dist:
                t = dist_from_top / top_fade_dist
                alpha *= t * t * (3 - 2 * t)

            # Apply bottom fade (fade from bottom edge up)
            if dist_from_bottom < bottom_fade_dist:
                t = dist_from_bottom / bottom_fade_dist
                # Cubic easing for ultra-smooth transition
                alpha *= t * t * t

            # Apply to mask
            mask.putpixel((x, y), int(255 * alpha))

    # Apply the mask to the alpha channel
    img.putalpha(mask)

    return img


def draw_centered_string(canvas_obj, text, font_name, font_size, center_x, baseline_y, fill_color, alpha=1.0):
    """Draw a centred string with the given styling.

    Args:
        alpha: Opacity from 0.0 (transparent) to 1.0 (opaque)
    """
    canvas_obj.setFillColor(fill_color)
    canvas_obj.setFillAlpha(alpha)
    canvas_obj.setFont(font_name, font_size)
    canvas_obj.drawCentredString(center_x, baseline_y, text)
    canvas_obj.setFillAlpha(1.0)  # Reset to opaque for other elements


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
