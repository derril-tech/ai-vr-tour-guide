"""
Q&A Agent

Handles real-time question answering with holographic citation chips,
voice recognition, and contextual understanding of the tour experience.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory

from .base import BaseAgent, TourContext
from .retriever import KnowledgeRetrieverAgent

logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    """Agent responsible for real-time question answering during tours."""
    
    def __init__(self):
        super().__init__(
            name="QAAgent",
            description="Handles real-time Q&A with contextual understanding and citations"
        )
        
        # Initialize LLM
        self.llm = OpenAI(temperature=0.2)  # Lower temperature for factual accuracy
        
        # Initialize retriever for knowledge lookup
        self.retriever = KnowledgeRetrieverAgent()
        
        # Conversation memory
        self.memory = ConversationBufferWindowMemory(k=5)  # Remember last 5 exchanges
        
        # Q&A templates
        self.qa_template = PromptTemplate(
            input_variables=[
                "question", "context", "retrieved_info", "tour_state", 
                "conversation_history", "user_profile"
            ],
            template="""
You are an expert tour guide AI assistant providing real-time answers during a VR tour experience.

Current Tour Context:
{context}

Tour State:
{tour_state}

User Profile:
{user_profile}

Recent Conversation:
{conversation_history}

User Question: "{question}"

Retrieved Information:
{retrieved_info}

Provide a helpful, accurate answer that:
1. Directly addresses the user's question
2. Uses information from reliable sources with citations
3. Relates to the current tour context and location
4. Matches the user's knowledge level and interests
5. Suggests follow-up exploration or related questions
6. Includes visual/spatial references for VR context
7. Maintains engagement and curiosity

If you cannot find sufficient information, be honest about limitations and suggest alternative ways to explore the topic.

