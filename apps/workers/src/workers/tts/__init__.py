"""
TTS Worker

Text-to-Speech with multilingual support, viseme generation for lip-sync,
and adaptive voice characteristics based on content and user preferences.
"""

from .main import app
from .processor import TTSProcessor
from .voice_manager import VoiceManager
from .viseme_generator import VisemeGenerator
from .audio_processor import AudioProcessor

__all__ = [
    "app",
    "TTSProcessor",
    "VoiceManager",
    "VisemeGenerator",
    "AudioProcessor",
]
