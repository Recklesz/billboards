"""
Asset preparation pipeline for exhibit graphics.

Handles gradient generation, vignette application, QR code creation,
and ensures all assets are CMYK-compliant before embedding.
"""

import os
import hashlib
import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

from color_management import (
    CMYKColor, ensure_cmyk_image, create_cmyk_gradient_image,
    apply_cmyk_vignette, BRAND_COLORS_CMYK
)


logger = logging.getLogger(__name__)


@dataclass
class GradientConfig:
    """Configuration for gradient background generation."""
    width_px: int
    height_px: int
    color_top: CMYKColor
    color_bottom: CMYKColor
    hotspot_x: Optional[float] = None  # 0-1, horizontal position of gradient center
    hotspot_y: Optional[float] = None  # 0-1, vertical position of gradient center
    
    def get_cache_key(self) -> str:
        """Generate cache key for this gradient configuration."""
        data = f"{self.width_px}x{self.height_px}_{self.color_top}_{self.color_bottom}"
        return hashlib.md5(data.encode()).hexdigest()


@dataclass
class VignetteConfig:
    """Configuration for vignette fade application."""
    edge_fade: float = 0.25  # Percentage of width
    bottom_fade: float = 0.45  # Percentage of height
    top_fade: float = 0.05  # Percentage of height
    
    def get_cache_key(self) -> str:
        """Generate cache key for this vignette configuration."""
        data = f"vignette_{self.edge_fade}_{self.bottom_fade}_{self.top_fade}"
        return hashlib.md5(data.encode()).hexdigest()


@dataclass
class QRCodeConfig:
    """Configuration for QR code generation."""
    data: str
    size_px: int = 400
    fg_color: Tuple[int, int, int, int] = (0, 0, 0, 255)  # CMYK black
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)  # CMYK white
    border: int = 2
    
    def get_cache_key(self) -> str:
        """Generate cache key for this QR code configuration."""
        data = f"qr_{self.data}_{self.size_px}_{self.border}"
        return hashlib.md5(data.encode()).hexdigest()


class AssetCache:
    """
    Cache manager for generated assets.
    
    Stores intermediate assets with hashed filenames to avoid
    redundant regeneration during iterative runs.
    """
    
    def __init__(self, cache_dir: str):
        """
        Initialize asset cache.
        
        Args:
            cache_dir: Directory to store cached assets
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_path(self, cache_key: str, extension: str = ".png") -> str:
        """Get path for a cached asset."""
        return os.path.join(self.cache_dir, f"{cache_key}{extension}")
    
    def exists(self, cache_key: str, extension: str = ".png") -> bool:
        """Check if cached asset exists."""
        return os.path.exists(self.get_path(cache_key, extension))
    
    def clear(self):
        """Remove all cached assets."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Cleared asset cache: {self.cache_dir}")


