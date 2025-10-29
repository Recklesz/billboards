"""
CMYK color management utilities for print-ready graphics.

Provides conversion between RGB/hex and CMYK, ICC profile handling,
and utilities to ensure all assets are CMYK-compliant before embedding.
"""

from reportlab.lib import colors
from PIL import Image, ImageCms
import os
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class CMYKColor:
    """CMYK color representation with conversion utilities."""
    c: float  # 0-100
    m: float  # 0-100
    y: float  # 0-100
    k: float  # 0-100
    
    def to_reportlab(self) -> colors.CMYKColor:
        """Convert to ReportLab CMYKColor (0-1 range)."""
        return colors.CMYKColor(
            self.c / 100.0,
            self.m / 100.0,
            self.y / 100.0,
            self.k / 100.0
        )
    
    def to_tuple_normalized(self) -> Tuple[float, float, float, float]:
        """Return CMYK as normalized tuple (0-1 range) for ReportLab."""
        return (self.c / 100.0, self.m / 100.0, self.y / 100.0, self.k / 100.0)
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'CMYKColor':
        """
        Convert hex color to CMYK using simple RGB->CMYK conversion.
        
        Note: This is a basic conversion. For accurate color matching,
        use ICC profiles with ensure_cmyk_image().
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB (0-1 range)
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return cls.from_rgb(r, g, b)
    
    @classmethod
    def from_rgb(cls, r: float, g: float, b: float) -> 'CMYKColor':
        """
        Convert RGB (0-1 range) to CMYK using standard conversion.
        
        Args:
            r, g, b: RGB values in 0-1 range
        
        Returns:
            CMYKColor instance
        """
        # Handle pure black
        if r == 0 and g == 0 and b == 0:
            return cls(0, 0, 0, 100)
        
        # Standard RGB to CMYK conversion
        k = 1 - max(r, g, b)
        
        if k == 1:
            return cls(0, 0, 0, 100)
        
        c = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        y = (1 - b - k) / (1 - k)
        
        return cls(c * 100, m * 100, y * 100, k * 100)


# Brand color palette in CMYK
# These values are derived from the hex colors but should be verified
# with actual print tests for accurate reproduction
BRAND_COLORS_CMYK = {
    "background": CMYKColor(3, 1, 0, 2),  # #F8FAFC - very light blue-gray
    "headline_text": CMYKColor(85, 60, 40, 60),  # #0E2E3E - dark blue-gray
    "accent_primary": CMYKColor(70, 0, 10, 0),  # #37BCD9 - bright cyan
    "accent_light": CMYKColor(40, 0, 0, 0),  # #8EE6F7 - light cyan
    "accent_muted": CMYKColor(15, 0, 0, 0),  # #DDF2F8 - very light cyan
    "accent_dark": CMYKColor(85, 25, 20, 5),  # #197FA1 - dark cyan
    "rich_black": CMYKColor(60, 40, 40, 100),  # Rich black recipe from requirements
    "pure_white": CMYKColor(0, 0, 0, 0),  # Pure white
}


# Legacy RGB colors for backward compatibility and proof generation
BRAND_COLORS_RGB = {
    "background": colors.HexColor("#F8FAFC"),
    "headline_text": colors.HexColor("#0E2E3E"),
    "accent_primary": colors.HexColor("#37BCD9"),
    "accent_light": colors.HexColor("#8EE6F7"),
    "accent_muted": colors.HexColor("#DDF2F8"),
    "accent_dark": colors.HexColor("#197FA1"),
}


def get_icc_profile_path() -> Optional[str]:
    """
    Get path to ICC profile for CMYK conversion.
    
    Returns None if no profile is available. Falls back to basic conversion.
    """
    # Common ICC profile locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "assets", "color", "ISOcoated_v2_300_eci.icc"),
        os.path.join(os.path.dirname(__file__), "assets", "color", "USWebCoatedSWOP.icc"),
        "/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc",  # macOS
        "/usr/share/color/icc/ISOcoated_v2_300_eci.icc",  # Linux
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def ensure_cmyk_image(image_path: str, output_path: Optional[str] = None,
                      icc_profile_path: Optional[str] = None) -> str:
    """
    Convert an image to CMYK mode, ensuring print compatibility.

    Args:
        image_path: Path to source image
        output_path: Path to save CMYK image (if None, overwrites source)
        icc_profile_path: Path to ICC profile (if None, uses default or basic conversion)

    Returns:
        Path to the CMYK image

    Note:
        CMYK images are saved as TIFF since PNG doesn't support CMYK mode.
        The output_path extension will be changed to .tif if it's .png
    """
    if output_path is None:
        output_path = image_path

    # PNG doesn't support CMYK, use JPEG for better PDF compatibility
    if output_path.lower().endswith('.png'):
        output_path = output_path[:-4] + '.jpg'
    elif not output_path.lower().endswith(('.tif', '.tiff', '.jpg', '.jpeg')):
        # Add .jpg extension if no extension or unsupported extension
        output_path = output_path + '.jpg'

    img = Image.open(image_path)

    # If already CMYK, just save and return
    if img.mode == 'CMYK':
        if output_path != image_path:
            img.save(output_path)
        return output_path

    # Try ICC profile conversion first for better accuracy
    if icc_profile_path is None:
        icc_profile_path = get_icc_profile_path()

    if icc_profile_path and os.path.exists(icc_profile_path):
        try:
            # Convert to RGB first if not already
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Load profiles
            rgb_profile = ImageCms.createProfile("sRGB")
            cmyk_profile = ImageCms.getOpenProfile(icc_profile_path)

            # Create transform
            transform = ImageCms.buildTransform(
                rgb_profile, cmyk_profile,
                "RGB", "CMYK",
                renderingIntent=ImageCms.Intent.PERCEPTUAL
            )

            # Apply transform
            img_cmyk = ImageCms.applyTransform(img, transform)
            img_cmyk.save(output_path)
            return output_path

        except Exception as e:
            print(f"⚠ ICC profile conversion failed: {e}. Using basic conversion.")

    # Fallback to basic conversion
    if img.mode == 'RGBA':
        # Handle transparency by compositing on white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Convert to CMYK
    img_cmyk = img.convert('CMYK')
    img_cmyk.save(output_path)

    return output_path


def create_cmyk_gradient_image(width: int, height: int,
                               color_top: CMYKColor,
                               color_bottom: CMYKColor,
                               output_path: str) -> str:
    """
    Create a vertical gradient image in CMYK mode.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color_top: CMYK color at top
        color_bottom: CMYK color at bottom
        output_path: Where to save the gradient image

    Returns:
        Path to the created image

    Note:
        CMYK images are saved as TIFF since PNG doesn't support CMYK mode.
        The output_path extension will be changed to .tif if it's .png
    """
    # PNG doesn't support CMYK, use JPEG for better PDF compatibility
    if output_path.lower().endswith('.png'):
        output_path = output_path[:-4] + '.jpg'
    elif not output_path.lower().endswith(('.tif', '.tiff', '.jpg', '.jpeg')):
        # Add .jpg extension if no extension or unsupported extension
        output_path = output_path + '.jpg'

    # Create CMYK image
    img = Image.new('CMYK', (width, height))
    
    # Generate gradient
    for y in range(height):
        # Linear interpolation factor (0 at top, 1 at bottom)
        t = y / (height - 1) if height > 1 else 0
        
        # Interpolate each channel
        c = color_top.c + (color_bottom.c - color_top.c) * t
        m = color_top.m + (color_bottom.m - color_top.m) * t
        y_val = color_top.y + (color_bottom.y - color_top.y) * t
        k = color_top.k + (color_bottom.k - color_top.k) * t
        
        # Convert to 0-255 range for PIL
        pixel = (
            int(c * 2.55),
            int(m * 2.55),
            int(y_val * 2.55),
            int(k * 2.55)
        )
        
        # Draw horizontal line
        for x in range(width):
            img.putpixel((x, y), pixel)
    
    img.save(output_path)
    return output_path


def verify_cmyk_mode(image_path: str) -> bool:
    """
    Check if an image is in CMYK mode.
    
    Args:
        image_path: Path to image file
    
    Returns:
        True if image is CMYK, False otherwise
    """
    try:
        img = Image.open(image_path)
        return img.mode == 'CMYK'
    except Exception:
        return False


def apply_cmyk_vignette(image_path: str, output_path: str,
                        edge_fade: float = 0.25,
                        bottom_fade: float = 0.45,
                        top_fade: float = 0.05) -> str:
    """
    Apply vignette fade to a CMYK image while preserving CMYK mode.

    Args:
        image_path: Path to source CMYK image
        output_path: Path to save result
        edge_fade: Percentage of width to fade on sides
        bottom_fade: Percentage of height to fade on bottom
        top_fade: Percentage of height to fade on top

    Returns:
        Path to the output image

    Note:
        CMYK images are saved as TIFF since PNG doesn't support CMYK mode.
        The output_path extension will be changed to .tif if it's .png
    """
    # PNG doesn't support CMYK, use JPEG for better PDF compatibility
    if output_path.lower().endswith('.png'):
        output_path = output_path[:-4] + '.jpg'
    elif not output_path.lower().endswith(('.tif', '.tiff', '.jpg', '.jpeg')):
        # Add .jpg extension if no extension or unsupported extension
        output_path = output_path + '.jpg'

    img = Image.open(image_path)

    # Ensure CMYK mode
    if img.mode != 'CMYK':
        img = img.convert('CMYK')
    
    width, height = img.size
    
    # Calculate fade distances
    side_fade_dist = int(width * edge_fade)
    bottom_fade_dist = int(height * bottom_fade)
    top_fade_dist = int(height * top_fade)
    
    # Create a copy to modify
    result = img.copy()
    pixels = result.load()
    
    # Apply vignette with smooth cubic easing
    for y in range(height):
        for x in range(width):
            # Calculate distance from each edge
            dist_left = x
            dist_right = width - x - 1
            dist_from_top = y
            dist_from_bottom = height - y - 1
            
            # Start with full opacity
            alpha = 1.0
            
            # Apply side fades
            if dist_left < side_fade_dist:
                t = dist_left / side_fade_dist
                alpha *= t * t * (3 - 2 * t)  # Smoothstep
            if dist_right < side_fade_dist:
                t = dist_right / side_fade_dist
                alpha *= t * t * (3 - 2 * t)
            
            # Apply top fade
            if dist_from_top < top_fade_dist:
                t = dist_from_top / top_fade_dist
                alpha *= t * t * (3 - 2 * t)
            
            # Apply bottom fade
            if dist_from_bottom < bottom_fade_dist:
                t = dist_from_bottom / bottom_fade_dist
                alpha *= t * t * t  # Cubic easing
            
            # Apply fade to pixel (fade toward white in CMYK = 0,0,0,0)
            if alpha < 1.0:
                c, m, y_val, k = pixels[x, y]
                pixels[x, y] = (
                    int(c * alpha),
                    int(m * alpha),
                    int(y_val * alpha),
                    int(k * alpha)
                )
    
    result.save(output_path)
    return output_path
