"""
Configuration and specification models for exhibit graphics generation.

Provides dataclass-based models that can be loaded from JSON and used
throughout the pipeline to ensure consistency.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import json
import os
from reportlab.lib.units import mm


@dataclass
class DimensionSpec:
    """Dimensions in millimeters."""
    width: float
    height: float
    
    def to_points(self) -> tuple[float, float]:
        """Convert to ReportLab points."""
        return (self.width * mm, self.height * mm)


@dataclass
class BleedSpec:
    """Bleed specifications."""
    all_sides: float  # mm
    
    def to_points(self) -> float:
        """Convert to ReportLab points."""
        return self.all_sides * mm


@dataclass
class NoTextZone:
    """No-text zone specification (backwall only)."""
    x: float  # mm from left edge of trim
    y: float  # mm from bottom edge of trim
    width: float  # mm
    height: float  # mm
    
    def to_points(self) -> Dict[str, float]:
        """Convert to ReportLab points."""
        return {
            "x": self.x * mm,
            "y": self.y * mm,
            "width": self.width * mm,
            "height": self.height * mm
        }


@dataclass
class RichBlackSpec:
    """Rich black CMYK recipe."""
    C: float  # 0-100
    M: float  # 0-100
    Y: float  # 0-100
    K: float  # 0-100
    
    def to_normalized(self) -> tuple[float, float, float, float]:
        """Convert to 0-1 range for ReportLab."""
        return (self.C / 100.0, self.M / 100.0, self.Y / 100.0, self.K / 100.0)


@dataclass
class PrintSpec:
    """Print production specifications."""
    color_mode: str  # "CMYK"
    min_effective_dpi: int
    preferred_effective_dpi: int
    rich_black: RichBlackSpec
    outline_all_text: bool
    embed_images: bool
    deliver_as_pdf_with_crop_marks_and_bleed: bool


@dataclass
class BackwallSpec:
    """Backwall graphic specifications."""
    trim: DimensionSpec
    bleed: BleedSpec
    safe_inset: float  # mm
    no_text_zone: NoTextZone
    
    def get_doc_size(self) -> tuple[float, float]:
        """Get document size including bleed, in points."""
        trim_w, trim_h = self.trim.to_points()
        bleed_pts = self.bleed.to_points()
        return (trim_w + 2 * bleed_pts, trim_h + 2 * bleed_pts)
    
    def get_safe_area(self) -> Dict[str, float]:
        """Get safe area bounds in points (relative to trim origin)."""
        safe_inset_pts = self.safe_inset * mm
        trim_w, trim_h = self.trim.to_points()
        return {
            "x": safe_inset_pts,
            "y": safe_inset_pts,
            "width": trim_w - 2 * safe_inset_pts,
            "height": trim_h - 2 * safe_inset_pts
        }


@dataclass
class CounterSpec:
    """Counter graphic specifications."""
    trim: DimensionSpec
    bleed: BleedSpec
    safe_inset: float  # mm
    
    def get_doc_size(self) -> tuple[float, float]:
        """Get document size including bleed, in points."""
        trim_w, trim_h = self.trim.to_points()
        bleed_pts = self.bleed.to_points()
        return (trim_w + 2 * bleed_pts, trim_h + 2 * bleed_pts)
    
    def get_safe_area(self) -> Dict[str, float]:
        """Get safe area bounds in points (relative to trim origin)."""
        safe_inset_pts = self.safe_inset * mm
        trim_w, trim_h = self.trim.to_points()
        return {
            "x": safe_inset_pts,
            "y": safe_inset_pts,
            "width": trim_w - 2 * safe_inset_pts,
            "height": trim_h - 2 * safe_inset_pts
        }


@dataclass
class GraphicsSpec:
    """Complete graphics specifications."""
    units: str
    backwall: BackwallSpec
    counter: CounterSpec
    print_spec: PrintSpec
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GraphicsSpec':
        """Load specifications from dictionary."""
        backwall_data = data["backwall"]
        counter_data = data["counter"]
        print_data = data["print"]
        
        return cls(
            units=data["units"],
            backwall=BackwallSpec(
                trim=DimensionSpec(**backwall_data["trim"]),
                bleed=BleedSpec(**backwall_data["bleed"]),
                safe_inset=backwall_data["safe_inset"],
                no_text_zone=NoTextZone(**backwall_data["no_text_zone"])
            ),
            counter=CounterSpec(
                trim=DimensionSpec(**counter_data["trim"]),
                bleed=BleedSpec(**counter_data["bleed"]),
                safe_inset=counter_data["safe_inset"]
            ),
            print_spec=PrintSpec(
                color_mode=print_data["color_mode"],
                min_effective_dpi=print_data["min_effective_dpi"],
                preferred_effective_dpi=print_data["preferred_effective_dpi"],
                rich_black=RichBlackSpec(**print_data["rich_black"]),
                outline_all_text=print_data["outline_all_text"],
                embed_images=print_data["embed_images"],
                deliver_as_pdf_with_crop_marks_and_bleed=print_data["deliver_as_pdf_with_crop_marks_and_bleed"]
            )
        )
    
    @classmethod
    def from_json_file(cls, json_path: str) -> 'GraphicsSpec':
        """Load specifications from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_requirements_md(cls) -> 'GraphicsSpec':
        """
        Load default specifications matching requirements.md.
        
        This provides the baseline spec without requiring a JSON file.
        """
        return cls.from_dict({
            "units": "mm",
            "backwall": {
                "trim": {"width": 1000, "height": 2170},
                "bleed": {"all_sides": 5},
                "safe_inset": 50,
                "no_text_zone": {"x": 700, "y": 0, "width": 300, "height": 800}
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
        })


@dataclass
class AssetPaths:
    """Paths to graphic assets."""
    logo: str
    face_image: str
    eyes_image: str
    ubuntu_bold_font: str
    
    def validate(self) -> list[str]:
        """Check which assets are missing and return list of missing paths."""
        missing = []
        for name, path in [
            ("logo", self.logo),
            ("face_image", self.face_image),
            ("eyes_image", self.eyes_image),
            ("ubuntu_bold_font", self.ubuntu_bold_font)
        ]:
            if not os.path.exists(path):
                missing.append(f"{name}: {path}")
        return missing
    
    @classmethod
    def default(cls, base_dir: Optional[str] = None) -> 'AssetPaths':
        """Create default asset paths relative to base directory."""
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        return cls(
            logo=os.path.join(base_dir, "assets", "skylar-clean-logo.png"),
            face_image=os.path.join(base_dir, "assets", "b7255f53-8368-4d30-bc18-698d6a1ac0df.png"),
            eyes_image=os.path.join(base_dir, "assets", "19842217-02bc-47dd-96cf-cd23d758449d.png"),
            ubuntu_bold_font=os.path.join(base_dir, "assets", "fonts", "Ubuntu-Bold.ttf")
        )


@dataclass
class OutputPaths:
    """Output directory structure."""
    base_dir: str
    raw_dir: str = field(init=False)
    final_dir: str = field(init=False)
    temp_dir: str = field(init=False)
    proofs_dir: str = field(init=False)
    
    def __post_init__(self):
        """Initialize subdirectories."""
        self.raw_dir = os.path.join(self.base_dir, "raw")
        self.final_dir = self.base_dir  # Final PDFs go in base output dir
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.proofs_dir = os.path.join(self.base_dir, "proofs")
    
    def ensure_directories(self):
        """Create all output directories if they don't exist."""
        for dir_path in [self.base_dir, self.raw_dir, self.temp_dir, self.proofs_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def cleanup_temp(self):
        """Remove temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)


@dataclass
class GraphicsConfig:
    """Complete configuration for graphics generation."""
    spec: GraphicsSpec
    assets: AssetPaths
    output: OutputPaths
    use_cmyk: bool = True
    generate_proofs: bool = True
    show_guides: bool = False
    run_inkscape_outlining: bool = False
    
    @classmethod
    def default(cls, output_dir: str = "output", show_guides: bool = False) -> 'GraphicsConfig':
        """Create default configuration."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        return cls(
            spec=GraphicsSpec.from_requirements_md(),
            assets=AssetPaths.default(base_dir),
            output=OutputPaths(os.path.join(base_dir, output_dir)),
            use_cmyk=True,
            generate_proofs=True,
            show_guides=show_guides,
            run_inkscape_outlining=False
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check assets
        missing_assets = self.assets.validate()
        if missing_assets:
            issues.append("Missing assets:")
            issues.extend(f"  - {asset}" for asset in missing_assets)
        
        # Check output directory is writable
        try:
            self.output.ensure_directories()
        except Exception as e:
            issues.append(f"Cannot create output directories: {e}")
        
        return issues
