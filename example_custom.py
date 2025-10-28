"""
Example: Creating Custom Exhibit Graphics

This example shows how to customize the graphics with your own content,
colors, images, and branding.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from graphics_generator import BackwallGraphic, CounterGraphic
import os


def create_custom_backwall():
    """Create a custom backwall with branded content"""

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Custom_Backwall.pdf")

    # Initialize backwall graphic
    graphic = BackwallGraphic()
    c = graphic.create_canvas(filename)

    # ====================
    # BACKGROUND
    # ====================

    # Gradient effect using multiple rectangles (simplified gradient)
    # Top color: deep blue
    # Bottom color: lighter blue

    num_steps = 100
    for i in range(num_steps):
        # Interpolate between two colors
        t = i / num_steps
        r = 0.0 + (0.3 * t)
        g = 0.2 + (0.5 * t)
        b = 0.5 + (0.3 * t)

        c.setFillColor(colors.Color(r, g, b))
        rect_height = graphic.doc_height / num_steps

        c.rect(
            0,
            i * rect_height,
            graphic.doc_width,
            rect_height + 1,  # +1 to avoid gaps
            fill=1,
            stroke=0
        )

    # ====================
    # MAIN HEADING (in safe area, avoiding no-text zone)
    # ====================

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 120)

    # Position in upper portion, centered
    heading = "INNOVATE"
    text_width = c.stringWidth(heading, "Helvetica-Bold", 120)
    text_x = (graphic.doc_width - text_width) / 2
    text_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (200 * mm)

    c.drawString(text_x, text_y, heading)

    # ====================
    # SUBHEADING
    # ====================

    c.setFont("Helvetica", 48)
    subheading = "Transform Your Business"
    sub_width = c.stringWidth(subheading, "Helvetica", 48)
    sub_x = (graphic.doc_width - sub_width) / 2
    sub_y = text_y - (80 * mm)

    c.drawString(sub_x, sub_y, subheading)

    # ====================
    # LOGO PLACEHOLDER (centered, upper area)
    # ====================

    logo_width = 400 * mm
    logo_height = 200 * mm
    logo_x = (graphic.doc_width - logo_width) / 2
    logo_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (600 * mm)

    # Draw logo placeholder box
    c.setStrokeColor(colors.white)
    c.setLineWidth(3)
    c.rect(logo_x, logo_y, logo_width, logo_height, fill=0, stroke=1)

    c.setFont("Helvetica", 36)
    c.drawString(logo_x + (130 * mm), logo_y + (85 * mm), "YOUR LOGO HERE")

    # Tip: Replace the placeholder with an actual image:
    # from reportlab.lib.utils import ImageReader
    # img = ImageReader("your_logo.png")
    # c.drawImage(img, logo_x, logo_y, width=logo_width, height=logo_height,
    #             preserveAspectRatio=True, mask='auto')

    # ====================
    # KEY FEATURES (bullet points in safe area, right side)
    # ====================

    features = [
        "• Advanced Technology",
        "• Proven Results",
        "• Expert Support",
        "• Global Reach"
    ]

    c.setFont("Helvetica", 36)
    feature_x = graphic.bleed + graphic.safe_inset + (500 * mm)
    feature_y = graphic.bleed + graphic.safe_inset + (400 * mm)

    for i, feature in enumerate(features):
        c.drawString(feature_x, feature_y + (i * 60 * mm), feature)

    # ====================
    # WEBSITE/CONTACT (bottom right, above no-text zone)
    # ====================

    c.setFont("Helvetica-Bold", 32)
    contact = "www.yourcompany.com"
    contact_x = graphic.bleed + graphic.safe_inset + (400 * mm)
    contact_y = graphic.bleed + graphic.safe_inset + (100 * mm)

    c.drawString(contact_x, contact_y, contact)

    # ====================
    # DECORATIVE ELEMENTS
    # ====================

    # Add some decorative circles/shapes (in safe area)
    c.setFillColor(colors.Color(1, 1, 1, alpha=0.1))  # Semi-transparent white

    for i in range(5):
        circle_x = graphic.bleed + (100 * mm) + (i * 150 * mm)
        circle_y = graphic.doc_height - (400 * mm)
        c.circle(circle_x, circle_y, 50 * mm, fill=1, stroke=0)

    # ====================
    # GUIDES (for review only - set to False for production)
    # ====================

    show_guides = True
    graphic.draw_crop_marks()
    graphic.draw_guides(show_guides)
    graphic.draw_no_text_zone_guide(show_guides)

    # ====================
    # SAVE
    # ====================

    graphic.save()
    print(f"✓ Created custom backwall: {filename}")

    # Note: The no-text zone (bottom-left 30×80cm) has been avoided
    # All text and logos are in the safe area

    return filename


def create_custom_counter():
    """Create a custom counter graphic matching the backwall"""

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "Custom_Counter.pdf")

    graphic = CounterGraphic()
    c = graphic.create_canvas(filename)

    # ====================
    # BACKGROUND (matching backwall)
    # ====================

    num_steps = 50
    for i in range(num_steps):
        t = i / num_steps
        r = 0.0 + (0.3 * t)
        g = 0.2 + (0.5 * t)
        b = 0.5 + (0.3 * t)

        c.setFillColor(colors.Color(r, g, b))
        rect_height = graphic.doc_height / num_steps
        c.rect(0, i * rect_height, graphic.doc_width, rect_height + 1, fill=1, stroke=0)

    # ====================
    # BRANDING
    # ====================

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 72)

    brand = "INNOVATE"
    brand_width = c.stringWidth(brand, "Helvetica-Bold", 72)
    brand_x = (graphic.doc_width - brand_width) / 2
    brand_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (150 * mm)

    c.drawString(brand_x, brand_y, brand)

    # ====================
    # LOGO PLACEHOLDER
    # ====================

    logo_width = 180 * mm
    logo_height = 120 * mm
    logo_x = (graphic.doc_width - logo_width) / 2
    logo_y = graphic.doc_height - graphic.bleed - graphic.safe_inset - (400 * mm)

    c.setStrokeColor(colors.white)
    c.setLineWidth(2)
    c.rect(logo_x, logo_y, logo_width, logo_height, fill=0, stroke=1)

    c.setFont("Helvetica", 18)
    c.drawString(logo_x + (35 * mm), logo_y + (55 * mm), "YOUR LOGO HERE")

    # ====================
    # CALL TO ACTION
    # ====================

    c.setFont("Helvetica-Bold", 28)
    cta = "Visit Booth #123"
    cta_width = c.stringWidth(cta, "Helvetica-Bold", 28)
    cta_x = (graphic.doc_width - cta_width) / 2
    cta_y = graphic.bleed + graphic.safe_inset + (80 * mm)

    c.drawString(cta_x, cta_y, cta)

    # ====================
    # GUIDES & SAVE
    # ====================

    show_guides = True
    graphic.draw_crop_marks()
    graphic.draw_guides(show_guides)

    graphic.save()
    print(f"✓ Created custom counter: {filename}")

    return filename


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CUSTOM EXHIBIT GRAPHICS")
    print("="*60 + "\n")

    create_custom_backwall()
    create_custom_counter()

    print("\n✓ Custom graphics created successfully!")
    print("\nNext steps:")
    print("  1. Review the PDFs in the output/ directory")
    print("  2. Replace placeholder text with your actual content")
    print("  3. Add your logo images using c.drawImage()")
    print("  4. Adjust colors to match your brand")
    print("  5. Set show_guides=False for final production")
    print("  6. Convert all text to outlines in Adobe Illustrator")
    print("  7. Send to printer!\n")
