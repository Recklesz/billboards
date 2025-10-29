"""
Enhanced canvas utilities and drawing primitives for exhibit graphics.

Provides reusable drawing functions, context managers for temporary assets,
and CMYK-aware canvas operations.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from contextlib import contextmanager
import os
import tempfile
import logging
from typing import Optional, Tuple, List
from PIL import Image

from color_management import CMYKColor, BRAND_COLORS_CMYK
from graphics_config import GraphicsSpec, BackwallSpec, CounterSpec


logger = logging.getLogger(__name__)


class CMYKCanvas:
    """
    Wrapper around ReportLab canvas that enforces CMYK color operations.
    
    Provides convenience methods for CMYK drawing and ensures all color
    operations use CMYK color space for print compliance.
    """
    
    def __init__(self, canvas_obj: canvas.Canvas, use_cmyk: bool = True):
        """
        Initialize CMYK canvas wrapper.
        
        Args:
            canvas_obj: ReportLab Canvas instance
            use_cmyk: If True, enforce CMYK colors; if False, allow RGB (for proofs)
        """
        self.canvas = canvas_obj
        self.use_cmyk = use_cmyk
    
    def set_fill_color_cmyk(self, color: CMYKColor, alpha: float = 1.0):
        """Set fill color using CMYK values."""
        if self.use_cmyk:
            c, m, y, k = color.to_tuple_normalized()
            self.canvas.setFillColorCMYK(c, m, y, k, alpha=alpha)
        else:
            # For proofs, use RGB approximation
            self.canvas.setFillColor(color.to_reportlab())
            self.canvas.setFillAlpha(alpha)
    
    def set_stroke_color_cmyk(self, color: CMYKColor, alpha: float = 1.0):
        """Set stroke color using CMYK values."""
        if self.use_cmyk:
            c, m, y, k = color.to_tuple_normalized()
            self.canvas.setStrokeColorCMYK(c, m, y, k, alpha=alpha)
        else:
            # For proofs, use RGB approximation
            self.canvas.setStrokeColor(color.to_reportlab())
            self.canvas.setStrokeAlpha(alpha)
    
    def draw_rect_cmyk(self, x: float, y: float, width: float, height: float,
                       fill_color: Optional[CMYKColor] = None,
                       stroke_color: Optional[CMYKColor] = None,
                       fill_alpha: float = 1.0,
                       stroke_alpha: float = 1.0):
        """Draw a rectangle with CMYK colors."""
        if fill_color:
            self.set_fill_color_cmyk(fill_color, fill_alpha)
        if stroke_color:
            self.set_stroke_color_cmyk(stroke_color, stroke_alpha)
        
        fill = 1 if fill_color else 0
        stroke = 1 if stroke_color else 0
        
        self.canvas.rect(x, y, width, height, fill=fill, stroke=stroke)
    
    def draw_rounded_rect_cmyk(self, x: float, y: float, width: float, height: float,
                               radius: float,
                               fill_color: Optional[CMYKColor] = None,
                               stroke_color: Optional[CMYKColor] = None,
                               fill_alpha: float = 1.0,
                               stroke_alpha: float = 1.0):
        """Draw a rounded rectangle with CMYK colors."""
        if fill_color:
            self.set_fill_color_cmyk(fill_color, fill_alpha)
        if stroke_color:
            self.set_stroke_color_cmyk(stroke_color, stroke_alpha)
        
        fill = 1 if fill_color else 0
        stroke = 1 if stroke_color else 0
        
        self.canvas.roundRect(x, y, width, height, radius, fill=fill, stroke=stroke)
    
    def draw_text_cmyk(self, text: str, x: float, y: float,
                       font_name: str, font_size: float,
                       color: CMYKColor, alpha: float = 1.0,
                       centered: bool = False):
        """Draw text with CMYK color."""
        self.set_fill_color_cmyk(color, alpha)
        self.canvas.setFont(font_name, font_size)

        if centered:
            self.canvas.drawCentredString(x, y, text)
        else:
            self.canvas.drawString(x, y, text)

        # Reset alpha
        self.canvas.setFillAlpha(1.0)

    def draw_cmyk_image(self, image_path: str, x: float, y: float,
                        width: float, height: float,
                        preserve_aspect: bool = True,
                        mask: str = "auto"):
        """
        Draw an image preserving CMYK color mode.

        Args:
            image_path: Path to image file
            x, y: Position in points
            width, height: Size in points
            preserve_aspect: If True, maintain aspect ratio
            mask: Mask mode ('auto', None, or mask data)

        Note:
            This method uses PIL to directly embed CMYK images in the PDF,
            avoiding ReportLab's ImageReader which converts to RGB.
        """
        try:
            img = Image.open(image_path)

            # If image is CMYK and we want to preserve it
            if img.mode == 'CMYK' and self.use_cmyk:
                # Use drawInlineImage to preserve CMYK
                self.canvas.drawInlineImage(
                    img, x, y,
                    width=width,
                    height=height,
                    preserveAspectRatio=preserve_aspect
                )
            else:
                # Fallback to standard method for non-CMYK or proof mode
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(image_path)
                self.canvas.drawImage(
                    img_reader, x, y,
                    width=width,
                    height=height,
                    mask=mask,
                    preserveAspectRatio=preserve_aspect
                )
        except Exception as e:
            logger.error(f"Failed to draw image {image_path}: {e}")
            raise

    def __getattr__(self, name):
        """Delegate unknown attributes to underlying canvas."""
        return getattr(self.canvas, name)


class ExhibitGraphicV2:
    """
    Enhanced base class for creating exhibit graphics with CMYK support.
    
    Provides geometry calculations, guide drawing, and temporary asset management.
    """
    
    def __init__(self, name: str, spec: GraphicsSpec, 
                 is_backwall: bool = False,
                 use_cmyk: bool = True):
        """
        Initialize exhibit graphic.
        
        Args:
            name: Name of the graphic (e.g., 'backwall', 'counter')
            spec: Graphics specification
            is_backwall: True if this is a backwall (has no-text zone)
            use_cmyk: Use CMYK color mode
        """
        self.name = name
        self.spec = spec
        self.is_backwall = is_backwall
        self.use_cmyk = use_cmyk
        
        # Get appropriate spec
        if is_backwall:
            self.item_spec = spec.backwall
        else:
            self.item_spec = spec.counter
        
        # Calculate dimensions
        self.trim_width, self.trim_height = self.item_spec.trim.to_points()
        self.bleed = self.item_spec.bleed.to_points()
        self.safe_inset = self.item_spec.safe_inset * mm
        
        # Document size includes bleed
        self.doc_width = self.trim_width + (2 * self.bleed)
        self.doc_height = self.trim_height + (2 * self.bleed)
        
        # Canvas wrapper
        self.canvas_wrapper: Optional[CMYKCanvas] = None
        self._temp_files: List[str] = []
    
    def create_canvas(self, filename: str) -> CMYKCanvas:
        """Create PDF canvas with proper dimensions and CMYK support."""
        raw_canvas = canvas.Canvas(
            filename,
            pagesize=(self.doc_width, self.doc_height)
        )
        self.canvas_wrapper = CMYKCanvas(raw_canvas, use_cmyk=self.use_cmyk)
        return self.canvas_wrapper
    
    def get_trim_origin(self) -> Tuple[float, float]:
        """Get the origin point of the trim area in document coordinates."""
        return (self.bleed, self.bleed)
    
    def get_safe_area_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get safe area bounds in document coordinates.
        
        Returns:
            (x, y, width, height) in points
        """
        x = self.bleed + self.safe_inset
        y = self.bleed + self.safe_inset
        width = self.trim_width - (2 * self.safe_inset)
        height = self.trim_height - (2 * self.safe_inset)
        return (x, y, width, height)
    
    def get_no_text_zone_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Get no-text zone bounds in document coordinates (backwall only).
        
        Returns:
            (x, y, width, height) in points, or None if not backwall
        """
        if not self.is_backwall:
            return None
        
        ntz = self.item_spec.no_text_zone.to_points()
        return (
            self.bleed + ntz["x"],
            self.bleed + ntz["y"],
            ntz["width"],
            ntz["height"]
        )
    
    def draw_background_cmyk(self, color: CMYKColor):
        """Draw background color extending to bleed."""
        if not self.canvas_wrapper:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        self.canvas_wrapper.draw_rect_cmyk(
            0, 0, self.doc_width, self.doc_height,
            fill_color=color
        )
    
    def draw_crop_marks(self):
        """Draw crop/trim marks at corners."""
        if not self.canvas_wrapper:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        c = self.canvas_wrapper.canvas
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
    
    def draw_guides(self, show_guides: bool = True):
        """Draw safe area and bleed guides (for reference, not in final)."""
        if not show_guides or not self.canvas_wrapper:
            return
        
        c = self.canvas_wrapper.canvas
        c.setStrokeColor(colors.Color(0, 1, 1, alpha=0.5))  # Cyan guide
        c.setLineWidth(0.25)
        c.setDash(3, 3)
        
        # Trim box
        c.rect(self.bleed, self.bleed, self.trim_width, self.trim_height)
        
        # Safe area
        safe_x, safe_y, safe_w, safe_h = self.get_safe_area_bounds()
        c.rect(safe_x, safe_y, safe_w, safe_h)
        
        c.setDash()  # Reset dash
    
    def draw_no_text_zone_guide(self, show_guides: bool = True):
        """Draw no-text zone indicator (backwall only)."""
        if not show_guides or not self.is_backwall or not self.canvas_wrapper:
            return
        
        bounds = self.get_no_text_zone_bounds()
        if not bounds:
            return
        
        x, y, width, height = bounds
        
        c = self.canvas_wrapper.canvas
        c.setStrokeColor(colors.Color(1, 0, 0, alpha=0.5))  # Red guide
        c.setLineWidth(0.5)
        c.setDash(5, 5)
        
        c.rect(x, y, width, height)
        c.setDash()  # Reset dash
    
    @contextmanager
    def temp_asset(self, suffix: str = ".png"):
        """
        Context manager for temporary asset files.
        
        Usage:
            with graphic.temp_asset(".png") as temp_path:
                # Generate asset at temp_path
                ...
            # File is tracked for cleanup
        """
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self._temp_files.append(temp_path)
        
        try:
            yield temp_path
        except Exception as e:
            logger.error(f"Error with temp asset {temp_path}: {e}")
            raise
    
    def cleanup_temp_assets(self):
        """Remove all temporary asset files."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file}: {e}")
        
        self._temp_files.clear()
    
    def save(self):
        """Save the PDF and cleanup temporary assets."""
        if self.canvas_wrapper:
            self.canvas_wrapper.canvas.save()
        self.cleanup_temp_assets()


