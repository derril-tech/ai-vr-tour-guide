"""
Level of Detail (LOD) manager for adaptive overlay rendering.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class LODManager:
    """Manages Level of Detail for 3D overlays and anchors."""
    
    def __init__(self):
        self.lod_distances = [5.0, 15.0, 50.0]  # Distance thresholds for LOD levels
        self.complexity_thresholds = [1000, 5000, 20000]  # Vertex count thresholds
        
    async def initialize(self):
        """Initialize the LOD manager."""
        logger.info("LOD manager initialized")
        
    async def calculate_lod(
        self, 
        position: List[float], 
        anchor_type: str,
        content: Dict[str, Any]
    ) -> int:
        """
        Calculate appropriate LOD level for an anchor.
        
        Args:
            position: Anchor position [x, y, z]
            anchor_type: Type of anchor
            content: Anchor content data
            
        Returns:
            LOD level (0 = highest detail, higher = lower detail)
        """
        try:
            # Base LOD on anchor type
            type_lod_map = {
                "hotspot": 0,  # Always high detail
                "label": 1,    # Medium detail
                "ghost_reconstruction": 2,  # Can be lower detail
                "timeline": 1,  # Medium detail
                "heatmap": 2   # Lower detail acceptable
            }
            
            base_lod = type_lod_map.get(anchor_type, 1)
            
            # Adjust based on content complexity
            content_complexity = self._calculate_content_complexity(content)
            
            if content_complexity > self.complexity_thresholds[2]:
                base_lod = max(base_lod, 2)
            elif content_complexity > self.complexity_thresholds[1]:
                base_lod = max(base_lod, 1)
            
            # Consider position importance (center of scene = higher detail)
            position_importance = self._calculate_position_importance(position)
            if position_importance > 0.8:
                base_lod = max(0, base_lod - 1)
            elif position_importance < 0.3:
                base_lod = min(2, base_lod + 1)
            
            return base_lod
            
        except Exception as e:
            logger.error(f"Error calculating LOD: {str(e)}")
            return 1  # Default to medium detail
            
    async def generate_lod_versions(
        self, 
        geometry: Dict[str, Any], 
        lod_levels: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate multiple LOD versions of geometry.
        
        Args:
            geometry: Original high-detail geometry
            lod_levels: Number of LOD levels to generate
            
        Returns:
            Dictionary mapping LOD level to geometry data
        """
        try:
            logger.info(f"Generating {lod_levels} LOD versions")
            
            lod_versions = {}
            
            # LOD 0 is the original geometry
            lod_versions["0"] = {
                "geometry": geometry,
                "vertex_count": geometry.get("vertex_count", 0),
                "triangle_count": geometry.get("triangle_count", 0),
                "detail_level": "high"
            }
            
            # Generate progressively lower detail versions
            for lod_level in range(1, lod_levels):
                simplified_geometry = await self._simplify_geometry(
                    geometry, lod_level
                )
                
                lod_versions[str(lod_level)] = {
                    "geometry": simplified_geometry,
                    "vertex_count": simplified_geometry.get("vertex_count", 0),
                    "triangle_count": simplified_geometry.get("triangle_count", 0),
                    "detail_level": self._get_detail_level_name(lod_level),
                    "reduction_factor": self._get_reduction_factor(lod_level)
                }
            
            return lod_versions
            
        except Exception as e:
            logger.error(f"Error generating LOD versions: {str(e)}")
            return {"0": {"geometry": geometry, "detail_level": "high"}}
            
    async def generate_lod_level(
        self, 
        geometry: Dict[str, Any], 
        lod_level: int
    ) -> Dict[str, Any]:
        """Generate a specific LOD level on demand."""
        try:
            if lod_level == 0:
                return {
                    "geometry": geometry,
                    "vertex_count": geometry.get("vertex_count", 0),
                    "triangle_count": geometry.get("triangle_count", 0),
                    "detail_level": "high"
                }
            
            simplified_geometry = await self._simplify_geometry(geometry, lod_level)
            
            return {
                "geometry": simplified_geometry,
                "vertex_count": simplified_geometry.get("vertex_count", 0),
                "triangle_count": simplified_geometry.get("triangle_count", 0),
                "detail_level": self._get_detail_level_name(lod_level),
                "reduction_factor": self._get_reduction_factor(lod_level)
            }
            
        except Exception as e:
            logger.error(f"Error generating LOD level {lod_level}: {str(e)}")
            return {"geometry": geometry, "detail_level": "high"}
            
    def _calculate_content_complexity(self, content: Dict[str, Any]) -> int:
        """Calculate complexity score for content."""
        complexity = 0
        
        # Count vertices/triangles if available
        if "vertices" in content:
            complexity += len(content["vertices"])
        
        if "faces" in content:
            complexity += len(content["faces"]) * 3  # Triangles
        
        # Consider texture complexity
        textures = content.get("textures", [])
        for texture in textures:
            if isinstance(texture, dict):
                width = texture.get("width", 512)
                height = texture.get("height", 512)
                complexity += (width * height) // 1000  # Normalize texture size
        
        # Consider animation complexity
        animations = content.get("animations", [])
        complexity += len(animations) * 100
        
        # Consider material complexity
        materials = content.get("materials", {})
        complexity += len(materials) * 50
        
        return complexity
        
    def _calculate_position_importance(self, position: List[float]) -> float:
        """
        Calculate importance score for a position.
        
        Positions near the center or key areas are more important.
        """
        pos = np.array(position)
        
        # Distance from origin (center importance)
        distance_from_center = np.linalg.norm(pos)
        center_importance = max(0, 1.0 - distance_from_center / 20.0)
        
        # Height importance (eye level is more important)
        eye_level = 1.7
        height_importance = max(0, 1.0 - abs(pos[1] - eye_level) / 5.0)
        
        # Combine importance factors
        overall_importance = (center_importance * 0.6 + height_importance * 0.4)
        
        return min(1.0, max(0.0, overall_importance))
        
    async def _simplify_geometry(
        self, 
        geometry: Dict[str, Any], 
        lod_level: int
    ) -> Dict[str, Any]:
        """
        Simplify geometry for a specific LOD level.
        
        This is a simplified implementation. A real system would use
        proper mesh decimation algorithms.
        """
        try:
            reduction_factor = self._get_reduction_factor(lod_level)
            
            simplified = geometry.copy()
            
            # Simplify vertices
            if "vertices" in geometry:
                vertices = geometry["vertices"]
                if isinstance(vertices, list) and len(vertices) > 0:
                    # Simple decimation by sampling
                    step = max(1, int(1.0 / reduction_factor))
                    simplified["vertices"] = vertices[::step]
                    simplified["vertex_count"] = len(simplified["vertices"])
            
            # Simplify faces/triangles
            if "faces" in geometry:
                faces = geometry["faces"]
                if isinstance(faces, list) and len(faces) > 0:
                    step = max(1, int(1.0 / reduction_factor))
                    simplified["faces"] = faces[::step]
                    simplified["triangle_count"] = len(simplified["faces"])
            
            # Simplify textures
            if "textures" in geometry:
                simplified["textures"] = await self._simplify_textures(
                    geometry["textures"], lod_level
                )
            
            # Simplify materials
            if "materials" in geometry:
                simplified["materials"] = self._simplify_materials(
                    geometry["materials"], lod_level
                )
            
            # Remove or simplify complex features for higher LOD levels
            if lod_level >= 2:
                # Remove fine details
                simplified.pop("detail_geometry", None)
                simplified.pop("fine_textures", None)
                
                # Simplify animations
                if "animations" in simplified:
                    animations = simplified["animations"]
                    if len(animations) > 2:
                        simplified["animations"] = animations[:2]  # Keep only main animations
            
            return simplified
            
        except Exception as e:
            logger.error(f"Error simplifying geometry: {str(e)}")
            return geometry
            
    async def _simplify_textures(
        self, 
        textures: List[Dict[str, Any]], 
        lod_level: int
    ) -> List[Dict[str, Any]]:
        """Simplify textures for LOD level."""
        simplified_textures = []
        
        resolution_factors = {
            1: 0.5,   # Half resolution
            2: 0.25,  # Quarter resolution
            3: 0.125  # Eighth resolution
        }
        
        resolution_factor = resolution_factors.get(lod_level, 0.5)
        
        for texture in textures:
            if isinstance(texture, dict):
                simplified_texture = texture.copy()
                
                # Reduce resolution
                if "width" in texture:
                    simplified_texture["width"] = max(64, int(texture["width"] * resolution_factor))
                if "height" in texture:
                    simplified_texture["height"] = max(64, int(texture["height"] * resolution_factor))
                
                # Reduce quality settings
                if lod_level >= 2:
                    simplified_texture["compression"] = "high"
                    simplified_texture["mip_maps"] = False
                
                simplified_textures.append(simplified_texture)
            else:
                simplified_textures.append(texture)
        
        return simplified_textures
        
    def _simplify_materials(
        self, 
        materials: Dict[str, Any], 
        lod_level: int
    ) -> Dict[str, Any]:
        """Simplify materials for LOD level."""
        simplified_materials = {}
        
        for material_name, material_data in materials.items():
            if isinstance(material_data, dict):
                simplified_material = material_data.copy()
                
                # Remove complex material features for higher LOD levels
                if lod_level >= 2:
                    # Remove expensive effects
                    simplified_material.pop("normal_map", None)
                    simplified_material.pop("detail_map", None)
                    simplified_material.pop("parallax_map", None)
                    
                    # Simplify shader
                    if "shader" in simplified_material:
                        simplified_material["shader"] = "simple"
                
                if lod_level >= 3:
                    # Use basic materials only
                    simplified_material = {
                        "color": material_data.get("color", [1, 1, 1]),
                        "shader": "unlit"
                    }
                
                simplified_materials[material_name] = simplified_material
            else:
                simplified_materials[material_name] = material_data
        
        return simplified_materials
        
    def _get_reduction_factor(self, lod_level: int) -> float:
        """Get geometry reduction factor for LOD level."""
        reduction_factors = {
            0: 1.0,   # No reduction
            1: 0.6,   # 60% of original
            2: 0.3,   # 30% of original
            3: 0.15,  # 15% of original
            4: 0.05   # 5% of original
        }
        
        return reduction_factors.get(lod_level, 0.3)
        
    def _get_detail_level_name(self, lod_level: int) -> str:
        """Get human-readable detail level name."""
        level_names = {
            0: "high",
            1: "medium",
            2: "low",
            3: "very_low",
            4: "minimal"
        }
        
        return level_names.get(lod_level, "medium")
        
    def calculate_dynamic_lod(
        self, 
        anchor_position: List[float],
        viewer_position: List[float],
        performance_budget: Dict[str, Any]
    ) -> int:
        """
        Calculate dynamic LOD based on viewer distance and performance.
        
        Args:
            anchor_position: Position of the anchor
            viewer_position: Current viewer position
            performance_budget: Available performance budget
            
        Returns:
            Appropriate LOD level
        """
        try:
            # Calculate distance
            distance = np.linalg.norm(
                np.array(anchor_position) - np.array(viewer_position)
            )
            
            # Base LOD on distance
            lod_level = 0
            for i, threshold in enumerate(self.lod_distances):
                if distance > threshold:
                    lod_level = i + 1
                else:
                    break
            
            # Adjust based on performance budget
            gpu_usage = performance_budget.get("gpu_usage", 0.5)
            frame_time = performance_budget.get("frame_time_ms", 16.0)
            
            # If performance is poor, increase LOD level (lower detail)
            if gpu_usage > 0.8 or frame_time > 20.0:
                lod_level = min(4, lod_level + 1)
            elif gpu_usage < 0.4 and frame_time < 12.0:
                lod_level = max(0, lod_level - 1)
            
            return lod_level
            
        except Exception as e:
            logger.error(f"Error calculating dynamic LOD: {str(e)}")
            return 1
            
    def get_lod_statistics(self, lod_versions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about LOD versions."""
        stats = {
            "lod_count": len(lod_versions),
            "total_vertices": 0,
            "total_triangles": 0,
            "memory_usage_mb": 0,
            "lod_breakdown": {}
        }
        
        for lod_level, lod_data in lod_versions.items():
            vertex_count = lod_data.get("vertex_count", 0)
            triangle_count = lod_data.get("triangle_count", 0)
            
            stats["total_vertices"] += vertex_count
            stats["total_triangles"] += triangle_count
            
            # Estimate memory usage (rough calculation)
            vertex_memory = vertex_count * 32  # 32 bytes per vertex (position + normal + uv)
            triangle_memory = triangle_count * 12  # 12 bytes per triangle (3 indices)
            texture_memory = len(lod_data.get("textures", [])) * 1024 * 1024  # 1MB per texture estimate
            
            lod_memory = (vertex_memory + triangle_memory + texture_memory) / (1024 * 1024)
            stats["memory_usage_mb"] += lod_memory
            
            stats["lod_breakdown"][lod_level] = {
                "vertices": vertex_count,
                "triangles": triangle_count,
                "memory_mb": lod_memory,
                "detail_level": lod_data.get("detail_level", "unknown")
            }
        
        return stats
