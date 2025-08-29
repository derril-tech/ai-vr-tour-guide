"""
Overlay Worker FastAPI Application

Handles 3D overlay placement, anchor solving, and spatial visualization.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import OverlayProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global processor instance
processor: OverlayProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global processor
    
    # Initialize services
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    # Initialize processor
    processor = OverlayProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Overlay worker started successfully")
    yield
    
    # Cleanup
    if processor:
        await processor.cleanup()
    logger.info("Overlay worker stopped")


# Create FastAPI app
app = FastAPI(
    title="AI VR Tour Guide - Overlay Worker",
    description="3D overlay placement and spatial visualization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnchorRequest(BaseModel):
    """Request model for anchor placement."""
    site_id: str
    tenant_id: str
    anchor_type: str  # "hotspot", "label", "ghost_reconstruction", "timeline"
    position: List[float]  # [x, y, z]
    rotation: List[float] = [0, 0, 0, 1]  # [x, y, z, w] quaternion
    scale: List[float] = [1, 1, 1]
    content: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class OverlayRequest(BaseModel):
    """Request model for overlay generation."""
    site_id: str
    tenant_id: str
    overlay_type: str  # "heatmap", "timeline", "route", "reconstruction"
    anchors: List[str]  # List of anchor IDs
    parameters: Dict[str, Any] = {}
    lod_levels: int = 3


class AnchorResponse(BaseModel):
    """Response model for anchor operations."""
    anchor_id: str
    status: str
    message: str
    position: List[float]
    occlusion_score: float = 0.0
    lod_level: int = 0


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "overlay-worker"}


@app.post("/anchors/place", response_model=AnchorResponse)
async def place_anchor(request: AnchorRequest):
    """
    Place a spatial anchor with occlusion awareness.
    
    Calculates optimal placement considering:
    - Scene geometry and occlusion
    - User viewing angles
    - Spatial constraints
    - Performance optimization
    """
    try:
        result = await processor.place_anchor(request)
        return AnchorResponse(**result)
        
    except Exception as e:
        logger.error(f"Error placing anchor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/anchors/solve")
async def solve_anchor_placement(
    background_tasks: BackgroundTasks,
    site_id: str,
    tenant_id: str,
    anchor_ids: List[str]
):
    """
    Solve optimal placement for multiple anchors simultaneously.
    
    Uses constraint solving to minimize occlusion and maximize visibility.
    """
    try:
        # Process in background for complex solving
        background_tasks.add_task(
            processor.solve_anchor_placement,
            site_id,
            tenant_id,
            anchor_ids
        )
        
        return {
            "status": "accepted",
            "message": "Anchor placement solving started",
            "site_id": site_id,
            "anchor_count": len(anchor_ids)
        }
        
    except Exception as e:
        logger.error(f"Error solving anchor placement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/overlays/generate")
async def generate_overlay(
    background_tasks: BackgroundTasks,
    request: OverlayRequest
):
    """
    Generate 3D overlays (heatmaps, timelines, reconstructions).
    
    Creates adaptive LOD versions for performance optimization.
    """
    try:
        # Process in background
        background_tasks.add_task(
            processor.generate_overlay,
            request
        )
        
        return {
            "status": "accepted",
            "message": "Overlay generation started",
            "overlay_type": request.overlay_type,
            "site_id": request.site_id
        }
        
    except Exception as e:
        logger.error(f"Error generating overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anchors/{anchor_id}/occlusion")
async def check_occlusion(anchor_id: str, viewpoint: List[float]):
    """
    Check occlusion for an anchor from a specific viewpoint.
    
    Returns occlusion score and visibility recommendations.
    """
    try:
        result = await processor.check_occlusion(anchor_id, viewpoint)
        return result
        
    except Exception as e:
        logger.error(f"Error checking occlusion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/overlays/{overlay_id}/lod/{level}")
async def get_overlay_lod(overlay_id: str, level: int):
    """
    Get specific LOD level for an overlay.
    
    Returns optimized geometry and textures for the requested detail level.
    """
    try:
        result = await processor.get_overlay_lod(overlay_id, level)
        return result
        
    except Exception as e:
        logger.error(f"Error getting overlay LOD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/heatmaps/generate")
async def generate_heatmap(
    site_id: str,
    tenant_id: str,
    data_type: str,  # "dwell_time", "interaction", "gaze", "movement"
    time_range: Dict[str, str] = None
):
    """
    Generate spatial heatmaps from telemetry data.
    
    Visualizes user behavior patterns in 3D space.
    """
    try:
        result = await processor.generate_heatmap(
            site_id, tenant_id, data_type, time_range
        )
        return result
        
    except Exception as e:
        logger.error(f"Error generating heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reconstructions/ghost")
async def create_ghost_reconstruction(
    site_id: str,
    tenant_id: str,
    time_period: str,  # Historical period to reconstruct
    reference_images: List[str] = None
):
    """
    Create ghost reconstructions of historical states.
    
    Generates transparent 3D models showing how spaces looked in the past.
    """
    try:
        result = await processor.create_ghost_reconstruction(
            site_id, tenant_id, time_period, reference_images
        )
        return result
        
    except Exception as e:
        logger.error(f"Error creating ghost reconstruction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/anchors/{anchor_id}")
async def delete_anchor(anchor_id: str, tenant_id: str):
    """Delete an anchor and its associated overlays."""
    try:
        await processor.delete_anchor(anchor_id, tenant_id)
        return {"status": "deleted", "anchor_id": anchor_id}
        
    except Exception as e:
        logger.error(f"Error deleting anchor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