def fit_text_size(text: str, font_name: str, max_width: float,
                  starting_size: float = 220, minimum_size: float = 48) -> float:
    """
    Reduce font size until the string fits within max_width (points).
    
    Args:
        text: Text to fit
        font_name: Font name
        max_width: Maximum width in points
        starting_size: Starting font size
        minimum_size: Minimum font size
    
    Returns:
        Font size that fits
    """
    font_size = starting_size
    while font_size > minimum_size:
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        if text_width <= max_width:
            break
        font_size -= 1
    return font_size


def fit_multiline_font_size(lines: List[str], font_name: str, max_width: float,
                            starting_size: float = 220, minimum_size: float = 48) -> float:
    """
    Reduce font size until all lines fit within max_width.
    
    Args:
        lines: List of text lines
        font_name: Font name
        max_width: Maximum width in points
        starting_size: Starting font size
        minimum_size: Minimum font size
    
    Returns:
        Font size that fits all lines
    """
    font_size = starting_size
    while font_size > minimum_size:
        widths = [pdfmetrics.stringWidth(line, font_name, font_size) for line in lines]
        if max(widths) <= max_width:
            break
        font_size -= 1
    return font_size


def draw_gradient_background(canvas_wrapper: CMYKCanvas, 
                             x: float, y: float, width: float, height: float,
                             color_top: CMYKColor, color_bottom: CMYKColor,
                             temp_dir: str, dpi: int = 300):
    """
    Draw a vertical gradient background using a temporary CMYK image.
    
    Args:
        canvas_wrapper: CMYKCanvas instance
        x, y: Position in points
        width, height: Size in points
        color_top: CMYK color at top
        color_bottom: CMYK color at bottom
        temp_dir: Directory for temporary files
        dpi: DPI for gradient image
    """
    from color_management import create_cmyk_gradient_image
    
    # Calculate pixel dimensions
    width_inches = width / 72.0
    height_inches = height / 72.0
    width_px = int(width_inches * dpi)
    height_px = int(height_inches * dpi)
    
    # Create temp gradient image
    temp_path = os.path.join(temp_dir, f"gradient_{id(canvas_wrapper)}.png")
    create_cmyk_gradient_image(width_px, height_px, color_top, color_bottom, temp_path)
    
    # Draw on canvas
    canvas_wrapper.canvas.drawImage(temp_path, x, y, width=width, height=height,
                                   preserveAspectRatio=False, mask='auto')
    
    # Cleanup
    try:
        os.remove(temp_path)
    except Exception as e:
        logger.warning(f"Could not remove temp gradient: {e}")
