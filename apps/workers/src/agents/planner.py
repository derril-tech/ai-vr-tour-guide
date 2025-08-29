"""
Tour Planner Agent

Plans optimal tour routes and experiences based on user preferences,
time constraints, and site characteristics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from langchain.llms import OpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from .base import BaseAgent, TourContext

logger = logging.getLogger(__name__)


class TourPlannerAgent(BaseAgent):
    """Agent responsible for planning optimal tour experiences."""
    
    def __init__(self):
        super().__init__(
            name="TourPlanner",
            description="Plans optimal tour routes and experiences based on user preferences"
        )
        
        # Initialize LLM
        self.llm = OpenAI(temperature=0.3)
        
        # Planning templates
        self.route_planning_template = PromptTemplate(
            input_variables=["site_info", "user_preferences", "time_available", "accessibility_needs"],
            template="""
You are an expert tour guide planning an optimal route through a historical site.

Site Information:
{site_info}

User Preferences:
{user_preferences}

Available Time: {time_available} minutes
Accessibility Needs: {accessibility_needs}

Plan an engaging tour route that:
1. Maximizes educational value within the time constraint
2. Accommodates accessibility requirements
3. Follows a logical narrative flow
4. Includes interactive elements and key highlights
5. Balances information density with engagement

Provide your response as a structured tour plan with:
- Route waypoints with estimated times
- Key narratives for each stop
- Interactive elements and questions
- Accessibility considerations
- Alternative paths for different interests

