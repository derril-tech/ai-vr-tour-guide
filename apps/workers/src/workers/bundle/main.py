"""
Bundle Worker FastAPI Application

Handles asset compression, optimization, and tour bundle generation.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import BundleProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global processor instance
processor: BundleProcessor = None


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
    processor = BundleProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Bundle worker started successfully")
    yield
    
    # Cleanup
    if processor:
        await processor.cleanup()
    logger.info("Bundle worker stopped")


# Create FastAPI app
app = FastAPI(
    title="AI VR Tour Guide - Bundle Worker",
    description="Asset compression and tour bundle generation",
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


class BundleRequest(BaseModel):
    """Request model for bundle generation."""
    site_id: str
    tenant_id: str
    bundle_type: str  # "tour", "assets", "streaming"
    target_platforms: List[str] = ["webxr", "quest", "pcvr"]
    compression_level: str = "medium"  # "low", "medium", "high", "maximum"
    include_lightmaps: bool = True
    include_navmesh: bool = True
    streaming_enabled: bool = False
    metadata: Dict[str, Any] = {}


class AssetOptimizationRequest(BaseModel):
    """Request model for asset optimization."""
    asset_ids: List[str]
    tenant_id: str
    optimization_preset: str = "balanced"  # "quality", "balanced", "performance"
    target_platforms: List[str] = ["webxr"]
    max_texture_size: int = 2048
    mesh_decimation: float = 0.8  # Keep 80% of vertices


class BundleResponse(BaseModel):
    """Response model for bundle operations."""
    bundle_id: str
    status: str
    message: str
    bundle_size_mb: float = 0.0
    asset_count: int = 0
    processing_time_ms: int = 0


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bundle-worker"}


@app.post("/bundles/create", response_model=BundleResponse)
async def create_bundle(
    background_tasks: BackgroundTasks,
    request: BundleRequest
):
    """
    Create a tour bundle with optimized assets.
    
    Generates compressed, optimized bundles for different platforms:
    - WebXR: Lightweight, streaming-optimized
    - Quest: Mobile VR optimized
    - PCVR: High-quality desktop VR
    """
    try:
        # Start bundle creation in background
        background_tasks.add_task(
            processor.create_bundle,
            request
        )
        
        return BundleResponse(
            bundle_id="pending",
            status="accepted",
            message="Bundle creation started"
        )
        
    except Exception as e:
        logger.error(f"Error creating bundle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/optimize")
async def optimize_assets(
    background_tasks: BackgroundTasks,
    request: AssetOptimizationRequest
):
    """
    Optimize assets for specific platforms and performance targets.
    
    Applies compression, mesh decimation, texture optimization, etc.
    """
    try:
        # Start optimization in background
        background_tasks.add_task(
            processor.optimize_assets,
            request
        )
        
        return {
            "status": "accepted",
            "message": "Asset optimization started",
            "asset_count": len(request.asset_ids)
        }
        
    except Exception as e:
        logger.error(f"Error optimizing assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/navmesh/generate")
async def generate_navmesh(
    background_tasks: BackgroundTasks,
    site_id: str,
    tenant_id: str,
    agent_radius: float = 0.3,
    agent_height: float = 1.8,
    max_slope: float = 45.0
):
    """
    Generate navigation mesh for VR locomotion.
    
    Creates walkable areas and navigation paths for teleportation and smooth locomotion.
    """
    try:
        # Start navmesh generation in background
        background_tasks.add_task(
            processor.generate_navmesh,
            site_id,
            tenant_id,
            {
                "agent_radius": agent_radius,
                "agent_height": agent_height,
                "max_slope": max_slope
            }
        )
        
        return {
            "status": "accepted",
            "message": "Navmesh generation started",
            "site_id": site_id
        }
        
    except Exception as e:
        logger.error(f"Error generating navmesh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/lightmaps/bake")
async def bake_lightmaps(
    background_tasks: BackgroundTasks,
    site_id: str,
    tenant_id: str,
    quality: str = "medium",  # "low", "medium", "high", "ultra"
    resolution: int = 512,
    samples: int = 256
):
    """
    Bake lightmaps and light probes for realistic lighting.
    
    Pre-computes lighting information for better performance and visual quality.
    """
    try:
        # Start lightmap baking in background
        background_tasks.add_task(
            processor.bake_lightmaps,
            site_id,
            tenant_id,
            {
                "quality": quality,
                "resolution": resolution,
                "samples": samples
            }
        )
        
        return {
            "status": "accepted",
            "message": "Lightmap baking started",
            "site_id": site_id,
            "quality": quality
        }
        
    except Exception as e:
        logger.error(f"Error baking lightmaps: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/{format}")
async def export_format(
    background_tasks: BackgroundTasks,
    format: str,  # "gltf", "usdz", "fbx", "obj"
    site_id: str,
    tenant_id: str,
    include_animations: bool = True,
    include_materials: bool = True,
    embed_textures: bool = False
):
    """
    Export site to different 3D formats.
    
    Supports glTF, USDZ, FBX, OBJ for cross-platform compatibility.
    """
    try:
        if format.lower() not in ["gltf", "usdz", "fbx", "obj"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Start export in background
        background_tasks.add_task(
            processor.export_format,
            site_id,
            tenant_id,
            format.lower(),
            {
                "include_animations": include_animations,
                "include_materials": include_materials,
                "embed_textures": embed_textures
            }
        )
        
        return {
            "status": "accepted",
            "message": f"Export to {format.upper()} started",
            "site_id": site_id,
            "format": format.upper()
        }
        
    except Exception as e:
        logger.error(f"Error exporting to {format}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bundles/{bundle_id}/status")
async def get_bundle_status(bundle_id: str):
    """Get the status of a bundle creation process."""
    try:
        status = await processor.get_bundle_status(bundle_id)
        return status
    except Exception as e:
        logger.error(f"Error getting bundle status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bundles/{bundle_id}/download")
async def download_bundle(bundle_id: str, tenant_id: str):
    """Get download URL for a completed bundle."""
    try:
        download_info = await processor.get_bundle_download(bundle_id, tenant_id)
        return download_info
    except Exception as e:
        logger.error(f"Error getting bundle download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/streaming/prepare")
async def prepare_streaming(
    background_tasks: BackgroundTasks,
    site_id: str,
    tenant_id: str,
    chunk_size_mb: float = 10.0,
    lod_levels: int = 3
):
    """
    Prepare assets for streaming delivery.
    
    Chunks assets into streamable segments with progressive loading.
    """
    try:
        # Start streaming preparation in background
        background_tasks.add_task(
            processor.prepare_streaming,
            site_id,
            tenant_id,
            {
                "chunk_size_mb": chunk_size_mb,
                "lod_levels": lod_levels
            }
        )
        
        return {
            "status": "accepted",
            "message": "Streaming preparation started",
            "site_id": site_id
        }
        
    except Exception as e:
        logger.error(f"Error preparing streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/bundles/{bundle_id}")
async def delete_bundle(bundle_id: str, tenant_id: str):
    """Delete a bundle and its associated files."""
    try:
        await processor.delete_bundle(bundle_id, tenant_id)
        return {"status": "deleted", "bundle_id": bundle_id}
    except Exception as e:
        logger.error(f"Error deleting bundle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
