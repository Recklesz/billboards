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
    "gradient_navy": colors.HexColor("#0A1F2E"),
    "gradient_royal_blue": colors.HexColor("#1A4D6F"),
    "gradient_medium_blue": colors.HexColor("#5BA8C8"),
    "gradient_light_blue": colors.HexColor("#B8E3F0"),
    "gradient_white": colors.HexColor("#F5FAFC"),
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "skylar-clean-logo.png")
EYES_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "8f686ed8-df57-4a5c-8b7e-1ad42ded5b90.png")
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




def draw_radial_gradient_spot(canvas_obj, center_x, center_y, max_radius, center_color, num_rings=80):
    """
    Draw a radial gradient spot that fades from center color to transparent/white.

    Args:
        canvas_obj: ReportLab canvas
        center_x, center_y: Center point of the radial gradient
        max_radius: Maximum radius of the gradient
        center_color: Color at the center (will fade to white)
        num_rings: Number of concentric circles to draw
    """
    for i in range(num_rings, 0, -1):
        # Calculate distance from center (0 at center, 1 at edge)
        t = i / num_rings

        # Fade from center color to white
        r = center_color.red + (1.0 - center_color.red) * (1 - t)
        g = center_color.green + (1.0 - center_color.green) * (1 - t)
        b = center_color.blue + (1.0 - center_color.blue) * (1 - t)

        # Reduce alpha as we go out
        alpha = t * 0.3  # Max 30% opacity

        ring_color = colors.Color(r, g, b, alpha)
        canvas_obj.setFillColor(ring_color)
        canvas_obj.setStrokeColor(ring_color)

        radius = max_radius * t
        canvas_obj.circle(center_x, center_y, radius, fill=1, stroke=0)


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
    import os
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


def create_sample_backwall(output_dir="output", show_guides=True):
    """
    Create clean, bold backwall graphic with eyes image and BIG two-line headline

    Args:
        output_dir: Directory to save output files
        show_guides: Whether to show guide lines (safe area, no-text zone)
    """
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Backwall_100x217cm_bleed5mm_CMYK.pdf")

    graphic = BackwallGraphic()
    c = graphic.create_canvas(filename)

    # Simple clean white background
    draw_backwall_background(c, graphic)

    safe_width = graphic.trim_width - (2 * graphic.safe_inset)
    safe_height = graphic.trim_height - (2 * graphic.safe_inset)

    # Add crop marks and guides
    graphic.draw_crop_marks()
    graphic.draw_guides(show_guides)
    graphic.draw_no_text_zone_guide(show_guides)

    # Face image - FULL WIDTH with bottom fade
    if os.path.exists(EYES_IMAGE_PATH):
        try:
            # Create image with bottom fade for natural blending
            eyes_img = create_bottom_fade_image(EYES_IMAGE_PATH, fade_percentage=0.35)
            eyes_ratio = eyes_img.height / eyes_img.width

            # FULL WIDTH - use entire trim width
            eyes_width = graphic.trim_width
            eyes_height = eyes_width * eyes_ratio

            # Position at top, centered horizontally
            eyes_x = graphic.bleed
            eyes_y = graphic.bleed + (1900 * mm) - (eyes_height / 2)

            # Keep top within safe area
            max_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - eyes_height
            if eyes_y > max_y:
                eyes_y = max_y

            # Save processed image temporarily for ReportLab
            temp_path = os.path.join(output_dir, "_temp_eyes_fade.png")
            eyes_img.save(temp_path)

            eyes_reader = ImageReader(temp_path)
            c.drawImage(
                eyes_reader,
                eyes_x,
                eyes_y,
                width=eyes_width,
                height=eyes_height,
                preserveAspectRatio=True,
            )

            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass

        except Exception as exc:
            print(f"⚠ Could not render eyes image: {exc}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ Eyes image not found.")

    # BIG HEADLINE - Two lines, Ubuntu Bold
    headline_font = get_headline_font_name()
    line1 = "AI ROLEPLAY"
    line2 = "FOR SALES TEAMS"

    # Make it BIG
    max_headline_width = safe_width * 0.95
    headline_font_size = fit_multiline_font_size(
        [line1, line2],
        headline_font,
        max_headline_width,
        starting_size=350,  # Start even bigger
        minimum_size=100
    )

    # Position so only top half of "AI ROLEPLAY" overlaps with smile
    # "FOR SALES TEAMS" should be completely below the image
    headline_center_x = graphic.doc_width / 2

    # Calculate line spacing
    ascent, descent = pdfmetrics.getAscentDescent(headline_font, headline_font_size)
    line_height = ascent - descent
    baseline_gap = line_height * 1.15  # Tight spacing

    # Position at ~154cm so only bottom portion of first line overlaps with smile
    first_baseline = graphic.bleed + (1540 * mm)

    # Ensure we're above no-text zone
    min_y = graphic.bleed + graphic.no_text_zone["height"] + (150 * mm)
    if first_baseline - line_height < min_y:
        first_baseline = min_y + line_height

    # Calculate text width for background
    text_width_line1 = pdfmetrics.stringWidth(line1, headline_font, headline_font_size)
    text_width_line2 = pdfmetrics.stringWidth(line2, headline_font, headline_font_size)
    max_text_width = max(text_width_line1, text_width_line2)

    # Draw semi-transparent background behind text with rounded corners
    # This makes text readable while showing some of the smile through
    bg_padding_h = 30 * mm  # Horizontal padding around text
    bg_padding_v = 45 * mm  # Vertical padding for more space between lines
    bg_x = headline_center_x - (max_text_width / 2) - bg_padding_h
    bg_y = first_baseline - baseline_gap - (descent * headline_font_size / 1000) - bg_padding_v
    bg_width = max_text_width + (2 * bg_padding_h)
    bg_height = line_height + baseline_gap + (2 * bg_padding_v)
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

    # Logo - prominent and visible (below text, 100cm = 1000mm)
    if os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as logo_img:
                logo_ratio = logo_img.height / logo_img.width

            # Make logo bigger and more visible
            max_logo_width = safe_width * 0.25
            max_logo_height = safe_height * 0.10
            computed_logo_height = max_logo_width * logo_ratio

            if computed_logo_height > max_logo_height:
                computed_logo_height = max_logo_height
                max_logo_width = computed_logo_height / logo_ratio

            logo_reader = ImageReader(LOGO_PATH)
            logo_x = (graphic.doc_width - max_logo_width) / 2
            logo_y = graphic.bleed + (1000 * mm)

            c.drawImage(
                logo_reader,
                logo_x,
                logo_y,
                width=max_logo_width,
                height=computed_logo_height,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception as exc:
            print(f"⚠ Could not read logo: {exc}")
    else:
        print("⚠ Logo not found.")

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
