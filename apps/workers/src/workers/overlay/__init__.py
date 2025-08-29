"""
Overlay Worker

Handles 3D anchor placement and overlay generation:
- Spatial anchor solving and placement
- Occlusion awareness and depth testing
- Adaptive Level of Detail (LOD) for overlays
- Ghost reconstructions and temporal overlays
- Heatmap generation and visualization
- 3D label and ribbon placement
"""

from .main import app
from .processor import OverlayProcessor
from .anchor_solver import AnchorSolver
from .occlusion_manager import OcclusionManager
from .lod_manager import LODManager

__all__ = [
    "app",
    "OverlayProcessor",
    "AnchorSolver", 
    "OcclusionManager",
    "LODManager",
]