Tour Plan:
"""
        )
        
        # Initialize LangGraph workflow
        self.workflow = self._create_planning_workflow()
        
    def _create_planning_workflow(self) -> StateGraph:
        """Create the tour planning workflow using LangGraph."""
        
        def analyze_user_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze user preferences and constraints."""
            context = state["context"]
            preferences = context.user_preferences
            
            # Extract key preference categories
            interests = preferences.get("interests", [])
            learning_style = preferences.get("learning_style", "balanced")
            pace = preferences.get("pace", "moderate")
            
            state["analyzed_preferences"] = {
                "interests": interests,
                "learning_style": learning_style,
                "pace": pace,
                "priority_themes": self._extract_priority_themes(interests)
            }
            
            return state
            
        def generate_route_options(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate multiple route options."""
            context = state["context"]
            preferences = state["analyzed_preferences"]
            
            # Generate 3 different route options
            routes = []
            
            # Route 1: Comprehensive (for history enthusiasts)
            routes.append(self._generate_comprehensive_route(context, preferences))
            
            # Route 2: Highlights (for time-constrained visitors)
            routes.append(self._generate_highlights_route(context, preferences))
            
            # Route 3: Interactive (for families/groups)
            routes.append(self._generate_interactive_route(context, preferences))
            
            state["route_options"] = routes
            return state
            
        def select_optimal_route(state: Dict[str, Any]) -> Dict[str, Any]:
            """Select the best route based on user context."""
            context = state["context"]
            routes = state["route_options"]
            preferences = state["analyzed_preferences"]
            
            # Score routes based on user preferences
            scored_routes = []
            for route in routes:
                score = self._score_route(route, preferences, context)
                scored_routes.append((route, score))
            
            # Select highest scoring route
            best_route = max(scored_routes, key=lambda x: x[1])[0]
            
            state["selected_route"] = best_route
            return state
            
        def personalize_content(state: Dict[str, Any]) -> Dict[str, Any]:
            """Personalize content for the selected route."""
            route = state["selected_route"]
            context = state["context"]
            preferences = state["analyzed_preferences"]
            
            # Customize narratives and interactions
            personalized_route = self._personalize_route_content(route, preferences, context)
            
            state["final_plan"] = personalized_route
            return state
        
        # Build the workflow graph
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("analyze_preferences", analyze_user_preferences)
        workflow.add_node("generate_routes", generate_route_options)
        workflow.add_node("select_route", select_optimal_route)
        workflow.add_node("personalize", personalize_content)
        
        # Add edges
        workflow.add_edge("analyze_preferences", "generate_routes")
        workflow.add_edge("generate_routes", "select_route")
        workflow.add_edge("select_route", "personalize")
        workflow.add_edge("personalize", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_preferences")
        
        return workflow.compile()
    
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process tour planning request."""
        try:
            # Prepare initial state
            initial_state = {
                "context": context,
                "input_data": input_data,
                "site_info": await self._get_site_information(context.site_id),
                "available_hotspots": await self._get_available_hotspots(context.site_id)
            }
            
            # Run the planning workflow
            result = await self.workflow.ainvoke(initial_state)
            
            tour_plan = result["final_plan"]
            
            return {
                "success": True,
                "tour_plan": tour_plan,
                "estimated_duration": tour_plan.get("estimated_duration", 60),
                "waypoint_count": len(tour_plan.get("waypoints", [])),
                "accessibility_compliant": tour_plan.get("accessibility_compliant", True),
                "personalization_score": tour_plan.get("personalization_score", 0.8)
            }
            
        except Exception as e:
            self.logger.error(f"Error in tour planning: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": await self._generate_fallback_plan(context)
            }
    
    def _extract_priority_themes(self, interests: List[str]) -> List[str]:
        """Extract priority themes from user interests."""
        theme_mapping = {
            "history": ["historical_events", "architecture", "cultural_heritage"],
            "architecture": ["building_techniques", "architectural_styles", "engineering"],
            "art": ["artistic_movements", "cultural_expression", "visual_arts"],
            "science": ["scientific_discoveries", "technology", "innovation"],
            "culture": ["social_history", "daily_life", "traditions"],
            "nature": ["environmental_history", "natural_features", "conservation"]
        }
        
        priority_themes = []
        for interest in interests:
            themes = theme_mapping.get(interest.lower(), [interest])
            priority_themes.extend(themes)
        
        return list(set(priority_themes))
    
    def _generate_comprehensive_route(self, context: TourContext, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive tour route."""
        return {
            "route_type": "comprehensive",
            "estimated_duration": 90,
            "waypoints": [
                {
                    "id": "entrance",
                    "name": "Main Entrance",
                    "duration": 5,
                    "narrative_type": "introduction",
                    "key_points": ["Welcome", "Site overview", "Safety briefing"]
                },
                {
                    "id": "historical_overview",
                    "name": "Historical Overview Point",
                    "duration": 15,
                    "narrative_type": "historical_context",
                    "key_points": ["Timeline", "Key figures", "Historical significance"]
                },
                {
                    "id": "main_structure",
                    "name": "Main Structure",
                    "duration": 25,
                    "narrative_type": "detailed_exploration",
                    "key_points": ["Architecture", "Construction techniques", "Purpose"]
                },
                {
                    "id": "daily_life_area",
                    "name": "Daily Life Exhibition",
                    "duration": 20,
                    "narrative_type": "immersive_experience",
                    "key_points": ["Social customs", "Daily routines", "Cultural practices"]
                },
                {
                    "id": "conclusion",
                    "name": "Conclusion Point",
                    "duration": 10,
                    "narrative_type": "synthesis",
                    "key_points": ["Key takeaways", "Modern relevance", "Further exploration"]
                }
            ],
            "accessibility_features": ["Audio descriptions", "Tactile elements", "Clear pathways"],
            "interactive_elements": ["AR reconstructions", "Quiz questions", "Photo opportunities"]
        }
    
    def _generate_highlights_route(self, context: TourContext, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a highlights-focused route."""
        return {
            "route_type": "highlights",
            "estimated_duration": 45,
            "waypoints": [
                {
                    "id": "entrance",
                    "name": "Quick Introduction",
                    "duration": 3,
                    "narrative_type": "brief_intro",
                    "key_points": ["Welcome", "What to expect"]
                },
                {
                    "id": "highlight_1",
                    "name": "Most Significant Feature",
                    "duration": 15,
                    "narrative_type": "highlight_focus",
                    "key_points": ["Why it's important", "Key story", "Visual impact"]
                },
                {
                    "id": "highlight_2",
                    "name": "Second Major Feature",
                    "duration": 12,
                    "narrative_type": "highlight_focus",
                    "key_points": ["Unique aspects", "Historical importance"]
                },
                {
                    "id": "highlight_3",
                    "name": "Final Highlight",
                    "duration": 10,
                    "narrative_type": "highlight_focus",
                    "key_points": ["Memorable conclusion", "Call to action"]
                },
                {
                    "id": "wrap_up",
                    "name": "Quick Wrap-up",
                    "duration": 5,
                    "narrative_type": "conclusion",
                    "key_points": ["Summary", "Next steps"]
                }
            ],
            "accessibility_features": ["Essential audio", "Key visual elements"],
            "interactive_elements": ["Photo spots", "Quick quiz"]
        }
    
    def _generate_interactive_route(self, context: TourContext, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an interactive, family-friendly route."""
        return {
            "route_type": "interactive",
            "estimated_duration": 60,
            "waypoints": [
                {
                    "id": "interactive_intro",
                    "name": "Interactive Welcome",
                    "duration": 8,
                    "narrative_type": "engaging_intro",
                    "key_points": ["Fun facts", "Mystery to solve", "What to look for"]
                },
                {
                    "id": "hands_on_1",
                    "name": "First Interactive Station",
                    "duration": 15,
                    "narrative_type": "hands_on_learning",
                    "key_points": ["Try it yourself", "How it works", "Why it matters"]
                },
                {
                    "id": "story_time",
                    "name": "Story Corner",
                    "duration": 12,
                    "narrative_type": "storytelling",
                    "key_points": ["Character stories", "Dramatic events", "Emotional connection"]
                },
                {
                    "id": "hands_on_2",
                    "name": "Second Interactive Station",
                    "duration": 15,
                    "narrative_type": "hands_on_learning",
                    "key_points": ["Group activity", "Problem solving", "Discovery"]
                },
                {
                    "id": "celebration",
                    "name": "Celebration Point",
                    "duration": 10,
                    "narrative_type": "celebration",
                    "key_points": ["What we learned", "Achievements", "Take-home message"]
                }
            ],
            "accessibility_features": ["Multi-sensory", "Group activities", "Flexible pacing"],
            "interactive_elements": ["AR games", "Scavenger hunt", "Group challenges", "Photo missions"]
        }
    
    def _score_route(self, route: Dict[str, Any], preferences: Dict[str, Any], context: TourContext) -> float:
        """Score a route based on user preferences and context."""
        score = 0.0
        
        # Time preference scoring
        available_time = context.user_preferences.get("available_time", 60)
        route_duration = route.get("estimated_duration", 60)
        
        if abs(route_duration - available_time) <= 15:
            score += 0.3  # Good time match
        elif route_duration > available_time:
            score -= 0.2  # Too long
        
        # Learning style preference
        learning_style = preferences.get("learning_style", "balanced")
        route_type = route.get("route_type", "comprehensive")
        
        style_match = {
            "visual": {"highlights": 0.3, "interactive": 0.2, "comprehensive": 0.1},
            "hands_on": {"interactive": 0.3, "comprehensive": 0.2, "highlights": 0.1},
            "detailed": {"comprehensive": 0.3, "highlights": 0.1, "interactive": 0.2},
            "balanced": {"comprehensive": 0.2, "highlights": 0.2, "interactive": 0.2}
        }
        
        score += style_match.get(learning_style, {}).get(route_type, 0.1)
        
        # Accessibility needs
        accessibility_needs = context.accessibility_needs
        if accessibility_needs and route.get("accessibility_features"):
            score += 0.2
        
        # Interest alignment
        interests = preferences.get("interests", [])
        route_themes = self._extract_route_themes(route)
        
        interest_overlap = len(set(interests) & set(route_themes))
        score += min(0.3, interest_overlap * 0.1)
        
        return score
    
    def _extract_route_themes(self, route: Dict[str, Any]) -> List[str]:
        """Extract themes from a route."""
        themes = []
        for waypoint in route.get("waypoints", []):
            key_points = waypoint.get("key_points", [])
            themes.extend(key_points)
        return themes
    
    def _personalize_route_content(self, route: Dict[str, Any], preferences: Dict[str, Any], context: TourContext) -> Dict[str, Any]:
        """Personalize route content based on user preferences."""
        personalized_route = route.copy()
        
        # Add personalization metadata
        personalized_route["personalization"] = {
            "language": context.language,
            "accessibility_adaptations": context.accessibility_needs,
            "interest_focus": preferences.get("interests", []),
            "learning_style_adaptations": preferences.get("learning_style", "balanced")
        }
        
        # Customize waypoint content
        for waypoint in personalized_route.get("waypoints", []):
            waypoint["personalized_content"] = self._personalize_waypoint(waypoint, preferences, context)
        
        # Calculate personalization score
        personalized_route["personalization_score"] = self._calculate_personalization_score(
            personalized_route, preferences, context
        )
        
        return personalized_route
    
    def _personalize_waypoint(self, waypoint: Dict[str, Any], preferences: Dict[str, Any], context: TourContext) -> Dict[str, Any]:
        """Personalize individual waypoint content."""
        return {
            "narrative_style": self._adapt_narrative_style(preferences.get("learning_style", "balanced")),
            "interaction_level": self._adapt_interaction_level(preferences.get("pace", "moderate")),
            "accessibility_features": self._adapt_accessibility_features(context.accessibility_needs),
            "language_adaptations": {"language": context.language, "complexity": "appropriate"}
        }
    
    def _adapt_narrative_style(self, learning_style: str) -> str:
        """Adapt narrative style to learning preference."""
        style_map = {
            "visual": "descriptive_visual",
            "hands_on": "interactive_discovery",
            "detailed": "comprehensive_analytical",
            "balanced": "engaging_informative"
        }
        return style_map.get(learning_style, "engaging_informative")
    
    def _adapt_interaction_level(self, pace: str) -> str:
        """Adapt interaction level to user pace."""
        pace_map = {
            "slow": "high_interaction",
            "moderate": "balanced_interaction",
            "fast": "minimal_interaction"
        }
        return pace_map.get(pace, "balanced_interaction")
    
    def _adapt_accessibility_features(self, accessibility_needs: List[str]) -> List[str]:
        """Adapt accessibility features to user needs."""
        features = []
        
        for need in accessibility_needs:
            if need == "visual_impairment":
                features.extend(["audio_descriptions", "tactile_elements", "high_contrast"])
            elif need == "hearing_impairment":
                features.extend(["visual_captions", "sign_language", "vibration_cues"])
            elif need == "mobility_impairment":
                features.extend(["accessible_paths", "seating_options", "alternative_viewpoints"])
            elif need == "cognitive_support":
                features.extend(["simplified_language", "clear_structure", "repetition"])
        
        return list(set(features))
    
    def _calculate_personalization_score(self, route: Dict[str, Any], preferences: Dict[str, Any], context: TourContext) -> float:
        """Calculate how well the route is personalized."""
        score = 0.0
        
        # Language match
        if route.get("personalization", {}).get("language") == context.language:
            score += 0.2
        
        # Accessibility adaptations
        if context.accessibility_needs and route.get("personalization", {}).get("accessibility_adaptations"):
            score += 0.3
        
        # Interest alignment
        interests = preferences.get("interests", [])
        route_interests = route.get("personalization", {}).get("interest_focus", [])
        if set(interests) & set(route_interests):
            score += 0.3
        
        # Learning style adaptation
        if route.get("personalization", {}).get("learning_style_adaptations"):
            score += 0.2
        
        return min(1.0, score)
    
    async def _get_site_information(self, site_id: str) -> Dict[str, Any]:
        """Get comprehensive site information."""
        # This would fetch from database in real implementation
        return {
            "site_id": site_id,
            "name": "Historical Site",
            "type": "museum",
            "themes": ["history", "architecture", "culture"],
            "estimated_visit_time": 60,
            "accessibility_features": ["wheelchair_accessible", "audio_guides"],
            "highlights": ["main_hall", "artifact_collection", "historical_timeline"]
        }
    
    async def _get_available_hotspots(self, site_id: str) -> List[Dict[str, Any]]:
        """Get available hotspots for the site."""
        # This would fetch from database in real implementation
        return [
            {"id": "entrance", "name": "Main Entrance", "type": "introduction"},
            {"id": "hall", "name": "Great Hall", "type": "architectural"},
            {"id": "artifacts", "name": "Artifact Gallery", "type": "collection"},
            {"id": "timeline", "name": "Historical Timeline", "type": "educational"}
        ]
    
    async def _generate_fallback_plan(self, context: TourContext) -> Dict[str, Any]:
        """Generate a simple fallback plan if main planning fails."""
        return {
            "route_type": "fallback",
            "estimated_duration": 45,
            "waypoints": [
                {"id": "start", "name": "Welcome", "duration": 5},
                {"id": "main", "name": "Main Feature", "duration": 30},
                {"id": "end", "name": "Conclusion", "duration": 10}
            ],
            "message": "Using simplified tour plan due to planning error"
        }
