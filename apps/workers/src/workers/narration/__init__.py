"""
Narration Worker

Advanced narration generation with citations, quiz injection, and adaptive storytelling.
Integrates with TTS for voice synthesis and supports multiple languages and accessibility features.
"""

from .main import app
from .processor import NarrationProcessor
from .citation_manager import CitationManager
from .quiz_injector import QuizInjector
from .story_adapter import StoryAdapter

__all__ = [
    "app",
    "NarrationProcessor",
    "CitationManager",
    "QuizInjector", 
    "StoryAdapter",
]
