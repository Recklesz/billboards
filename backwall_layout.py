"""
Backwall layout module using the refactored pipeline architecture.

Provides BackwallLayout class that orchestrates backwall graphic generation
with CMYK color management and asset pipeline integration.
"""

import os
import logging
from typing import Optional
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from PIL import Image
import tempfile

from graphics_config import GraphicsConfig
from canvas_utils import ExhibitGraphicV2, CMYKCanvas, fit_multiline_font_size
from asset_pipeline import AssetPipeline, GradientConfig, VignetteConfig
from color_management import BRAND_COLORS_CMYK, BRAND_COLORS_RGB


logger = logging.getLogger(__name__)


class BackwallLayout:
    """
    Backwall layout orchestrator using the new pipeline architecture.
    
    Handles all backwall-specific layout logic including background generation,
    image placement, typography, and logo positioning.
    """
    
    def __init__(self, config: GraphicsConfig, asset_pipeline: AssetPipeline):
        """
        Initialize backwall layout.
        
        Args:
            config: Graphics configuration
            asset_pipeline: Asset preparation pipeline
        """
        self.config = config
        self.asset_pipeline = asset_pipeline
        self.graphic: Optional[ExhibitGraphicV2] = None
        self.canvas: Optional[CMYKCanvas] = None
        
        # Layout parameters (can be made configurable)
        self.headline_line1 = "AI ROLEPLAY"
        self.headline_line2 = "FOR SALES TEAMS"
        self.face_position_y_mm = 1900  # mm from bottom
        self.headline_position_y_mm = 1520  # mm from bottom
    
    def _get_font_name(self) -> str:
        """Get headline font name, registering if needed."""
        from reportlab.pdfbase.ttfonts import TTFont
        
        preferred_font = "Ubuntu-Bold"
        if preferred_font in pdfmetrics.getRegisteredFontNames():
            return preferred_font
        
        font_path = self.config.assets.ubuntu_bold_font
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(preferred_font, font_path))
                return preferred_font
            except Exception as e:
                logger.warning(f"Could not register Ubuntu font: {e}. Using Helvetica-Bold.")
        
        return "Helvetica-Bold"
    
    def _draw_background(self):
        """Draw background with radial gradient accents."""
        logger.info("Drawing backwall background")
        
        # Calculate pixel dimensions for gradient (150 DPI)
        dpi = 150
        width_mm = self.graphic.doc_width / mm
        height_mm = self.graphic.doc_height / mm
        width_px = int(width_mm * (dpi / 25.4))
        height_px = int(height_mm * (dpi / 25.4))
        
        # For now, use PIL-based gradient generation (matching original)
        # TODO: Migrate to pure CMYK gradient using asset_pipeline
        from PIL import Image, ImageDraw
        import tempfile
        
        # Create white background
        bg_img = Image.new("RGB", (width_px, height_px), (255, 255, 255))
        overlay = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
        
        # Teal gradient spots
        teal_rgb = (90, 180, 190)
        gradient_spots = [
            {"x": 0.15, "y": 0.15, "radius": 0.35},
            {"x": 0.85, "y": 0.50, "radius": 0.30},
            {"x": 0.20, "y": 0.85, "radius": 0.25},
            {"x": 0.80, "y": 0.90, "radius": 0.22},
        ]
        
        for spot in gradient_spots:
            cx = int(spot["x"] * width_px)
            cy = int((1 - spot["y"]) * height_px)
            max_radius = int(spot["radius"] * max(width_px, height_px))
            
            for y in range(max(0, cy - max_radius), min(height_px, cy + max_radius)):
                for x in range(max(0, cx - max_radius), min(width_px, cx + max_radius)):
                    dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                    if dist < max_radius:
                        alpha = int(60 * (1 - (dist / max_radius) ** 1.5))
                        if alpha > 0:
                            existing = overlay.getpixel((x, y))
                            new_alpha = min(255, existing[3] + alpha)
                            overlay.putpixel((x, y), (*teal_rgb, new_alpha))
        
        bg_img.paste(overlay, (0, 0), overlay)
        
        # Save and draw
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            bg_img.save(tmp_path)
        
        try:
            # Convert to CMYK if needed
            if self.config.use_cmyk:
                cmyk_path = self.asset_pipeline.ensure_cmyk_asset(tmp_path, "backwall_bg.png")
                image_path = cmyk_path
            else:
                image_path = tmp_path

            # Use CMYK-aware image drawing
            self.canvas.draw_cmyk_image(
                image_path, 0, 0,
                width=self.graphic.doc_width,
                height=self.graphic.doc_height,
                preserve_aspect=False
            )
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
    
    def _draw_face_image(self):
        """Draw face image with vignette fade at top."""
        if not os.path.exists(self.config.assets.face_image):
            logger.warning("Face image not found")
            return
        
        logger.info("Drawing face image")
        
        try:
            # Apply vignette fade
            vignette_config = VignetteConfig(
                edge_fade=0.25,
                bottom_fade=0.45,
                top_fade=0.10
            )
            
            face_path = self.asset_pipeline.prepare_vignette_image(
                self.config.assets.face_image,
                vignette_config,
                output_name="face_vignetted.png"
            )
            
            # Calculate dimensions
            face_img = Image.open(face_path)
            face_ratio = face_img.height / face_img.width
            
            face_width = self.graphic.trim_width
            face_height = face_width * face_ratio
            
            # Position at top
            face_x = self.graphic.bleed
            face_y = self.graphic.bleed + (self.face_position_y_mm * mm) - (face_height / 2)
            
            # Keep within safe area
            max_y = self.graphic.doc_height - self.graphic.bleed - self.graphic.safe_inset - face_height
            if face_y > max_y:
                face_y = max_y
            
            # Draw using CMYK-aware method
            self.canvas.draw_cmyk_image(
                face_path, face_x, face_y,
                width=face_width, height=face_height,
                preserve_aspect=True,
                mask="auto"
            )
            
        except Exception as e:
            logger.error(f"Could not render face image: {e}", exc_info=True)
    
    def _draw_eyes_image(self, bg_y: float, bg_height: float) -> float:
        """
        Draw eyes image below text box with vignette fade.
        
        Args:
            bg_y: Y position of text box bottom
            bg_height: Height of text box
        
        Returns:
            Y position of eyes image
        """
        if not os.path.exists(self.config.assets.eyes_image):
            logger.warning("Eyes image not found")
            return 0
        
        logger.info("Drawing eyes image")
        
        try:
            # Apply vignette fade
            vignette_config = VignetteConfig(
                edge_fade=0.25,
                bottom_fade=0.35,
                top_fade=0.40
            )
            
            eyes_path = self.asset_pipeline.prepare_vignette_image(
                self.config.assets.eyes_image,
                vignette_config,
                output_name="eyes_vignetted.png"
            )
            
            # Calculate dimensions
            eyes_img = Image.open(eyes_path)
            eyes_ratio = eyes_img.height / eyes_img.width
            
            eyes_width = self.graphic.trim_width
            eyes_height = eyes_width * eyes_ratio
            
            # Position with overlap
            eyes_x = self.graphic.bleed
            overlap_amount = 120 * mm
            eyes_y = bg_y - eyes_height + overlap_amount
            
            logger.debug(f"Eyes positioning: bg_y={bg_y/mm:.1f}mm, eyes_y={eyes_y/mm:.1f}mm")
            
            # Draw using CMYK-aware method
            self.canvas.draw_cmyk_image(
                eyes_path, eyes_x, eyes_y,
                width=eyes_width, height=eyes_height,
                preserve_aspect=True,
                mask="auto"
            )
            
            return eyes_y
            
        except Exception as e:
            logger.error(f"Could not render eyes image: {e}", exc_info=True)
            return 0
    
    def _draw_text_box_and_content(self):
        """Draw text box with gradient transparency, headline, and logo."""
        logger.info("Drawing text box and content")
        
        headline_font = self._get_font_name()
        
        # Calculate safe area
        safe_width = self.graphic.trim_width - (2 * self.graphic.safe_inset)
        
        # Calculate font size
        max_headline_width = safe_width * 0.92
        headline_font_size = fit_multiline_font_size(
            [self.headline_line1, self.headline_line2],
            headline_font,
            max_headline_width,
            starting_size=300,
            minimum_size=80
        )
        
        # Calculate positioning
        headline_center_x = self.graphic.doc_width / 2
        ascent, descent = pdfmetrics.getAscentDescent(headline_font, headline_font_size)
        line_height = ascent - descent
        baseline_gap = line_height * 1.60
        
        first_baseline = self.graphic.bleed + (self.headline_position_y_mm * mm)
        
        # Ensure above no-text zone
        ntz_bounds = self.graphic.get_no_text_zone_bounds()
        if ntz_bounds:
            min_y = self.graphic.bleed + ntz_bounds[3] + (150 * mm)
            if first_baseline - line_height < min_y:
                first_baseline = min_y + line_height
        
        # Calculate text widths
        text_width_line1 = pdfmetrics.stringWidth(self.headline_line1, headline_font, headline_font_size)
        text_width_line2 = pdfmetrics.stringWidth(self.headline_line2, headline_font, headline_font_size)
        max_text_width = max(text_width_line1, text_width_line2)
        
        # Load logo dimensions
        logo_width, logo_height = self._get_logo_dimensions(safe_width)
        
        # Calculate box dimensions
        bg_padding_h = 30 * mm
        bg_padding_top = 35 * mm
        bg_padding_bottom = 60 * mm
        logo_gap = 60 * mm
        
        bg_x = headline_center_x - (max_text_width / 2) - bg_padding_h
        bg_y = first_baseline - baseline_gap - (descent * headline_font_size / 1000) - bg_padding_bottom - logo_height - logo_gap
        bg_width = max_text_width + (2 * bg_padding_h)
        bg_height = line_height + baseline_gap + bg_padding_top + bg_padding_bottom + logo_height + logo_gap
        bg_radius = 40 * mm
        
        # Draw eyes image first (underneath box)
        self._draw_eyes_image(bg_y, bg_height)
        
        # Draw text box with gradient transparency
        self._draw_gradient_text_box(bg_x, bg_y, bg_width, bg_height, bg_radius)
        
        # Draw text
        text_color = BRAND_COLORS_CMYK["headline_text"] if self.config.use_cmyk else BRAND_COLORS_RGB["headline_text"]
        
        if self.config.use_cmyk:
            self.canvas.draw_text_cmyk(
                self.headline_line1, headline_center_x, first_baseline,
                headline_font, headline_font_size, text_color, alpha=1.0, centered=True
            )
            self.canvas.draw_text_cmyk(
                self.headline_line2, headline_center_x, first_baseline - baseline_gap,
                headline_font, headline_font_size, text_color, alpha=1.0, centered=True
            )
        else:
            self.canvas.canvas.setFillColor(text_color)
            self.canvas.canvas.setFont(headline_font, headline_font_size)
            self.canvas.canvas.drawCentredString(headline_center_x, first_baseline, self.headline_line1)
            self.canvas.canvas.drawCentredString(headline_center_x, first_baseline - baseline_gap, self.headline_line2)
        
        # Draw logo
        if logo_width > 0:
            self._draw_logo(
                headline_center_x,
                first_baseline - baseline_gap - (descent * headline_font_size / 1000) - logo_gap,
                logo_width,
                logo_height
            )
    
    def _get_logo_dimensions(self, safe_width: float) -> tuple[float, float]:
        """Calculate logo dimensions."""
        if not os.path.exists(self.config.assets.logo):
            return (0, 0)
        
        try:
            with Image.open(self.config.assets.logo) as logo_img:
                logo_ratio = logo_img.height / logo_img.width
                max_logo_width = safe_width * 0.20
                logo_width = max_logo_width
                logo_height = logo_width * logo_ratio
                return (logo_width, logo_height)
        except Exception as e:
            logger.warning(f"Could not read logo dimensions: {e}")
            return (0, 0)
    
    def _draw_gradient_text_box(self, x: float, y: float, width: float, height: float, radius: float):
        """Draw semi-transparent box with gradient alpha and rounded corners."""
        from PIL import Image, ImageDraw, ImageChops
        import tempfile
        
        dpi = 150
        box_width_px = int((width / mm) * (dpi / 25.4))
        box_height_px = int((height / mm) * (dpi / 25.4))
        box_radius_px = int((radius / mm) * (dpi / 25.4))
        
        # Create RGBA image
        box_img = Image.new("RGBA", (box_width_px, box_height_px), (255, 255, 255, 0))
        draw = ImageDraw.Draw(box_img)
        
        # Draw with gradient alpha
        for y_px in range(box_height_px):
            t = y_px / box_height_px
            alpha = int(255 * (0.50 - (t * 0.20)))
            line_color = (255, 255, 255, alpha)
            draw.rectangle([0, y_px, box_width_px, y_px], fill=line_color)
        
        # Apply rounded corners
        mask = Image.new("L", (box_width_px, box_height_px), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, box_width_px, box_height_px], radius=box_radius_px, fill=255)
        box_img.putalpha(ImageChops.multiply(box_img.split()[3], mask))
        
        # Save and draw
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            box_img.save(tmp_path)
        
        try:
            # Use CMYK-aware method (temp file is PNG/RGB, which is fine for text box)
            self.canvas.draw_cmyk_image(tmp_path, x, y, width=width, height=height,
                                       preserve_aspect=False, mask="auto")
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
    
    def _draw_logo(self, center_x: float, baseline_y: float, width: float, height: float):
        """Draw logo centered at position."""
        if not os.path.exists(self.config.assets.logo):
            logger.warning("Logo not found")
            return
        
        try:
            logo_x = center_x - (width / 2)
            logo_y = baseline_y - height

            # Use CMYK-aware method
            self.canvas.draw_cmyk_image(
                self.config.assets.logo, logo_x, logo_y,
                width=width, height=height,
                preserve_aspect=True,
                mask="auto"
            )
        except Exception as e:
            logger.error(f"Could not render logo: {e}")
    
    def generate(self, output_path: str) -> str:
        """
        Generate backwall PDF.
        
        Args:
            output_path: Path to save PDF
        
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating backwall: {output_path}")
        
        # Create graphic
        self.graphic = ExhibitGraphicV2(
            "backwall",
            self.config.spec,
            is_backwall=True,
            use_cmyk=self.config.use_cmyk
        )
        
        # Create canvas
        self.canvas = self.graphic.create_canvas(output_path)
        
        # Draw layers
        self._draw_background()
        self._draw_face_image()
        self._draw_text_box_and_content()
        
        # Draw guides and crop marks
        self.graphic.draw_crop_marks()
        self.graphic.draw_guides(self.config.show_guides)
        self.graphic.draw_no_text_zone_guide(self.config.show_guides)
        
        # Save
        self.graphic.save()
        
        logger.info(f"Backwall generated: {output_path}")
        return output_path
