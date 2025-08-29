"""
Core bundle processor that orchestrates asset compression and bundle generation.
"""

import asyncio
import logging
import json
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from pathlib import Path

from .asset_compressor import AssetCompressor
from .navmesh_baker import NavmeshBaker
from .lightmap_baker import LightmapBaker
from .format_exporter import FormatExporter
from ..shared.database import Database
from ..shared.nats_client import NATSClient
from ..shared.storage import StorageClient
from ..shared.config import Settings

logger = logging.getLogger(__name__)


class BundleProcessor:
    """Main processor for bundle generation and asset optimization."""
    
    def __init__(self, db: Database, nats: NATSClient, storage: StorageClient, settings: Settings):
        self.db = db
        self.nats = nats
        self.storage = storage
        self.settings = settings
        
        # Initialize specialized processors
        self.asset_compressor = AssetCompressor()
        self.navmesh_baker = NavmeshBaker()
        self.lightmap_baker = LightmapBaker()
        self.format_exporter = FormatExporter()
        
        # Processing status cache
        self.bundle_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the processor."""
        logger.info("Initializing bundle processor")
        
        # Subscribe to NATS topics
        await self.nats.subscribe("bundle.create", self._handle_bundle_message)
        await self.nats.subscribe("asset.optimize", self._handle_asset_message)
        
        # Initialize sub-processors
        await self.asset_compressor.initialize()
        await self.navmesh_baker.initialize()
        await self.lightmap_baker.initialize()
        await self.format_exporter.initialize()
        
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up bundle processor")
        
    async def create_bundle(self, request) -> Dict[str, Any]:
        """Create a tour bundle with optimized assets."""
        bundle_id = str(uuid4())
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Creating {request.bundle_type} bundle {bundle_id} for site {request.site_id}")
            
            # Update status
            self.bundle_status[bundle_id] = {
                "status": "processing",
                "stage": "initialization",
                "start_time": start_time,
                "site_id": request.site_id,
                "bundle_type": request.bundle_type
            }
            
            # Get site assets
            assets = await self._get_site_assets(request.site_id, request.tenant_id)
            
            # Optimize assets for target platforms
            self.bundle_status[bundle_id]["stage"] = "asset_optimization"
            optimized_assets = await self._optimize_assets_for_bundle(
                assets, request.target_platforms, request.compression_level
            )
            
            # Generate navmesh if requested
            navmesh_data = None
            if request.include_navmesh:
                self.bundle_status[bundle_id]["stage"] = "navmesh_generation"
                navmesh_data = await self.navmesh_baker.generate_navmesh(
                    request.site_id, assets
                )
            
            # Bake lightmaps if requested
            lightmap_data = None
            if request.include_lightmaps:
                self.bundle_status[bundle_id]["stage"] = "lightmap_baking"
                lightmap_data = await self.lightmap_baker.bake_lightmaps(
                    request.site_id, assets
                )
            
            # Create bundle package
            self.bundle_status[bundle_id]["stage"] = "packaging"
            bundle_data = await self._create_bundle_package(
                bundle_id,
                request,
                optimized_assets,
                navmesh_data,
                lightmap_data
            )
            
            # Upload bundle to storage
            self.bundle_status[bundle_id]["stage"] = "uploading"
            bundle_url = await self._upload_bundle(bundle_id, bundle_data, request.tenant_id)
            
            # Save bundle metadata
            await self._save_bundle_metadata(bundle_id, request, bundle_data, bundle_url)
            
            # Update final status
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.bundle_status[bundle_id] = {
                "status": "completed",
                "stage": "done",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "processing_time_ms": processing_time,
                "bundle_size_mb": bundle_data["size_mb"],
                "asset_count": len(optimized_assets),
                "download_url": bundle_url
            }
            
            # Publish completion event
            await self.nats.publish("bundle.completed", {
                "bundle_id": bundle_id,
                "site_id": request.site_id,
                "tenant_id": request.tenant_id,
                "bundle_type": request.bundle_type,
                "size_mb": bundle_data["size_mb"]
            })
            
            logger.info(f"Bundle {bundle_id} created successfully in {processing_time}ms")
            
            return {
                "bundle_id": bundle_id,
                "status": "completed",
                "bundle_size_mb": bundle_data["size_mb"],
                "asset_count": len(optimized_assets),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error creating bundle {bundle_id}: {str(e)}")
            
            # Update error status
            self.bundle_status[bundle_id] = {
                "status": "error",
                "stage": "failed",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "error": str(e)
            }
            
            raise e
            
    async def optimize_assets(self, request):
        """Optimize assets for specific platforms."""
        try:
            logger.info(f"Optimizing {len(request.asset_ids)} assets")
            
            # Get asset data
            assets = []
            for asset_id in request.asset_ids:
                asset = await self._get_asset(asset_id, request.tenant_id)
                if asset:
                    assets.append(asset)
            
            # Apply optimization based on preset
            optimization_settings = self._get_optimization_settings(
                request.optimization_preset,
                request.target_platforms
            )
            
            optimized_count = 0
            for asset in assets:
                try:
                    optimized_asset = await self.asset_compressor.optimize_asset(
                        asset, optimization_settings
                    )
                    
                    # Update asset in storage
                    await self._update_asset(asset["id"], optimized_asset)
                    optimized_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to optimize asset {asset['id']}: {str(e)}")
            
            # Publish optimization complete event
            await self.nats.publish("assets.optimized", {
                "asset_ids": request.asset_ids,
                "tenant_id": request.tenant_id,
                "optimized_count": optimized_count,
                "preset": request.optimization_preset
            })
            
            logger.info(f"Asset optimization completed: {optimized_count}/{len(assets)} assets")
            
        except Exception as e:
            logger.error(f"Error optimizing assets: {str(e)}")
            raise e
            
    async def generate_navmesh(self, site_id: str, tenant_id: str, parameters: Dict[str, Any]):
        """Generate navigation mesh for a site."""
        try:
            logger.info(f"Generating navmesh for site {site_id}")
            
            # Get site geometry
            site_assets = await self._get_site_assets(site_id, tenant_id)
            
            # Generate navmesh
            navmesh_data = await self.navmesh_baker.generate_navmesh(
                site_id, site_assets, parameters
            )
            
            # Save navmesh data
            await self._save_navmesh(site_id, tenant_id, navmesh_data)
            
            # Publish navmesh generated event
            await self.nats.publish("navmesh.generated", {
                "site_id": site_id,
                "tenant_id": tenant_id,
                "triangle_count": navmesh_data.get("triangle_count", 0)
            })
            
            logger.info(f"Navmesh generated for site {site_id}")
            
        except Exception as e:
            logger.error(f"Error generating navmesh: {str(e)}")
            raise e
            
    async def bake_lightmaps(self, site_id: str, tenant_id: str, parameters: Dict[str, Any]):
        """Bake lightmaps for a site."""
        try:
            logger.info(f"Baking lightmaps for site {site_id}")
            
            # Get site assets
            site_assets = await self._get_site_assets(site_id, tenant_id)
            
            # Bake lightmaps
            lightmap_data = await self.lightmap_baker.bake_lightmaps(
                site_id, site_assets, parameters
            )
            
            # Save lightmap data
            await self._save_lightmaps(site_id, tenant_id, lightmap_data)
            
            # Publish lightmaps baked event
            await self.nats.publish("lightmaps.baked", {
                "site_id": site_id,
                "tenant_id": tenant_id,
                "lightmap_count": len(lightmap_data.get("lightmaps", []))
            })
            
            logger.info(f"Lightmaps baked for site {site_id}")
            
        except Exception as e:
            logger.error(f"Error baking lightmaps: {str(e)}")
            raise e
            
    async def export_format(self, site_id: str, tenant_id: str, format: str, options: Dict[str, Any]):
        """Export site to a specific 3D format."""
        try:
            logger.info(f"Exporting site {site_id} to {format.upper()}")
            
            # Get site assets
            site_assets = await self._get_site_assets(site_id, tenant_id)
            
            # Export to format
            exported_data = await self.format_exporter.export_format(
                site_id, site_assets, format, options
            )
            
            # Save exported file
            export_id = str(uuid4())
            file_key = f"exports/{tenant_id}/{site_id}/{export_id}.{format}"
            
            await self.storage.upload_file(
                file_key, 
                exported_data["file_data"], 
                exported_data["content_type"]
            )
            
            # Publish export complete event
            await self.nats.publish("format.exported", {
                "site_id": site_id,
                "tenant_id": tenant_id,
                "format": format,
                "export_id": export_id,
                "file_size": len(exported_data["file_data"])
            })
            
            logger.info(f"Site {site_id} exported to {format.upper()}")
            
        except Exception as e:
            logger.error(f"Error exporting to {format}: {str(e)}")
            raise e
            
    async def prepare_streaming(self, site_id: str, tenant_id: str, parameters: Dict[str, Any]):
        """Prepare assets for streaming delivery."""
        try:
            logger.info(f"Preparing streaming for site {site_id}")
            
            # Get site assets
            site_assets = await self._get_site_assets(site_id, tenant_id)
            
            # Create streaming chunks
            streaming_data = await self._create_streaming_chunks(
                site_assets, parameters
            )
            
            # Save streaming manifest
            await self._save_streaming_manifest(site_id, tenant_id, streaming_data)
            
            # Publish streaming ready event
            await self.nats.publish("streaming.prepared", {
                "site_id": site_id,
                "tenant_id": tenant_id,
                "chunk_count": len(streaming_data.get("chunks", []))
            })
            
            logger.info(f"Streaming prepared for site {site_id}")
            
        except Exception as e:
            logger.error(f"Error preparing streaming: {str(e)}")
            raise e
            
    # Helper methods
    
    async def _get_site_assets(self, site_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all assets for a site."""
        # This would query the database for site assets
        # For now, return mock data
        return [
            {
                "id": "asset_1",
                "type": "mesh",
                "name": "main_building.fbx",
                "size_mb": 15.2,
                "format": "fbx"
            },
            {
                "id": "asset_2", 
                "type": "texture",
                "name": "building_diffuse.jpg",
                "size_mb": 8.5,
                "format": "jpg"
            }
        ]
        
    async def _get_asset(self, asset_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific asset."""
        # This would query the database
        return {
            "id": asset_id,
            "tenant_id": tenant_id,
            "type": "mesh",
            "data": {}
        }
        
    async def _optimize_assets_for_bundle(
        self, 
        assets: List[Dict[str, Any]], 
        target_platforms: List[str],
        compression_level: str
    ) -> List[Dict[str, Any]]:
        """Optimize assets for bundle creation."""
        optimized_assets = []
        
        optimization_settings = self._get_optimization_settings(
            compression_level, target_platforms
        )
        
        for asset in assets:
            try:
                optimized_asset = await self.asset_compressor.optimize_asset(
                    asset, optimization_settings
                )
                optimized_assets.append(optimized_asset)
            except Exception as e:
                logger.warning(f"Failed to optimize asset {asset['id']}: {str(e)}")
                # Include original asset if optimization fails
                optimized_assets.append(asset)
        
        return optimized_assets
        
    def _get_optimization_settings(self, preset: str, target_platforms: List[str]) -> Dict[str, Any]:
        """Get optimization settings for a preset and platforms."""
        base_settings = {
            "quality": {
                "texture_compression": "low",
                "mesh_decimation": 0.95,
                "max_texture_size": 4096,
                "audio_bitrate": 320
            },
            "balanced": {
                "texture_compression": "medium",
                "mesh_decimation": 0.8,
                "max_texture_size": 2048,
                "audio_bitrate": 192
            },
            "performance": {
                "texture_compression": "high",
                "mesh_decimation": 0.6,
                "max_texture_size": 1024,
                "audio_bitrate": 128
            }
        }
        
        settings = base_settings.get(preset, base_settings["balanced"])
        
        # Adjust for mobile platforms
        if "quest" in target_platforms:
            settings["max_texture_size"] = min(settings["max_texture_size"], 1024)
            settings["mesh_decimation"] = min(settings["mesh_decimation"], 0.7)
        
        return settings
        
    async def _create_bundle_package(
        self,
        bundle_id: str,
        request,
        assets: List[Dict[str, Any]],
        navmesh_data: Optional[Dict[str, Any]],
        lightmap_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create the bundle package."""
        # Create bundle manifest
        manifest = {
            "bundle_id": bundle_id,
            "version": "1.0",
            "site_id": request.site_id,
            "bundle_type": request.bundle_type,
            "target_platforms": request.target_platforms,
            "created_at": datetime.utcnow().isoformat(),
            "assets": assets,
            "navmesh": navmesh_data,
            "lightmaps": lightmap_data,
            "metadata": request.metadata
        }
        
        # Calculate total size
        total_size_mb = sum(asset.get("size_mb", 0) for asset in assets)
        if navmesh_data:
            total_size_mb += navmesh_data.get("size_mb", 0)
        if lightmap_data:
            total_size_mb += lightmap_data.get("size_mb", 0)
        
        return {
            "manifest": manifest,
            "size_mb": total_size_mb,
            "asset_count": len(assets)
        }
        
    async def _upload_bundle(self, bundle_id: str, bundle_data: Dict[str, Any], tenant_id: str) -> str:
        """Upload bundle to storage."""
        # Create bundle archive (simplified)
        bundle_json = json.dumps(bundle_data["manifest"], indent=2)
        bundle_bytes = bundle_json.encode('utf-8')
        
        # Upload to storage
        file_key = f"bundles/{tenant_id}/{bundle_id}/bundle.json"
        bundle_url = await self.storage.upload_file(
            file_key, bundle_bytes, "application/json"
        )
        
        return bundle_url
        
    async def _save_bundle_metadata(self, bundle_id: str, request, bundle_data: Dict[str, Any], bundle_url: str):
        """Save bundle metadata to database."""
        # This would save to database
        logger.info(f"Saved bundle metadata for {bundle_id}")
        
    async def _create_streaming_chunks(self, assets: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create streaming chunks from assets."""
        chunk_size_mb = parameters.get("chunk_size_mb", 10.0)
        chunks = []
        
        current_chunk = []
        current_size = 0.0
        
        for asset in assets:
            asset_size = asset.get("size_mb", 0)
            
            if current_size + asset_size > chunk_size_mb and current_chunk:
                # Create chunk
                chunks.append({
                    "id": str(uuid4()),
                    "assets": current_chunk,
                    "size_mb": current_size,
                    "priority": len(chunks)  # Earlier chunks have higher priority
                })
                
                current_chunk = [asset]
                current_size = asset_size
            else:
                current_chunk.append(asset)
                current_size += asset_size
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "id": str(uuid4()),
                "assets": current_chunk,
                "size_mb": current_size,
                "priority": len(chunks)
            })
        
        return {
            "chunks": chunks,
            "total_size_mb": sum(chunk["size_mb"] for chunk in chunks),
            "chunk_count": len(chunks)
        }
        
    async def get_bundle_status(self, bundle_id: str) -> Dict[str, Any]:
        """Get bundle processing status."""
        return self.bundle_status.get(bundle_id, {"status": "not_found"})
        
    async def get_bundle_download(self, bundle_id: str, tenant_id: str) -> Dict[str, Any]:
        """Get bundle download information."""
        status = self.bundle_status.get(bundle_id)
        if not status or status["status"] != "completed":
            raise ValueError("Bundle not ready for download")
        
        return {
            "bundle_id": bundle_id,
            "download_url": status.get("download_url"),
            "size_mb": status.get("bundle_size_mb", 0),
            "expires_at": "2024-12-31T23:59:59Z"  # Placeholder
        }
        
    async def delete_bundle(self, bundle_id: str, tenant_id: str):
        """Delete a bundle and its files."""
        # Remove from cache
        if bundle_id in self.bundle_status:
            del self.bundle_status[bundle_id]
        
        # Delete from storage
        file_key = f"bundles/{tenant_id}/{bundle_id}/"
        # This would delete the bundle files
        
        # Publish deletion event
        await self.nats.publish("bundle.deleted", {
            "bundle_id": bundle_id,
            "tenant_id": tenant_id
        })
        
    async def _update_asset(self, asset_id: str, asset_data: Dict[str, Any]):
        """Update asset in database."""
        logger.info(f"Updated asset {asset_id}")
        
    async def _save_navmesh(self, site_id: str, tenant_id: str, navmesh_data: Dict[str, Any]):
        """Save navmesh data."""
        logger.info(f"Saved navmesh for site {site_id}")
        
    async def _save_lightmaps(self, site_id: str, tenant_id: str, lightmap_data: Dict[str, Any]):
        """Save lightmap data."""
        logger.info(f"Saved lightmaps for site {site_id}")
        
    async def _save_streaming_manifest(self, site_id: str, tenant_id: str, streaming_data: Dict[str, Any]):
        """Save streaming manifest."""
        logger.info(f"Saved streaming manifest for site {site_id}")
        
    async def _handle_bundle_message(self, message: Dict[str, Any]):
        """Handle bundle creation messages from NATS."""
        # Handle async bundle requests
        pass
        
    async def _handle_asset_message(self, message: Dict[str, Any]):
        """Handle asset optimization messages from NATS."""
        # Handle async asset optimization requests
        pass