class AssetPipeline:
    """
    Asset preparation pipeline with CMYK enforcement.
    
    Generates and caches gradients, vignettes, QR codes, and ensures
    all assets are CMYK-compliant before use.
    """
    
    def __init__(self, cache_dir: str, force_cmyk: bool = True):
        """
        Initialize asset pipeline.
        
        Args:
            cache_dir: Directory for cached assets
            force_cmyk: If True, convert all assets to CMYK
        """
        self.cache = AssetCache(cache_dir)
        self.force_cmyk = force_cmyk
    
    def prepare_gradient(self, config: GradientConfig) -> str:
        """
        Generate or retrieve cached gradient image.
        
        Args:
            config: Gradient configuration
        
        Returns:
            Path to gradient image
        """
        cache_key = config.get_cache_key()
        output_path = self.cache.get_path(cache_key)
        
        if self.cache.exists(cache_key):
            logger.debug(f"Using cached gradient: {cache_key}")
            return output_path
        
        logger.info(f"Generating gradient: {config.width_px}x{config.height_px}px")
        
        # Generate gradient
        create_cmyk_gradient_image(
            config.width_px,
            config.height_px,
            config.color_top,
            config.color_bottom,
            output_path
        )
        
        return output_path
    
    def prepare_vignette_image(self, source_path: str, config: VignetteConfig,
                               output_name: Optional[str] = None) -> str:
        """
        Apply vignette fade to an image.
        
        Args:
            source_path: Path to source image
            config: Vignette configuration
            output_name: Optional output filename (otherwise uses cache key)
        
        Returns:
            Path to vignetted image
        """
        # Generate cache key based on source and config
        source_hash = hashlib.md5(source_path.encode()).hexdigest()[:8]
        vignette_hash = config.get_cache_key()
        cache_key = f"{source_hash}_{vignette_hash}"
        
        if output_name:
            output_path = self.cache.get_path(output_name, "")
        else:
            output_path = self.cache.get_path(cache_key)
        
        # Check for both original extension and .tif (CMYK images are saved as TIFF)
        tif_path = output_path
        if output_path.lower().endswith('.png'):
            tif_path = output_path[:-4] + '.tif'

        if os.path.exists(tif_path):
            logger.debug(f"Using cached vignette: {cache_key}")
            return tif_path

        if os.path.exists(output_path):
            logger.debug(f"Using cached vignette: {cache_key}")
            return output_path

        logger.info(f"Applying vignette to: {os.path.basename(source_path)}")

        # Ensure source is CMYK
        if self.force_cmyk:
            cmyk_source = self.cache.get_path(f"{source_hash}_cmyk")
            actual_cmyk_source = ensure_cmyk_image(source_path, cmyk_source)
            source_path = actual_cmyk_source

        # Apply vignette
        actual_output = apply_cmyk_vignette(
            source_path,
            output_path,
            edge_fade=config.edge_fade,
            bottom_fade=config.bottom_fade,
            top_fade=config.top_fade
        )

        return actual_output
    
    def prepare_qr_code(self, config: QRCodeConfig) -> str:
        """
        Generate or retrieve cached QR code.
        
        Args:
            config: QR code configuration
        
        Returns:
            Path to QR code image
        """
        cache_key = config.get_cache_key()
        output_path = self.cache.get_path(cache_key)
        
        if self.cache.exists(cache_key):
            logger.debug(f"Using cached QR code: {cache_key}")
            return output_path
        
        logger.info(f"Generating QR code for: {config.data[:50]}...")
        
        try:
            import qrcode
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=config.border,
            )
            qr.add_data(config.data)
            qr.make(fit=True)
            
            # Generate image in CMYK mode
            img = qr.make_image(fill_color=config.fg_color, back_color=config.bg_color)
            
            # Ensure CMYK mode
            if img.mode != 'CMYK':
                img = img.convert('CMYK')
            
            # Resize to desired size
            img = img.resize((config.size_px, config.size_px), Image.Resampling.LANCZOS)
            
            img.save(output_path)
            return output_path
            
        except ImportError:
            logger.error("qrcode library not installed. Install with: pip install qrcode[pil]")
            raise
    
    def ensure_cmyk_asset(self, source_path: str, output_name: Optional[str] = None) -> str:
        """
        Ensure an asset is in CMYK mode.
        
        Args:
            source_path: Path to source image
            output_name: Optional output filename
        
        Returns:
            Path to CMYK image
        """
        if not self.force_cmyk:
            return source_path
        
        source_hash = hashlib.md5(source_path.encode()).hexdigest()[:8]
        
        if output_name:
            output_path = self.cache.get_path(output_name, "")
        else:
            output_path = self.cache.get_path(f"{source_hash}_cmyk")
        
        # Check for both original extension and .tif (CMYK images are saved as TIFF)
        tif_path = output_path
        if output_path.lower().endswith('.png'):
            tif_path = output_path[:-4] + '.tif'

        if os.path.exists(tif_path):
            logger.debug(f"Using cached CMYK asset: {os.path.basename(tif_path)}")
            return tif_path

        if os.path.exists(output_path):
            logger.debug(f"Using cached CMYK asset: {os.path.basename(output_path)}")
            return output_path

        logger.info(f"Converting to CMYK: {os.path.basename(source_path)}")
        actual_path = ensure_cmyk_image(source_path, output_path)

        return actual_path
    
    def prepare_logo(self, logo_path: str, target_width_px: int,
                    preserve_transparency: bool = True) -> str:
        """
        Prepare logo at specific size, optionally preserving transparency.
        
        Args:
            logo_path: Path to source logo
            target_width_px: Target width in pixels
            preserve_transparency: If True, keep alpha channel
        
        Returns:
            Path to prepared logo
        """
        source_hash = hashlib.md5(logo_path.encode()).hexdigest()[:8]
        cache_key = f"{source_hash}_logo_{target_width_px}{'_alpha' if preserve_transparency else ''}"
        output_path = self.cache.get_path(cache_key)
        
        if os.path.exists(output_path):
            logger.debug(f"Using cached logo: {cache_key}")
            return output_path
        
        logger.info(f"Preparing logo: {target_width_px}px wide")
        
        img = Image.open(logo_path)
        
        # Calculate target height maintaining aspect ratio
        aspect_ratio = img.height / img.width
        target_height_px = int(target_width_px * aspect_ratio)
        
        # Resize
        img_resized = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)
        
        # Handle color mode
        if preserve_transparency and img_resized.mode in ('RGBA', 'LA'):
            # Keep transparency for compositing
            img_resized.save(output_path)
        else:
            # Convert to CMYK
            if img_resized.mode == 'RGBA':
                # Composite on white background
                background = Image.new('RGB', img_resized.size, (255, 255, 255))
                background.paste(img_resized, mask=img_resized.split()[3])
                img_resized = background
            elif img_resized.mode != 'RGB':
                img_resized = img_resized.convert('RGB')
            
            if self.force_cmyk:
                img_resized = img_resized.convert('CMYK')
            
            img_resized.save(output_path)
        
        return output_path


def create_bottom_fade_mask(width: int, height: int, fade_percentage: float = 0.35) -> Image.Image:
    """
    Create an alpha mask with bottom fade for compositing.
    
    Args:
        width: Mask width in pixels
        height: Mask height in pixels
        fade_percentage: Percentage of height to fade (0-1)
    
    Returns:
        PIL Image in 'L' mode (grayscale alpha mask)
    """
    mask = Image.new("L", (width, height), 255)
    
    fade_height = int(height * fade_percentage)
    fade_start = height - fade_height
    
    for y in range(fade_start, height):
        alpha = int(255 * (1 - (y - fade_start) / fade_height))
        for x in range(width):
            mask.putpixel((x, y), alpha)
    
    return mask


def calculate_dpi_for_size(width_mm: float, height_mm: float,
                           width_pts: float, height_pts: float,
                           target_dpi: int = 300) -> Tuple[int, int]:
    """
    Calculate pixel dimensions for a given physical size and target DPI.
    
    Args:
        width_mm: Physical width in millimeters
        height_mm: Physical height in millimeters
        width_pts: Width in points (for verification)
        height_pts: Height in points (for verification)
        target_dpi: Target DPI
    
    Returns:
        (width_px, height_px) tuple
    """
    # Convert mm to inches
    width_inches = width_mm / 25.4
    height_inches = height_mm / 25.4
    
    # Calculate pixel dimensions
    width_px = int(width_inches * target_dpi)
    height_px = int(height_inches * target_dpi)
    
    return (width_px, height_px)