Answer:
"""
        )
        
        # Question classification
        self.question_types = {
            "factual": ["what", "when", "where", "who", "how many"],
            "explanatory": ["why", "how", "explain"],
            "comparative": ["compare", "difference", "similar", "versus"],
            "opinion": ["think", "believe", "opinion", "feel"],
            "procedural": ["steps", "process", "procedure", "method"],
            "contextual": ["here", "this", "current", "now"]
        }
    
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Q&A request."""
        try:
            question = input_data.get("question", "")
            question_audio = input_data.get("audio_data")  # For ASR processing
            current_location = input_data.get("current_location", {})
            
            if not question and not question_audio:
                return {"success": False, "error": "No question provided"}
            
            # Process audio if provided (ASR)
            if question_audio and not question:
                question = await self._process_speech_to_text(question_audio, context)
            
            # Classify question type
            question_type = self._classify_question(question)
            
            # Get relevant context
            tour_context = await self._get_tour_context(context, current_location)
            
            # Retrieve relevant information
            retrieval_result = await self.retriever.process(context, {
                "query": question,
                "query_type": question_type,
                "max_results": 5
            })
            
            # Generate answer
            answer = await self._generate_answer(
                question, question_type, context, tour_context, retrieval_result
            )
            
            # Create citation chips for VR display
            citation_chips = await self._create_citation_chips(
                retrieval_result, current_location
            )
            
            # Generate follow-up suggestions
            follow_ups = await self._generate_follow_up_questions(
                question, answer, context, tour_context
            )
            
            # Update conversation memory
            self.memory.save_context(
                {"input": question},
                {"output": answer["content"]}
            )
            
            return {
                "success": True,
                "question": question,
                "question_type": question_type,
                "answer": answer,
                "citation_chips": citation_chips,
                "follow_up_questions": follow_ups,
                "confidence_score": answer.get("confidence", 0.8),
                "response_time_ms": answer.get("response_time_ms", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Q&A processing: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": await self._generate_fallback_response(
                    input_data.get("question", ""), context
                )
            }
    
    async def _process_speech_to_text(self, audio_data: bytes, context: TourContext) -> str:
        """Process speech to text using ASR."""
        try:
            # This would integrate with a speech recognition service
            # For now, return a placeholder
            return "What is the history of this building?"
            
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {str(e)}")
            return ""
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question being asked."""
        question_lower = question.lower()
        
        # Check for question type indicators
        for q_type, indicators in self.question_types.items():
            if any(indicator in question_lower for indicator in indicators):
                return q_type
        
        # Default classification
        if "?" in question:
            return "general"
        else:
            return "statement"
    
    async def _get_tour_context(self, context: TourContext, current_location: Dict[str, Any]) -> Dict[str, Any]:
        """Get current tour context and state."""
        return {
            "current_waypoint": current_location.get("waypoint_id", "unknown"),
            "location_name": current_location.get("name", "Current Location"),
            "visited_locations": context.visited_hotspots,
            "tour_progress": len(context.visited_hotspots),
            "user_interests": context.user_preferences.get("interests", []),
            "tour_theme": context.user_preferences.get("tour_theme", "general"),
            "time_spent": current_location.get("time_spent", 0)
        }
    
    async def _generate_answer(
        self,
        question: str,
        question_type: str,
        context: TourContext,
        tour_context: Dict[str, Any],
        retrieval_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive answer to the question."""
        
        start_time = datetime.utcnow()
        
        try:
            # Prepare retrieved information
            retrieved_info = ""
            if retrieval_result.get("success") and retrieval_result.get("results"):
                retrieved_info = "\n".join([
                    f"- {result['content'][:200]}... (Source: {result.get('source', {}).get('title', 'Unknown')})"
                    for result in retrieval_result["results"][:3]
                ])
            else:
                retrieved_info = "No specific information retrieved for this question."
            
            # Get conversation history
            conversation_history = self.memory.buffer if hasattr(self.memory, 'buffer') else "No previous conversation."
            
            # Prepare user profile
            user_profile = {
                "language": context.language,
                "interests": context.user_preferences.get("interests", []),
                "learning_style": context.user_preferences.get("learning_style", "balanced"),
                "accessibility_needs": context.accessibility_needs
            }
            
            # Generate answer using LLM
            prompt = self.qa_template.format(
                question=question,
                context=f"Site: {context.site_id}, Current Location: {tour_context['location_name']}",
                retrieved_info=retrieved_info,
                tour_state=tour_context,
                conversation_history=conversation_history,
                user_profile=user_profile
            )
            
            response = await self.llm.agenerate([prompt])
            answer_content = response.generations[0][0].text.strip()
            
            # Calculate response time
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Determine confidence based on retrieval quality
            confidence = self._calculate_answer_confidence(retrieval_result, question_type)
            
            return {
                "content": answer_content,
                "confidence": confidence,
                "response_time_ms": response_time,
                "sources_used": len(retrieval_result.get("results", [])),
                "answer_type": question_type
            }
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {str(e)}")
            
            # Return fallback answer
            return {
                "content": "I'm having trouble accessing specific information right now. Could you rephrase your question or ask about something else?",
                "confidence": 0.3,
                "response_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "sources_used": 0,
                "answer_type": "fallback"
            }
    
    def _calculate_answer_confidence(self, retrieval_result: Dict[str, Any], question_type: str) -> float:
        """Calculate confidence score for the answer."""
        base_confidence = 0.5
        
        # Boost confidence based on retrieval quality
        if retrieval_result.get("success"):
            results = retrieval_result.get("results", [])
            if results:
                # Average relevance score
                avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results)
                base_confidence += avg_relevance * 0.3
                
                # Source credibility
                avg_credibility = sum(
                    r.get("source_verification", {}).get("credibility_score", 0.5)
                    for r in results
                ) / len(results)
                base_confidence += avg_credibility * 0.2
        
        # Adjust based on question type
        type_confidence_map = {
            "factual": 0.9,      # High confidence for factual questions
            "explanatory": 0.8,   # Good confidence for explanations
            "contextual": 0.85,   # High confidence for contextual questions
            "comparative": 0.7,   # Medium confidence for comparisons
            "opinion": 0.6,       # Lower confidence for opinion questions
            "procedural": 0.75    # Good confidence for procedures
        }
        
        type_multiplier = type_confidence_map.get(question_type, 0.7)
        final_confidence = base_confidence * type_multiplier
        
        return min(1.0, final_confidence)
    
    async def _create_citation_chips(
        self, 
        retrieval_result: Dict[str, Any], 
        current_location: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create holographic citation chips for VR display."""
        
        citation_chips = []
        
        if not retrieval_result.get("success") or not retrieval_result.get("results"):
            return citation_chips
        
        for i, result in enumerate(retrieval_result["results"][:3]):  # Max 3 chips
            source = result.get("source", {})
            
            # Calculate chip position in VR space
            chip_position = self._calculate_chip_position(i, current_location)
            
            chip = {
                "id": f"citation_{i+1}",
                "position": chip_position,
                "source_title": source.get("title", "Unknown Source"),
                "source_type": source.get("type", "unknown"),
                "credibility_score": source.get("credibility_score", 0.5),
                "relevance_score": result.get("relevance_score", 0.5),
                "preview_text": result.get("content", "")[:100] + "...",
                "full_citation": source.get("formatted", "Unknown Source"),
                "visual_style": self._get_chip_visual_style(source.get("credibility_score", 0.5)),
                "interaction_type": "hover_expand",
                "display_duration": 30  # seconds
            }
            
            citation_chips.append(chip)
        
        return citation_chips
    
    def _calculate_chip_position(self, chip_index: int, current_location: Dict[str, Any]) -> Dict[str, float]:
        """Calculate 3D position for citation chip in VR space."""
        
        # Base position relative to user
        base_positions = [
            {"x": 1.5, "y": 1.8, "z": -2.0},   # Right side
            {"x": -1.5, "y": 1.8, "z": -2.0},  # Left side
            {"x": 0.0, "y": 2.2, "z": -2.5}    # Above center
        ]
        
        if chip_index < len(base_positions):
            return base_positions[chip_index]
        else:
            # Additional positions for more chips
            return {"x": 0.0, "y": 1.5, "z": -3.0}
    
    def _get_chip_visual_style(self, credibility_score: float) -> Dict[str, Any]:
        """Get visual style for citation chip based on credibility."""
        
        if credibility_score >= 0.8:
            return {
                "color": "#4CAF50",  # Green for high credibility
                "opacity": 0.9,
                "glow_intensity": 0.8,
                "border_style": "solid"
            }
        elif credibility_score >= 0.6:
            return {
                "color": "#FF9800",  # Orange for medium credibility
                "opacity": 0.8,
                "glow_intensity": 0.6,
                "border_style": "dashed"
            }
        else:
            return {
                "color": "#F44336",  # Red for low credibility
                "opacity": 0.7,
                "glow_intensity": 0.4,
                "border_style": "dotted"
            }
    
    async def _generate_follow_up_questions(
        self,
        original_question: str,
        answer: Dict[str, Any],
        context: TourContext,
        tour_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate relevant follow-up questions."""
        
        follow_ups = []
        
        # Generate contextual follow-ups based on current location
        current_location = tour_context.get("location_name", "this location")
        
        # Location-specific follow-ups
        follow_ups.extend([
            {
                "question": f"What else happened at {current_location}?",
                "type": "contextual",
                "relevance": 0.8
            },
            {
                "question": f"Who were the important people associated with {current_location}?",
                "type": "factual",
                "relevance": 0.7
            }
        ])
        
        # Interest-based follow-ups
        user_interests = context.user_preferences.get("interests", [])
        
        if "architecture" in user_interests:
            follow_ups.append({
                "question": "What architectural style is this building?",
                "type": "factual",
                "relevance": 0.9
            })
        
        if "history" in user_interests:
            follow_ups.append({
                "question": "What historical events took place here?",
                "type": "factual",
                "relevance": 0.9
            })
        
        if "culture" in user_interests:
            follow_ups.append({
                "question": "How did people live and work in this space?",
                "type": "explanatory",
                "relevance": 0.8
            })
        
        # Question-type specific follow-ups
        question_type = self._classify_question(original_question)
        
        if question_type == "factual":
            follow_ups.append({
                "question": "Why was this significant?",
                "type": "explanatory",
                "relevance": 0.7
            })
        elif question_type == "explanatory":
            follow_ups.append({
                "question": "Can you show me an example of this?",
                "type": "contextual",
                "relevance": 0.8
            })
        
        # Sort by relevance and return top 3
        follow_ups.sort(key=lambda x: x["relevance"], reverse=True)
        return follow_ups[:3]
    
    async def _generate_fallback_response(self, question: str, context: TourContext) -> Dict[str, Any]:
        """Generate a fallback response when main processing fails."""
        
        fallback_responses = [
            "That's an interesting question! Let me help you explore this location to find more information.",
            "I'd love to help you learn more about that. Try looking around for visual clues that might provide answers.",
            "Great question! While I gather more specific information, what do you notice about your current surroundings?",
            "I'm working on finding the best answer for you. In the meantime, feel free to explore and ask about anything you see."
        ]
        
        # Select response based on question length (simple heuristic)
        response_index = min(len(question) % len(fallback_responses), len(fallback_responses) - 1)
        
        return {
            "content": fallback_responses[response_index],
            "confidence": 0.3,
            "type": "fallback",
            "suggestions": [
                "Try rephrasing your question",
                "Ask about something specific you can see",
                "Explore the current location for more context"
            ]
        }
