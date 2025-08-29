"""
Bundle Worker

Handles asset compression, optimization, and tour bundle generation:
- Asset compression and optimization
- Navmesh generation for VR navigation
- Light probe baking for realistic lighting
- glTF/USDZ export for cross-platform compatibility
- Tour bundle packaging for distribution
- Asset streaming optimization
"""

from .main import app
from .processor import BundleProcessor
from .asset_compressor import AssetCompressor
from .navmesh_baker import NavmeshBaker
from .lightmap_baker import LightmapBaker
from .format_exporter import FormatExporter

__all__ = [
    "app",
    "BundleProcessor",
    "AssetCompressor",
    "NavmeshBaker", 
    "LightmapBaker",
    "FormatExporter",
]
