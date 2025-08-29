"""
Narrator Agent

Generates engaging, contextual narrations with citations and quiz integration.
Adapts storytelling style based on user preferences and tour context.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base import BaseAgent, TourContext

logger = logging.getLogger(__name__)


class NarrationSegment(BaseModel):
    """A segment of narration with metadata."""
    content: str = Field(description="The narration content")
    duration_seconds: int = Field(description="Estimated duration in seconds")
    emotion: str = Field(description="Emotional tone: neutral, excited, mysterious, reverent")
    emphasis_points: List[str] = Field(description="Key points to emphasize")
    citations: List[Dict[str, Any]] = Field(description="Source citations")
    interactive_elements: List[Dict[str, Any]] = Field(description="Interactive elements like questions")


class NarrationResponse(BaseModel):
    """Complete narration response."""
    segments: List[NarrationSegment] = Field(description="Narration segments")
    total_duration: int = Field(description="Total duration in seconds")
    style: str = Field(description="Narration style used")
    quiz_questions: List[Dict[str, Any]] = Field(description="Integrated quiz questions")
    accessibility_notes: List[str] = Field(description="Accessibility considerations")


class NarratorAgent(BaseAgent):
    """Agent responsible for generating engaging narrations with citations."""
    
    def __init__(self):
        super().__init__(
            name="Narrator",
            description="Generates engaging, contextual narrations with citations and quiz integration"
        )
        
        # Initialize LLM
        self.llm = OpenAI(temperature=0.7)  # Higher temperature for creativity
        
        # Output parser
        self.output_parser = PydanticOutputParser(pydantic_object=NarrationResponse)
        
        # Narration templates
        self.narration_template = PromptTemplate(
            input_variables=[
                "content_info", "user_context", "narration_style", 
                "duration_target", "citations", "accessibility_needs"
            ],
            template="""
You are an expert storyteller and tour guide creating an engaging narration for a VR tour experience.

Content Information:
{content_info}

User Context:
- Language: {user_context[language]}
- Learning Style: {user_context[learning_style]}
- Interests: {user_context[interests]}
- Available Time: {duration_target} seconds

Narration Style: {narration_style}
Accessibility Needs: {accessibility_needs}

Source Citations to Include:
{citations}

Create an engaging narration that:
1. Tells a compelling story while being historically accurate
2. Adapts to the user's learning style and interests
3. Includes proper citations naturally within the narrative
4. Incorporates interactive elements and questions
5. Considers accessibility needs
6. Maintains appropriate pacing for the time available
7. Uses vivid, immersive language that brings the past to life

{format_instructions}

