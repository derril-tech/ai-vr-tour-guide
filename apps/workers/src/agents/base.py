"""Base agent class with common functionality."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from uuid import uuid4

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentMetrics(BaseModel):
    """Metrics for agent performance tracking."""
    agent_id: str
    agent_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


class TourContext(BaseModel):
    """Context information for tour agents."""
    site_id: str
    tour_id: str
    user_id: str
    tenant_id: str
    session_id: str
    current_position: Optional[Dict[str, float]] = None
    visited_hotspots: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    accessibility_needs: List[str] = Field(default_factory=list)


class AgentCallback(BaseCallbackHandler):
    """Callback handler for tracking agent metrics."""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.start_time = datetime.utcnow()
        self.tokens_used = 0
        self.cost_usd = 0.0
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        logger.debug(f"Agent {self.agent_id} starting LLM call")
        
    def on_llm_end(self, response, **kwargs) -> None:
        # Track token usage if available
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            self.tokens_used += token_usage.get('total_tokens', 0)
            
    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs) -> None:
        logger.error(f"Agent {self.agent_id} LLM error: {error}")
        
    def get_metrics(self) -> AgentMetrics:
        """Get current metrics for this agent run."""
        end_time = datetime.utcnow()
        duration_ms = int((end_time - self.start_time).total_seconds() * 1000)
        
        return AgentMetrics(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            start_time=self.start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            tokens_used=self.tokens_used,
            cost_usd=self.cost_usd,
            success=True
        )


class BaseAgent(ABC):
    """Base class for all tour guide agents."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_id = str(uuid4())
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result."""
        pass
        
    def create_callback(self) -> AgentCallback:
        """Create a callback handler for this agent."""
        return AgentCallback(self.agent_id, self.__class__.__name__)
        
    async def _safe_process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Safely process input with error handling and metrics."""
        callback = self.create_callback()
        
        try:
            self.logger.info(f"Agent {self.name} starting processing for session {context.session_id}")
            result = await self.process(context, input_data)
            
            # Add metrics to result
            metrics = callback.get_metrics()
            result["_metrics"] = metrics.dict()
            
            self.logger.info(f"Agent {self.name} completed successfully in {metrics.duration_ms}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} failed: {str(e)}", exc_info=True)
            
            # Return error result with metrics
            metrics = callback.get_metrics()
            metrics.success = False
            metrics.error = str(e)
            
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "_metrics": metrics.dict()
            }
    
    def format_messages(self, system_prompt: str, user_message: str, 
                       chat_history: Optional[List[BaseMessage]] = None) -> List[BaseMessage]:
        """Format messages for LLM input."""
        messages = [SystemMessage(content=system_prompt)]
        
        if chat_history:
            messages.extend(chat_history)
            
        messages.append(HumanMessage(content=user_message))
        return messages