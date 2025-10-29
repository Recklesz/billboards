"""
Counter layout module using the refactored pipeline architecture.

Provides CounterLayout class that orchestrates counter graphic generation
with CMYK color management and asset pipeline integration.
"""

import os
import logging
import tempfile
from typing import Optional
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from PIL import Image

from graphics_config import GraphicsConfig
from canvas_utils import ExhibitGraphicV2, CMYKCanvas
from asset_pipeline import AssetPipeline, QRCodeConfig
from color_management import BRAND_COLORS_CMYK, BRAND_COLORS_RGB


logger = logging.getLogger(__name__)


class CounterLayout:
    """
    Counter layout orchestrator using the new pipeline architecture.
    
    Handles all counter-specific layout logic including background generation,
    QR code placement, logo, and website URL.
    """
    
    def __init__(self, config: GraphicsConfig, asset_pipeline: AssetPipeline):
        """
        Initialize counter layout.
        
        Args:
            config: Graphics configuration
            asset_pipeline: Asset preparation pipeline
        """
        self.config = config
        self.asset_pipeline = asset_pipeline
        self.graphic: Optional[ExhibitGraphicV2] = None
        self.canvas: Optional[CMYKCanvas] = None
        
        # Layout parameters (can be made configurable)
        self.qr_url = "https://www.getskylar.com/conference"
        self.website_text = "CallSkylar.com"
        self.qr_position_y_mm = 480  # mm from bottom
    
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
        """Draw background with radial gradient accents matching backwall."""
        logger.info("Drawing counter background")
        
        # Calculate pixel dimensions (150 DPI)
        dpi = 150
        width_mm = self.graphic.doc_width / mm
        height_mm = self.graphic.doc_height / mm
        width_px = int(width_mm * (dpi / 25.4))
        height_px = int(height_mm * (dpi / 25.4))
        
        # Create white background with teal gradient overlay
        bg_img = Image.new("RGB", (width_px, height_px), (255, 255, 255))
        overlay = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
        
        # Teal gradient spots
        teal_rgb = (90, 180, 190)
        gradient_spots = [
            {"x": 0.20, "y": 0.15, "radius": 0.40},
            {"x": 0.80, "y": 0.25, "radius": 0.35},
            {"x": 0.15, "y": 0.50, "radius": 0.30},
            {"x": 0.85, "y": 0.65, "radius": 0.28},
            {"x": 0.50, "y": 0.88, "radius": 0.32},
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
                cmyk_path = self.asset_pipeline.ensure_cmyk_asset(tmp_path, "counter_bg.png")
                bg_reader = ImageReader(cmyk_path)
            else:
                bg_reader = ImageReader(tmp_path)
            
            self.canvas.canvas.drawImage(
                bg_reader, 0, 0,
                width=self.graphic.doc_width,
                height=self.graphic.doc_height
            )
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
    
    def _draw_qr_code(self):
        """Draw QR code in elegant rounded container."""
        logger.info("Drawing QR code")
        
        try:
            # Generate QR code
            qr_config = QRCodeConfig(
                data=self.qr_url,
                size_px=800,
                fg_color=(0, 0, 0, 255) if self.config.use_cmyk else (14, 46, 62, 255),
                bg_color=(0, 0, 0, 0),  # White in CMYK
                border=2
            )
            
            qr_path = self.asset_pipeline.prepare_qr_code(qr_config)
            
            # Calculate dimensions
            safe_width = self.graphic.trim_width - (2 * self.graphic.safe_inset)
            qr_size = safe_width * 0.65
            qr_x = (self.graphic.doc_width - qr_size) / 2
            qr_y = self.graphic.bleed + (self.qr_position_y_mm * mm)
            
            # Draw container
            container_padding = 25 * mm
            container_x = qr_x - container_padding
            container_y = qr_y - container_padding
            container_width = qr_size + (2 * container_padding)
            container_height = qr_size + (2 * container_padding)
            container_radius = 35 * mm
            
            # Draw semi-transparent white container
            if self.config.use_cmyk:
                white_cmyk = BRAND_COLORS_CMYK["pure_white"]
                self.canvas.draw_rounded_rect_cmyk(
                    container_x, container_y, container_width, container_height,
                    container_radius,
                    fill_color=white_cmyk,
                    fill_alpha=0.92
                )
            else:
                self.canvas.canvas.setFillColorRGB(1, 1, 1, alpha=0.92)
                self.canvas.canvas.roundRect(
                    container_x, container_y, container_width, container_height,
                    container_radius, fill=1, stroke=0
                )
            
            # Draw QR code
            qr_reader = ImageReader(qr_path)
            self.canvas.canvas.drawImage(
                qr_reader, qr_x, qr_y,
                width=qr_size, height=qr_size,
                preserveAspectRatio=True
            )
            
        except Exception as e:
            logger.error(f"Could not render QR code: {e}", exc_info=True)
    
    def _draw_website_text(self, qr_y: float):
        """Draw website URL below QR code."""
        logger.info("Drawing website text")
        
        headline_font = self._get_font_name()
        website_font_size = 42
        
        text_color = BRAND_COLORS_CMYK["headline_text"] if self.config.use_cmyk else BRAND_COLORS_RGB["headline_text"]
        
        # Calculate position
        text_width = pdfmetrics.stringWidth(self.website_text, headline_font, website_font_size)
        text_x = (self.graphic.doc_width - text_width) / 2
        text_y = qr_y - (55 * mm)
        
        # Draw text
        if self.config.use_cmyk:
            self.canvas.draw_text_cmyk(
                self.website_text, text_x, text_y,
                headline_font, website_font_size, text_color
            )
        else:
            self.canvas.canvas.setFillColor(text_color)
            self.canvas.canvas.setFont(headline_font, website_font_size)
            self.canvas.canvas.drawString(text_x, text_y, self.website_text)
    
    def _draw_logo(self):
        """Draw Skylar logo at bottom."""
        if not os.path.exists(self.config.assets.logo):
            logger.warning("Logo not found")
            return
        
        logger.info("Drawing logo")
        
        try:
            with Image.open(self.config.assets.logo) as logo_img:
                logo_ratio = logo_img.height / logo_img.width
                
                # Calculate dimensions
                safe_origin_x = self.graphic.bleed + self.graphic.safe_inset
                safe_origin_y = self.graphic.bleed + self.graphic.safe_inset
                safe_width = self.graphic.trim_width - (2 * self.graphic.safe_inset)
                
                max_logo_width = safe_width * 0.55
                logo_width = max_logo_width
                logo_height = logo_width * logo_ratio
                
                # Position at bottom
                logo_x = (self.graphic.doc_width - logo_width) / 2
                logo_y = safe_origin_y + (40 * mm)
                
                # Draw
                logo_reader = ImageReader(self.config.assets.logo)
                self.canvas.canvas.drawImage(
                    logo_reader, logo_x, logo_y,
                    width=logo_width, height=logo_height,
                    mask="auto", preserveAspectRatio=True
                )
        except Exception as e:
            logger.error(f"Could not render logo: {e}")
    
    def generate(self, output_path: str) -> str:
        """
        Generate counter PDF.
        
        Args:
            output_path: Path to save PDF
        
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating counter: {output_path}")
        
        # Create graphic
        self.graphic = ExhibitGraphicV2(
            "counter",
            self.config.spec,
            is_backwall=False,
            use_cmyk=self.config.use_cmyk
        )
        
        # Create canvas
        self.canvas = self.graphic.create_canvas(output_path)
        
        # Draw layers
        self._draw_background()
        self._draw_qr_code()
        
        # Get QR position for website text
        qr_y = self.graphic.bleed + (self.qr_position_y_mm * mm)
        self._draw_website_text(qr_y)
        
        self._draw_logo()
        
        # Draw guides and crop marks
        self.graphic.draw_crop_marks()
        self.graphic.draw_guides(self.config.show_guides)
        
        # Save
        self.graphic.save()
        
        logger.info(f"Counter generated: {output_path}")
        return output_path
