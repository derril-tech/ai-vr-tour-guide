"""
Occlusion management for 3D anchor visibility.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class OcclusionManager:
    """Manages occlusion detection and visibility optimization."""
    
    def __init__(self):
        self.ray_samples = 32  # Number of rays for occlusion testing
        self.visibility_threshold = 0.3  # Minimum visibility required
        
    async def initialize(self):
        """Initialize the occlusion manager."""
        logger.info("Occlusion manager initialized")
        
    async def analyze_occlusion(
        self, 
        position: List[float], 
        site_geometry: Dict[str, Any],
        anchor_type: str
    ) -> Dict[str, Any]:
        """
        Analyze occlusion for a position from multiple viewpoints.
        
        Args:
            position: Position to analyze [x, y, z]
            site_geometry: 3D geometry data
            anchor_type: Type of anchor (affects analysis parameters)
            
        Returns:
            Occlusion analysis results
        """
        try:
            logger.debug(f"Analyzing occlusion for position {position}")
            
            # Generate viewpoints around the position
            viewpoints = self._generate_viewpoints(position, anchor_type)
            
            # Test visibility from each viewpoint
            visibility_results = []
            for viewpoint in viewpoints:
                visibility = await self._test_visibility(
                    position, viewpoint, site_geometry
                )
                visibility_results.append({
                    "viewpoint": viewpoint,
                    "visibility": visibility["visible"],
                    "occlusion_factor": visibility["occlusion_factor"],
                    "blocking_objects": visibility.get("blocking_objects", [])
                })
            
            # Calculate overall occlusion metrics
            total_visible = sum(1 for r in visibility_results if r["visibility"])
            visibility_percentage = (total_visible / len(visibility_results)) * 100
            
            average_occlusion = np.mean([r["occlusion_factor"] for r in visibility_results])
            
            # Find best viewing angles
            best_viewpoints = sorted(
                visibility_results, 
                key=lambda x: x["occlusion_factor"]
            )[:3]
            
            # Generate recommendations if visibility is poor
            recommendations = []
            if visibility_percentage < 50:
                recommendations = await self._generate_visibility_recommendations(
                    position, site_geometry, visibility_results
                )
            
            return {
                "position": position,
                "visibility_percentage": visibility_percentage,
                "average_occlusion": average_occlusion,
                "viewpoint_count": len(viewpoints),
                "visible_viewpoints": total_visible,
                "best_viewpoints": best_viewpoints,
                "visibility_results": visibility_results,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing occlusion: {str(e)}")
            return {
                "position": position,
                "visibility_percentage": 0,
                "average_occlusion": 1.0,
                "error": str(e)
            }
            
    async def check_occlusion(
        self, 
        anchor_position: List[float], 
        viewpoint: List[float],
        site_geometry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check occlusion between a specific anchor and viewpoint.
        
        Args:
            anchor_position: Position of the anchor [x, y, z]
            viewpoint: Viewer position [x, y, z]
            site_geometry: 3D geometry data
            
        Returns:
            Occlusion check results
        """
        try:
            # Cast ray from viewpoint to anchor
            ray_result = await self._cast_ray(
                viewpoint, anchor_position, site_geometry
            )
            
            # Calculate visibility metrics
            distance = np.linalg.norm(
                np.array(anchor_position) - np.array(viewpoint)
            )
            
            # Check if ray hits the anchor or is blocked
            is_visible = ray_result["hit_target"]
            occlusion_factor = ray_result["occlusion_factor"]
            
            # Generate alternative position if heavily occluded
            recommended_position = None
            if occlusion_factor > 0.7:
                recommended_position = await self._find_alternative_position(
                    anchor_position, viewpoint, site_geometry
                )
            
            return {
                "anchor_position": anchor_position,
                "viewpoint": viewpoint,
                "distance": distance,
                "visible": is_visible,
                "score": 1.0 - occlusion_factor,
                "occlusion_factor": occlusion_factor,
                "blocking_objects": ray_result.get("blocking_objects", []),
                "recommended_position": recommended_position,
                "visibility_percentage": (1.0 - occlusion_factor) * 100
            }
            
        except Exception as e:
            logger.error(f"Error checking occlusion: {str(e)}")
            return {
                "anchor_position": anchor_position,
                "viewpoint": viewpoint,
                "visible": False,
                "score": 0.0,
                "error": str(e)
            }
            
    def _generate_viewpoints(self, position: List[float], anchor_type: str) -> List[List[float]]:
        """Generate viewpoints around a position for occlusion testing."""
        pos = np.array(position)
        viewpoints = []
        
        # Parameters based on anchor type
        type_params = {
            "hotspot": {"radius": 5.0, "height_offset": 0.0, "angles": 8},
            "label": {"radius": 3.0, "height_offset": 0.2, "angles": 6},
            "ghost_reconstruction": {"radius": 10.0, "height_offset": 2.0, "angles": 12},
            "timeline": {"radius": 4.0, "height_offset": 0.5, "angles": 6}
        }
        
        params = type_params.get(anchor_type, {"radius": 5.0, "height_offset": 0.0, "angles": 8})
        
        # Generate circular viewpoints
        for i in range(params["angles"]):
            angle = (2 * np.pi * i) / params["angles"]
            
            # Calculate viewpoint position
            x = pos[0] + params["radius"] * np.cos(angle)
            z = pos[2] + params["radius"] * np.sin(angle)
            y = pos[1] + params["height_offset"]
            
            viewpoints.append([float(x), float(y), float(z)])
        
        # Add elevated viewpoints
        for i in range(params["angles"] // 2):
            angle = (2 * np.pi * i) / (params["angles"] // 2)
            
            x = pos[0] + (params["radius"] * 0.7) * np.cos(angle)
            z = pos[2] + (params["radius"] * 0.7) * np.sin(angle)
            y = pos[1] + 2.0  # Elevated view
            
            viewpoints.append([float(x), float(y), float(z)])
        
        return viewpoints
        
    async def _test_visibility(
        self, 
        target_position: List[float], 
        viewpoint: List[float],
        site_geometry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test visibility between target and viewpoint."""
        # Cast ray from viewpoint to target
        ray_result = await self._cast_ray(viewpoint, target_position, site_geometry)
        
        return {
            "visible": ray_result["hit_target"],
            "occlusion_factor": ray_result["occlusion_factor"],
            "blocking_objects": ray_result.get("blocking_objects", [])
        }
        
    async def _cast_ray(
        self, 
        origin: List[float], 
        target: List[float],
        site_geometry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cast a ray from origin to target and check for intersections.
        
        This is a simplified implementation. A real system would use
        proper 3D ray-mesh intersection algorithms.
        """
        origin_np = np.array(origin)
        target_np = np.array(target)
        
        # Calculate ray direction and distance
        direction = target_np - origin_np
        distance = np.linalg.norm(direction)
        
        if distance == 0:
            return {"hit_target": True, "occlusion_factor": 0.0}
        
        direction_normalized = direction / distance
        
        # Simplified occlusion test using bounding boxes
        collision_mesh = site_geometry.get("collision_mesh", [])
        blocking_objects = []
        occlusion_factor = 0.0
        
        # Sample points along the ray
        sample_count = 10
        for i in range(1, sample_count):
            t = i / sample_count
            sample_point = origin_np + t * direction
            
            # Check if sample point is inside any collision geometry
            if self._point_in_collision_mesh(sample_point.tolist(), collision_mesh):
                occlusion_factor += 1.0 / sample_count
                blocking_objects.append(f"collision_object_{i}")
        
        # Additional occlusion based on distance and geometry complexity
        bounds = site_geometry.get("bounds", {"min": [-50, -10, -50], "max": [50, 10, 50]})
        geometry_complexity = len(collision_mesh) / 100.0  # Normalize
        distance_factor = min(1.0, distance / 20.0)  # Normalize distance
        
        # Add environmental occlusion
        environmental_occlusion = geometry_complexity * distance_factor * 0.2
        occlusion_factor = min(1.0, occlusion_factor + environmental_occlusion)
        
        hit_target = occlusion_factor < 0.8  # Target is visible if not heavily occluded
        
        return {
            "hit_target": hit_target,
            "occlusion_factor": occlusion_factor,
            "distance": distance,
            "blocking_objects": blocking_objects
        }
        
    def _point_in_collision_mesh(self, point: List[float], collision_mesh: List[Dict]) -> bool:
        """Check if a point is inside collision geometry."""
        # Simplified point-in-mesh test
        # Real implementation would use proper 3D point-in-polygon tests
        
        for mesh_object in collision_mesh:
            bounds = mesh_object.get("bounds")
            if bounds:
                min_bounds = bounds.get("min", [-1, -1, -1])
                max_bounds = bounds.get("max", [1, 1, 1])
                
                if (min_bounds[0] <= point[0] <= max_bounds[0] and
                    min_bounds[1] <= point[1] <= max_bounds[1] and
                    min_bounds[2] <= point[2] <= max_bounds[2]):
                    return True
        
        return False
        
    async def _generate_visibility_recommendations(
        self,
        position: List[float],
        site_geometry: Dict[str, Any],
        visibility_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations to improve visibility."""
        recommendations = []
        
        # Find the best visible viewpoints
        best_viewpoints = [r for r in visibility_results if r["visibility"]]
        
        if best_viewpoints:
            # Recommend moving towards better visibility
            best_viewpoint = min(best_viewpoints, key=lambda x: x["occlusion_factor"])
            
            # Calculate suggested position adjustment
            current_pos = np.array(position)
            best_view_pos = np.array(best_viewpoint["viewpoint"])
            
            # Move slightly towards the best viewpoint
            adjustment_vector = (best_view_pos - current_pos) * 0.3
            suggested_position = (current_pos + adjustment_vector).tolist()
            
            recommendations.append({
                "type": "position_adjustment",
                "description": "Move anchor towards better visibility",
                "suggested_position": suggested_position,
                "expected_improvement": 0.3
            })
        
        # Recommend height adjustment
        avg_occlusion = np.mean([r["occlusion_factor"] for r in visibility_results])
        if avg_occlusion > 0.6:
            height_adjustment = 1.0 if position[1] < 3.0 else -0.5
            adjusted_position = position.copy()
            adjusted_position[1] += height_adjustment
            
            recommendations.append({
                "type": "height_adjustment",
                "description": f"Adjust height by {height_adjustment}m",
                "suggested_position": adjusted_position,
                "expected_improvement": 0.2
            })
        
        return recommendations
        
    async def _find_alternative_position(
        self,
        anchor_position: List[float],
        viewpoint: List[float],
        site_geometry: Dict[str, Any]
    ) -> Optional[List[float]]:
        """Find an alternative position with better visibility."""
        anchor_pos = np.array(anchor_position)
        view_pos = np.array(viewpoint)
        
        # Try positions in a small radius around the original
        search_radius = 2.0
        best_position = None
        best_visibility = 0.0
        
        # Sample positions in a circle
        for angle in np.linspace(0, 2 * np.pi, 8):
            for radius in [0.5, 1.0, 1.5]:
                # Calculate candidate position
                offset_x = radius * np.cos(angle)
                offset_z = radius * np.sin(angle)
                
                candidate_pos = anchor_pos + np.array([offset_x, 0, offset_z])
                
                # Test visibility from viewpoint
                ray_result = await self._cast_ray(
                    viewpoint, candidate_pos.tolist(), site_geometry
                )
                
                visibility_score = 1.0 - ray_result["occlusion_factor"]
                
                if visibility_score > best_visibility:
                    best_visibility = visibility_score
                    best_position = candidate_pos.tolist()
        
        return best_position if best_visibility > 0.5 else None
        
    def calculate_visibility_heatmap(
        self,
        site_geometry: Dict[str, Any],
        grid_resolution: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate a visibility heatmap for the entire site.
        
        This shows which areas have good visibility for anchor placement.
        """
        bounds = site_geometry.get("bounds", {"min": [-10, 0, -10], "max": [10, 5, 10]})
        
        # Create grid
        x_range = np.arange(bounds["min"][0], bounds["max"][0], grid_resolution)
        z_range = np.arange(bounds["min"][2], bounds["max"][2], grid_resolution)
        
        heatmap_data = []
        
        for x in x_range:
            for z in z_range:
                position = [float(x), 1.8, float(z)]  # Standard height
                
                # Calculate visibility score for this position
                viewpoints = self._generate_viewpoints(position, "hotspot")
                visibility_scores = []
                
                for viewpoint in viewpoints:
                    # Simplified visibility calculation
                    distance = np.linalg.norm(
                        np.array(position) - np.array(viewpoint)
                    )
                    
                    # Simple distance-based visibility (placeholder)
                    visibility = max(0, 1.0 - distance / 10.0)
                    visibility_scores.append(visibility)
                
                avg_visibility = np.mean(visibility_scores)
                
                heatmap_data.append({
                    "position": position,
                    "visibility_score": avg_visibility,
                    "grid_x": float(x),
                    "grid_z": float(z)
                })
        
        return {
            "heatmap_data": heatmap_data,
            "grid_resolution": grid_resolution,
            "bounds": bounds,
            "max_visibility": max(d["visibility_score"] for d in heatmap_data),
            "min_visibility": min(d["visibility_score"] for d in heatmap_data)
        }