Narration:
"""
        )
        
        # Style templates for different narration approaches
        self.style_templates = {
            "storytelling": "Focus on narrative flow, character stories, and dramatic moments",
            "educational": "Emphasize facts, analysis, and learning objectives",
            "immersive": "Use sensory details and 'you are there' perspective",
            "conversational": "Adopt a friendly, informal tone as if talking to a friend",
            "dramatic": "Build tension and excitement around key moments",
            "contemplative": "Encourage reflection and deeper thinking"
        }
    
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process narration generation request."""
        try:
            # Extract input parameters
            content_info = input_data.get("content_info", {})
            retrieved_knowledge = input_data.get("retrieved_knowledge", {})
            waypoint_info = input_data.get("waypoint_info", {})
            duration_target = input_data.get("duration_seconds", 60)
            
            # Determine narration style
            narration_style = await self._determine_narration_style(context, input_data)
            
            # Prepare content for narration
            prepared_content = await self._prepare_content(
                content_info, retrieved_knowledge, waypoint_info, context
            )
            
            # Generate narration
            narration = await self._generate_narration(
                prepared_content, context, narration_style, duration_target
            )
            
            # Add quiz integration
            narration_with_quiz = await self._integrate_quiz_elements(narration, context)
            
            # Apply accessibility adaptations
            final_narration = await self._apply_accessibility_adaptations(
                narration_with_quiz, context
            )
            
            return {
                "success": True,
                "narration": final_narration,
                "style": narration_style,
                "estimated_duration": final_narration.total_duration,
                "segment_count": len(final_narration.segments),
                "citation_count": sum(len(seg.citations) for seg in final_narration.segments),
                "quiz_count": len(final_narration.quiz_questions)
            }
            
        except Exception as e:
            self.logger.error(f"Error in narration generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_narration": await self._generate_fallback_narration(context, input_data)
            }
    
    async def _determine_narration_style(self, context: TourContext, input_data: Dict[str, Any]) -> str:
        """Determine the best narration style based on context."""
        user_prefs = context.user_preferences
        
        # Check for explicit style preference
        if "narration_style" in input_data:
            return input_data["narration_style"]
        
        # Determine based on user characteristics
        learning_style = user_prefs.get("learning_style", "balanced")
        interests = user_prefs.get("interests", [])
        age_group = user_prefs.get("age_group", "adult")
        
        # Style selection logic
        if age_group == "child":
            return "storytelling"
        elif learning_style == "visual":
            return "immersive"
        elif learning_style == "detailed":
            return "educational"
        elif "drama" in interests or "stories" in interests:
            return "dramatic"
        elif learning_style == "hands_on":
            return "conversational"
        else:
            return "storytelling"  # Default to storytelling
    
    async def _prepare_content(
        self, 
        content_info: Dict[str, Any], 
        retrieved_knowledge: Dict[str, Any],
        waypoint_info: Dict[str, Any],
        context: TourContext
    ) -> Dict[str, Any]:
        """Prepare and structure content for narration."""
        
        # Combine information from different sources
        combined_content = {
            "main_topic": waypoint_info.get("name", "Unknown Location"),
            "key_points": waypoint_info.get("key_points", []),
            "historical_context": [],
            "interesting_facts": [],
            "personal_stories": [],
            "technical_details": [],
            "cultural_significance": []
        }
        
        # Process retrieved knowledge
        if retrieved_knowledge.get("success") and retrieved_knowledge.get("results"):
            for result in retrieved_knowledge["results"]:
                content = result.get("content", "")
                
                # Categorize content based on keywords and context
                if any(word in content.lower() for word in ["built", "constructed", "established", "founded"]):
                    combined_content["historical_context"].append({
                        "content": content,
                        "source": result.get("source", {}),
                        "relevance": result.get("relevance_score", 0)
                    })
                elif any(word in content.lower() for word in ["interesting", "unique", "remarkable", "notable"]):
                    combined_content["interesting_facts"].append({
                        "content": content,
                        "source": result.get("source", {}),
                        "relevance": result.get("relevance_score", 0)
                    })
                elif any(word in content.lower() for word in ["person", "people", "lived", "worked", "story"]):
                    combined_content["personal_stories"].append({
                        "content": content,
                        "source": result.get("source", {}),
                        "relevance": result.get("relevance_score", 0)
                    })
                elif any(word in content.lower() for word in ["architecture", "design", "structure", "material"]):
                    combined_content["technical_details"].append({
                        "content": content,
                        "source": result.get("source", {}),
                        "relevance": result.get("relevance_score", 0)
                    })
                else:
                    combined_content["cultural_significance"].append({
                        "content": content,
                        "source": result.get("source", {}),
                        "relevance": result.get("relevance_score", 0)
                    })
        
        # Sort each category by relevance
        for category in ["historical_context", "interesting_facts", "personal_stories", "technical_details", "cultural_significance"]:
            combined_content[category].sort(key=lambda x: x["relevance"], reverse=True)
        
        return combined_content
    
    async def _generate_narration(
        self,
        content: Dict[str, Any],
        context: TourContext,
        style: str,
        duration_target: int
    ) -> NarrationResponse:
        """Generate the main narration content."""
        
        # Prepare citations
        citations = self._extract_citations(content)
        
        # Format content for prompt
        content_summary = self._format_content_for_prompt(content)
        
        # Prepare user context
        user_context = {
            "language": context.language,
            "learning_style": context.user_preferences.get("learning_style", "balanced"),
            "interests": context.user_preferences.get("interests", [])
        }
        
        # Create prompt
        prompt = self.narration_template.format(
            content_info=content_summary,
            user_context=user_context,
            narration_style=self.style_templates.get(style, "storytelling"),
            duration_target=duration_target,
            citations=citations,
            accessibility_needs=context.accessibility_needs,
            format_instructions=self.output_parser.get_format_instructions()
        )
        
        try:
            # Generate narration
            response = await self.llm.agenerate([prompt])
            narration_text = response.generations[0][0].text.strip()
            
            # Parse the response
            narration = self.output_parser.parse(narration_text)
            
            return narration
            
        except Exception as e:
            self.logger.error(f"Error generating narration: {str(e)}")
            
            # Create fallback narration
            return self._create_fallback_narration(content, style, duration_target, citations)
    
    def _extract_citations(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract citations from content sources."""
        citations = []
        
        for category in ["historical_context", "interesting_facts", "personal_stories", "technical_details", "cultural_significance"]:
            for item in content.get(category, []):
                source = item.get("source", {})
                if source:
                    citation = {
                        "title": source.get("title", "Unknown Source"),
                        "author": source.get("author", "Unknown Author"),
                        "type": source.get("type", "unknown"),
                        "credibility_score": source.get("credibility_score", 0.5),
                        "formatted": source.get("formatted", "Unknown Source")
                    }
                    citations.append(citation)
        
        # Remove duplicates
        seen = set()
        unique_citations = []
        for citation in citations:
            key = citation["title"] + citation["author"]
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _format_content_for_prompt(self, content: Dict[str, Any]) -> str:
        """Format content for the narration prompt."""
        formatted_parts = []
        
        formatted_parts.append(f"Main Topic: {content['main_topic']}")
        
        if content.get("key_points"):
            formatted_parts.append(f"Key Points: {', '.join(content['key_points'])}")
        
        for category, items in content.items():
            if category in ["historical_context", "interesting_facts", "personal_stories", "technical_details", "cultural_significance"] and items:
                formatted_parts.append(f"\n{category.replace('_', ' ').title()}:")
                for item in items[:2]:  # Limit to top 2 items per category
                    formatted_parts.append(f"- {item['content'][:200]}...")
        
        return "\n".join(formatted_parts)
    
    def _create_fallback_narration(
        self, 
        content: Dict[str, Any], 
        style: str, 
        duration_target: int,
        citations: List[Dict[str, Any]]
    ) -> NarrationResponse:
        """Create a simple fallback narration."""
        
        main_topic = content.get("main_topic", "This Location")
        
        # Create basic narration segment
        basic_content = f"Welcome to {main_topic}. This is a significant location with rich history and cultural importance. "
        
        if content.get("key_points"):
            basic_content += f"Key features include {', '.join(content['key_points'][:3])}. "
        
        basic_content += "Take a moment to observe your surroundings and imagine the stories this place could tell."
        
        segment = NarrationSegment(
            content=basic_content,
            duration_seconds=min(duration_target, 30),
            emotion="neutral",
            emphasis_points=content.get("key_points", [])[:2],
            citations=citations[:2],
            interactive_elements=[
                {
                    "type": "observation_prompt",
                    "content": "What details do you notice about this location?",
                    "timing": "end"
                }
            ]
        )
        
        return NarrationResponse(
            segments=[segment],
            total_duration=segment.duration_seconds,
            style=style,
            quiz_questions=[],
            accessibility_notes=["Basic narration provided", "Visual observation encouraged"]
        )
    
    async def _integrate_quiz_elements(self, narration: NarrationResponse, context: TourContext) -> NarrationResponse:
        """Integrate quiz questions into the narration."""
        
        # Generate quiz questions based on narration content
        quiz_questions = []
        
        for i, segment in enumerate(narration.segments):
            # Extract key information for quiz generation
            key_points = segment.emphasis_points
            
            if key_points and len(quiz_questions) < 3:  # Limit to 3 questions
                # Generate different types of questions
                if i == 0:
                    # Opening question - observation based
                    quiz_questions.append({
                        "id": f"quiz_{i+1}",
                        "type": "observation",
                        "question": f"Based on what you've learned, what is the most significant feature of {key_points[0] if key_points else 'this location'}?",
                        "timing": "after_segment",
                        "segment_index": i,
                        "options": [
                            "Its historical importance",
                            "Its architectural features", 
                            "Its cultural significance",
                            "Its current use"
                        ],
                        "correct_answer": 0,
                        "explanation": "Each aspect contributes to the overall significance of this location."
                    })
                elif i == len(narration.segments) - 1:
                    # Closing question - synthesis
                    quiz_questions.append({
                        "id": f"quiz_{i+1}",
                        "type": "synthesis",
                        "question": "How does this location connect to the broader historical narrative?",
                        "timing": "after_segment",
                        "segment_index": i,
                        "options": [
                            "It represents a specific time period",
                            "It shows cultural evolution",
                            "It demonstrates technological progress",
                            "All of the above"
                        ],
                        "correct_answer": 3,
                        "explanation": "Historical sites often represent multiple aspects of human development and cultural change."
                    })
                else:
                    # Middle question - factual
                    if key_points:
                        quiz_questions.append({
                            "id": f"quiz_{i+1}",
                            "type": "factual",
                            "question": f"What is particularly notable about {key_points[0]}?",
                            "timing": "after_segment",
                            "segment_index": i,
                            "options": [
                                "Its age and historical period",
                                "Its construction methods",
                                "Its cultural importance",
                                "Its preservation state"
                            ],
                            "correct_answer": 0,
                            "explanation": f"The {key_points[0]} represents important historical and cultural elements of this site."
                        })
        
        # Update narration with quiz questions
        narration.quiz_questions = quiz_questions
        
        return narration
    
    async def _apply_accessibility_adaptations(self, narration: NarrationResponse, context: TourContext) -> NarrationResponse:
        """Apply accessibility adaptations to the narration."""
        
        accessibility_notes = []
        
        for need in context.accessibility_needs:
            if need == "visual_impairment":
                # Add more descriptive language
                for segment in narration.segments:
                    if "see" in segment.content.lower() or "look" in segment.content.lower():
                        segment.content = segment.content.replace("you can see", "you can experience")
                        segment.content = segment.content.replace("look at", "notice")
                
                accessibility_notes.append("Enhanced audio descriptions provided")
                accessibility_notes.append("Visual references adapted for audio experience")
                
            elif need == "hearing_impairment":
                # Ensure visual elements are described
                for segment in narration.segments:
                    segment.interactive_elements.append({
                        "type": "visual_cue",
                        "content": "Visual indicators will highlight key points mentioned in narration",
                        "timing": "continuous"
                    })
                
                accessibility_notes.append("Visual cues provided for audio content")
                
            elif need == "cognitive_support":
                # Simplify language and add structure
                for segment in narration.segments:
                    # Add clear transitions
                    if not segment.content.startswith(("First", "Next", "Now", "Finally")):
                        segment.content = f"Now, {segment.content}"
                    
                    # Add summary points
                    segment.interactive_elements.append({
                        "type": "summary_point",
                        "content": f"Key point: {segment.emphasis_points[0] if segment.emphasis_points else 'Important information shared'}",
                        "timing": "end"
                    })
                
                accessibility_notes.append("Simplified language and clear structure provided")
                accessibility_notes.append("Summary points added for key information")
        
        # Update accessibility notes
        narration.accessibility_notes.extend(accessibility_notes)
        
        return narration
    
    async def _generate_fallback_narration(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a simple fallback narration when main generation fails."""
        return {
            "content": "Welcome to this fascinating location. While we prepare your personalized narration, take a moment to explore your surroundings and discover the stories waiting to be told.",
            "duration": 15,
            "style": "basic",
            "accessibility_notes": ["Fallback narration provided", "Full narration will be available shortly"]
        }
