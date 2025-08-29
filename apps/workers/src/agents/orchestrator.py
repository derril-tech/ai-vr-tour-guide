"""
Tour Orchestrator

Coordinates all agents to provide a seamless, intelligent tour experience.
Manages agent interactions, context sharing, and experience flow.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from .base import BaseAgent, TourContext
from .planner import TourPlannerAgent
from .retriever import KnowledgeRetrieverAgent
from .narrator import NarratorAgent
from .qa_agent import QAAgent

logger = logging.getLogger(__name__)


class TourState(Enum):
    """Tour states for orchestration."""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    Q_AND_A = "q_and_a"
    TRANSITIONING = "transitioning"
    COMPLETED = "completed"
    ERROR = "error"


class TourOrchestrator(BaseAgent):
    """Orchestrates all tour agents for seamless experience delivery."""
    
    def __init__(self):
        super().__init__(
            name="TourOrchestrator",
            description="Coordinates all agents for seamless tour experience"
        )
        
        # Initialize all agents
        self.planner = TourPlannerAgent()
        self.retriever = KnowledgeRetrieverAgent()
        self.narrator = NarratorAgent()
        self.qa_agent = QAAgent()
        
        # Tour state management
        self.active_tours: Dict[str, Dict[str, Any]] = {}
        
        # Agent coordination settings
        self.max_concurrent_operations = 3
        self.context_sharing_enabled = True
        self.adaptive_pacing = True
        
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process orchestration request."""
        try:
            operation = input_data.get("operation", "unknown")
            
            if operation == "start_tour":
                return await self._start_tour(context, input_data)
            elif operation == "continue_tour":
                return await self._continue_tour(context, input_data)
            elif operation == "handle_question":
                return await self._handle_question(context, input_data)
            elif operation == "update_context":
                return await self._update_context(context, input_data)
            elif operation == "pause_tour":
                return await self._pause_tour(context, input_data)
            elif operation == "resume_tour":
                return await self._resume_tour(context, input_data)
            elif operation == "end_tour":
                return await self._end_tour(context, input_data)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            self.logger.error(f"Error in tour orchestration: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recovery_actions": await self._get_recovery_actions(context, input_data)
            }
    
    async def _start_tour(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new tour experience."""
        try:
            self.logger.info(f"Starting tour for session {context.session_id}")
            
            # Initialize tour state
            tour_state = {
                "state": TourState.INITIALIZING,
                "start_time": datetime.utcnow(),
                "context": context,
                "current_waypoint": None,
                "completed_waypoints": [],
                "active_operations": [],
                "shared_context": {},
                "performance_metrics": {
                    "agent_response_times": {},
                    "user_engagement_score": 0.8,
                    "content_relevance_score": 0.8
                }
            }
            
            self.active_tours[context.session_id] = tour_state
            
            # Phase 1: Planning
            tour_state["state"] = TourState.PLANNING
            planning_result = await self.planner.process(context, input_data)
            
            if not planning_result.get("success"):
                tour_state["state"] = TourState.ERROR
                return {
                    "success": False,
                    "error": "Tour planning failed",
                    "details": planning_result
                }
            
            # Store tour plan
            tour_state["tour_plan"] = planning_result["tour_plan"]
            tour_state["shared_context"]["tour_plan"] = planning_result["tour_plan"]
            
            # Phase 2: Initialize first waypoint
            first_waypoint = planning_result["tour_plan"]["waypoints"][0]
            
            # Prepare content for first waypoint
            waypoint_content = await self._prepare_waypoint_content(
                first_waypoint, context, tour_state
            )
            
            # Set tour to active
            tour_state["state"] = TourState.ACTIVE
            tour_state["current_waypoint"] = first_waypoint
            
            return {
                "success": True,
                "tour_id": context.tour_id,
                "session_id": context.session_id,
                "tour_plan": planning_result["tour_plan"],
                "first_waypoint": waypoint_content,
                "estimated_duration": planning_result.get("estimated_duration", 60),
                "state": tour_state["state"].value
            }
            
        except Exception as e:
            self.logger.error(f"Error starting tour: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _continue_tour(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Continue tour to next waypoint or update current experience."""
        try:
            tour_state = self.active_tours.get(context.session_id)
            if not tour_state:
                return {"success": False, "error": "No active tour found"}
            
            action = input_data.get("action", "next_waypoint")
            
            if action == "next_waypoint":
                return await self._advance_to_next_waypoint(context, tour_state, input_data)
            elif action == "update_current":
                return await self._update_current_waypoint(context, tour_state, input_data)
            elif action == "adaptive_adjustment":
                return await self._make_adaptive_adjustment(context, tour_state, input_data)
            else:
                return {"success": False, "error": f"Unknown continue action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error continuing tour: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _advance_to_next_waypoint(
        self, 
        context: TourContext, 
        tour_state: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Advance tour to the next waypoint."""
        
        current_waypoint = tour_state.get("current_waypoint")
        tour_plan = tour_state.get("tour_plan", {})
        waypoints = tour_plan.get("waypoints", [])
        
        # Find current waypoint index
        current_index = -1
        for i, waypoint in enumerate(waypoints):
            if waypoint.get("id") == current_waypoint.get("id"):
                current_index = i
                break
        
        # Check if tour is complete
        if current_index >= len(waypoints) - 1:
            return await self._complete_tour(context, tour_state)
        
        # Get next waypoint
        next_waypoint = waypoints[current_index + 1]
        
        # Mark current waypoint as completed
        if current_waypoint:
            tour_state["completed_waypoints"].append(current_waypoint)
            context.visited_hotspots.append(current_waypoint.get("id", "unknown"))
        
        # Prepare content for next waypoint
        tour_state["state"] = TourState.TRANSITIONING
        waypoint_content = await self._prepare_waypoint_content(
            next_waypoint, context, tour_state
        )
        
        # Update tour state
        tour_state["current_waypoint"] = next_waypoint
        tour_state["state"] = TourState.ACTIVE
        
        return {
            "success": True,
            "action": "waypoint_advanced",
            "current_waypoint": waypoint_content,
            "progress": {
                "completed": len(tour_state["completed_waypoints"]),
                "total": len(waypoints),
                "percentage": (len(tour_state["completed_waypoints"]) / len(waypoints)) * 100
            },
            "state": tour_state["state"].value
        }
    
    async def _prepare_waypoint_content(
        self, 
        waypoint: Dict[str, Any], 
        context: TourContext, 
        tour_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare comprehensive content for a waypoint."""
        
        # Coordinate multiple agents concurrently
        tasks = []
        
        # Task 1: Retrieve relevant knowledge
        retrieval_task = asyncio.create_task(
            self.retriever.process(context, {
                "query": f"{waypoint.get('name', '')} {' '.join(waypoint.get('key_points', []))}",
                "query_type": "contextual",
                "max_results": 5
            })
        )
        tasks.append(("retrieval", retrieval_task))
        
        # Task 2: Generate narration (depends on retrieval, so we'll do this after)
        
        # Wait for retrieval to complete
        retrieval_result = await retrieval_task
        
        # Task 2: Generate narration with retrieved knowledge
        narration_task = asyncio.create_task(
            self.narrator.process(context, {
                "content_info": waypoint,
                "retrieved_knowledge": retrieval_result,
                "waypoint_info": waypoint,
                "duration_seconds": waypoint.get("duration", 60) * 60  # Convert minutes to seconds
            })
        )
        
        # Wait for narration
        narration_result = await narration_task
        
        # Combine results
        waypoint_content = {
            "waypoint": waypoint,
            "knowledge": retrieval_result,
            "narration": narration_result,
            "interactive_elements": self._prepare_interactive_elements(waypoint, context),
            "accessibility_features": self._prepare_accessibility_features(waypoint, context),
            "performance_hints": self._get_performance_hints(waypoint, tour_state)
        }
        
        # Update shared context
        tour_state["shared_context"]["current_waypoint_content"] = waypoint_content
        
        return waypoint_content
    
    async def _handle_question(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle real-time Q&A during tour."""
        try:
            tour_state = self.active_tours.get(context.session_id)
            if not tour_state:
                return {"success": False, "error": "No active tour found"}
            
            # Pause current narration if active
            previous_state = tour_state["state"]
            tour_state["state"] = TourState.Q_AND_A
            
            # Add current tour context to Q&A input
            enhanced_input = {
                **input_data,
                "current_location": tour_state.get("current_waypoint", {}),
                "tour_context": tour_state.get("shared_context", {}),
                "visited_locations": tour_state.get("completed_waypoints", [])
            }
            
            # Process Q&A
            qa_result = await self.qa_agent.process(context, enhanced_input)
            
            # Resume previous state
            tour_state["state"] = previous_state
            
            # Update engagement metrics
            self._update_engagement_metrics(tour_state, "question_asked")
            
            return {
                "success": True,
                "qa_result": qa_result,
                "tour_state": tour_state["state"].value,
                "context_maintained": True
            }
            
        except Exception as e:
            self.logger.error(f"Error handling question: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _update_context(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tour context based on user interactions."""
        try:
            tour_state = self.active_tours.get(context.session_id)
            if not tour_state:
                return {"success": False, "error": "No active tour found"}
            
            # Update context based on input
            updates = input_data.get("context_updates", {})
            
            for key, value in updates.items():
                if key == "user_position":
                    context.current_position = value
                elif key == "user_preferences":
                    context.user_preferences.update(value)
                elif key == "accessibility_needs":
                    context.accessibility_needs = value
                elif key == "engagement_data":
                    self._update_engagement_metrics(tour_state, value)
            
            # Check if adaptive adjustments are needed
            if self.adaptive_pacing:
                adjustments = await self._check_adaptive_adjustments(context, tour_state)
                if adjustments:
                    return await self._make_adaptive_adjustment(context, tour_state, adjustments)
            
            return {
                "success": True,
                "context_updated": True,
                "adaptive_adjustments": False
            }
            
        except Exception as e:
            self.logger.error(f"Error updating context: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _check_adaptive_adjustments(
        self, 
        context: TourContext, 
        tour_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if adaptive adjustments are needed."""
        
        metrics = tour_state.get("performance_metrics", {})
        engagement_score = metrics.get("user_engagement_score", 0.8)
        
        adjustments = {}
        
        # Check engagement level
        if engagement_score < 0.5:
            adjustments["pacing"] = "increase_interaction"
            adjustments["content"] = "more_engaging"
        elif engagement_score > 0.9:
            adjustments["pacing"] = "increase_depth"
            adjustments["content"] = "more_detailed"
        
        # Check time constraints
        elapsed_time = (datetime.utcnow() - tour_state["start_time"]).total_seconds()
        planned_duration = tour_state.get("tour_plan", {}).get("estimated_duration", 60) * 60
        
        if elapsed_time > planned_duration * 0.8:  # 80% of planned time used
            adjustments["pacing"] = "accelerate"
            adjustments["content"] = "highlights_only"
        
        return adjustments if adjustments else None
    
    async def _make_adaptive_adjustment(
        self, 
        context: TourContext, 
        tour_state: Dict[str, Any], 
        adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make adaptive adjustments to the tour experience."""
        
        applied_adjustments = []
        
        # Adjust pacing
        if "pacing" in adjustments:
            pacing_adjustment = adjustments["pacing"]
            
            if pacing_adjustment == "accelerate":
                # Reduce duration of remaining waypoints
                remaining_waypoints = self._get_remaining_waypoints(tour_state)
                for waypoint in remaining_waypoints:
                    waypoint["duration"] = max(5, waypoint.get("duration", 15) * 0.7)
                applied_adjustments.append("reduced_waypoint_durations")
                
            elif pacing_adjustment == "increase_interaction":
                # Add more interactive elements
                current_waypoint = tour_state.get("current_waypoint")
                if current_waypoint:
                    current_waypoint["interactive_elements"] = current_waypoint.get("interactive_elements", [])
                    current_waypoint["interactive_elements"].append({
                        "type": "engagement_boost",
                        "content": "What do you find most interesting about what you're seeing?",
                        "timing": "immediate"
                    })
                applied_adjustments.append("added_interactive_elements")
        
        # Adjust content
        if "content" in adjustments:
            content_adjustment = adjustments["content"]
            
            if content_adjustment == "highlights_only":
                # Focus on key highlights only
                remaining_waypoints = self._get_remaining_waypoints(tour_state)
                for waypoint in remaining_waypoints:
                    key_points = waypoint.get("key_points", [])
                    waypoint["key_points"] = key_points[:2]  # Keep only top 2 points
                applied_adjustments.append("focused_on_highlights")
        
        return {
            "success": True,
            "adaptive_adjustments_applied": applied_adjustments,
            "tour_state": tour_state["state"].value
        }
    
    def _get_remaining_waypoints(self, tour_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get remaining waypoints in the tour."""
        tour_plan = tour_state.get("tour_plan", {})
        waypoints = tour_plan.get("waypoints", [])
        completed_ids = [wp.get("id") for wp in tour_state.get("completed_waypoints", [])]
        current_id = tour_state.get("current_waypoint", {}).get("id")
        
        remaining = []
        found_current = False
        
        for waypoint in waypoints:
            if waypoint.get("id") == current_id:
                found_current = True
                continue
            
            if found_current and waypoint.get("id") not in completed_ids:
                remaining.append(waypoint)
        
        return remaining
    
    def _prepare_interactive_elements(self, waypoint: Dict[str, Any], context: TourContext) -> List[Dict[str, Any]]:
        """Prepare interactive elements for a waypoint."""
        elements = []
        
        # Add waypoint-specific interactive elements
        waypoint_elements = waypoint.get("interactive_elements", [])
        elements.extend(waypoint_elements)
        
        # Add context-based interactive elements
        if "architecture" in context.user_preferences.get("interests", []):
            elements.append({
                "type": "architectural_highlight",
                "content": "Notice the architectural details around you",
                "timing": "on_arrival"
            })
        
        if context.accessibility_needs:
            elements.append({
                "type": "accessibility_guide",
                "content": "Audio description available for visual elements",
                "timing": "continuous"
            })
        
        return elements
    
    def _prepare_accessibility_features(self, waypoint: Dict[str, Any], context: TourContext) -> List[str]:
        """Prepare accessibility features for a waypoint."""
        features = []
        
        for need in context.accessibility_needs:
            if need == "visual_impairment":
                features.extend(["audio_descriptions", "spatial_audio_cues", "tactile_feedback"])
            elif need == "hearing_impairment":
                features.extend(["visual_captions", "haptic_feedback", "sign_language_avatar"])
            elif need == "mobility_impairment":
                features.extend(["teleport_navigation", "seated_experience", "gesture_alternatives"])
            elif need == "cognitive_support":
                features.extend(["simplified_interface", "progress_indicators", "clear_instructions"])
        
        return list(set(features))  # Remove duplicates
    
    def _get_performance_hints(self, waypoint: Dict[str, Any], tour_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance optimization hints for the waypoint."""
        return {
            "preload_assets": waypoint.get("assets", []),
            "lod_level": "medium",  # Based on device capabilities
            "streaming_priority": "high" if waypoint.get("duration", 0) > 10 else "normal",
            "cache_strategy": "aggressive"
        }
    
    def _update_engagement_metrics(self, tour_state: Dict[str, Any], event: str):
        """Update user engagement metrics."""
        metrics = tour_state.get("performance_metrics", {})
        
        if event == "question_asked":
            metrics["user_engagement_score"] = min(1.0, metrics.get("user_engagement_score", 0.8) + 0.1)
        elif event == "waypoint_completed":
            metrics["user_engagement_score"] = min(1.0, metrics.get("user_engagement_score", 0.8) + 0.05)
        elif event == "interaction_timeout":
            metrics["user_engagement_score"] = max(0.0, metrics.get("user_engagement_score", 0.8) - 0.1)
    
    async def _pause_tour(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pause the current tour."""
        tour_state = self.active_tours.get(context.session_id)
        if not tour_state:
            return {"success": False, "error": "No active tour found"}
        
        tour_state["state"] = TourState.PAUSED
        tour_state["pause_time"] = datetime.utcnow()
        
        return {
            "success": True,
            "state": tour_state["state"].value,
            "message": "Tour paused. You can resume at any time."
        }
    
    async def _resume_tour(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resume a paused tour."""
        tour_state = self.active_tours.get(context.session_id)
        if not tour_state:
            return {"success": False, "error": "No active tour found"}
        
        if tour_state["state"] != TourState.PAUSED:
            return {"success": False, "error": "Tour is not paused"}
        
        tour_state["state"] = TourState.ACTIVE
        
        # Calculate pause duration for metrics
        if "pause_time" in tour_state:
            pause_duration = (datetime.utcnow() - tour_state["pause_time"]).total_seconds()
            tour_state["total_pause_time"] = tour_state.get("total_pause_time", 0) + pause_duration
            del tour_state["pause_time"]
        
        return {
            "success": True,
            "state": tour_state["state"].value,
            "message": "Tour resumed. Welcome back!"
        }
    
    async def _complete_tour(self, context: TourContext, tour_state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the tour and generate summary."""
        tour_state["state"] = TourState.COMPLETED
        tour_state["end_time"] = datetime.utcnow()
        
        # Calculate tour metrics
        total_duration = (tour_state["end_time"] - tour_state["start_time"]).total_seconds()
        waypoints_completed = len(tour_state.get("completed_waypoints", []))
        
        tour_summary = {
            "tour_id": context.tour_id,
            "session_id": context.session_id,
            "total_duration_seconds": int(total_duration),
            "waypoints_completed": waypoints_completed,
            "questions_asked": tour_state.get("questions_asked", 0),
            "engagement_score": tour_state.get("performance_metrics", {}).get("user_engagement_score", 0.8),
            "completion_status": "completed"
        }
        
        return {
            "success": True,
            "state": tour_state["state"].value,
            "tour_summary": tour_summary,
            "message": "Tour completed! Thank you for exploring with us."
        }
    
    async def _end_tour(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """End tour (can be called at any time)."""
        tour_state = self.active_tours.get(context.session_id)
        if not tour_state:
            return {"success": False, "error": "No active tour found"}
        
        # Complete tour regardless of current state
        result = await self._complete_tour(context, tour_state)
        
        # Clean up tour state
        del self.active_tours[context.session_id]
        
        return result
    
    async def _get_recovery_actions(self, context: TourContext, input_data: Dict[str, Any]) -> List[str]:
        """Get recovery actions for error scenarios."""
        return [
            "Restart tour from current waypoint",
            "Skip to next waypoint",
            "Return to previous waypoint",
            "Switch to basic tour mode",
            "Contact support"
        ]
