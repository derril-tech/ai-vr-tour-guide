"""
Audio/Video transcription processor for extracting text from media files.
"""

import io
import logging
import tempfile
import os
from typing import Optional, Dict, Any

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    logging.warning("OpenAI Whisper not available. Install openai-whisper for transcription.")

try:
    import openai
    HAS_OPENAI_API = True
except ImportError:
    HAS_OPENAI_API = False
    logging.warning("OpenAI API client not available.")

logger = logging.getLogger(__name__)


class TranscriptionProcessor:
    """Processor for transcribing audio and video content to text."""
    
    def __init__(self):
        self.whisper_available = HAS_WHISPER
        self.openai_api_available = HAS_OPENAI_API
        self.whisper_model = None
        
        # Initialize local Whisper model if available
        if self.whisper_available:
            try:
                # Load a medium-sized model for good balance of speed/accuracy
                self.whisper_model = whisper.load_model("medium")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load Whisper model: {e}")
                self.whisper_available = False
    
    async def transcribe(self, content: bytes, content_type: str, language: Optional[str] = None) -> str:
        """Transcribe audio/video content to text."""
        try:
            if not self.whisper_available and not self.openai_api_available:
                logger.error("No transcription engines available")
                return ""
            
            # Save content to temporary file
            temp_path = await self._save_to_temp_file(content, content_type)
            
            try:
                # Try local Whisper first
                if self.whisper_available and self.whisper_model:
                    try:
                        text = await self._transcribe_with_whisper(temp_path, language)
                        if text.strip():
                            logger.info("Successfully transcribed using local Whisper")
                            return text
                    except Exception as e:
                        logger.warning(f"Local Whisper failed: {e}")
                
                # Fallback to OpenAI API
                if self.openai_api_available:
                    try:
                        text = await self._transcribe_with_openai_api(temp_path, language)
                        if text.strip():
                            logger.info("Successfully transcribed using OpenAI API")
                            return text
                    except Exception as e:
                        logger.warning(f"OpenAI API transcription failed: {e}")
                
                logger.warning("No transcription engine could process the audio")
                return ""
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error in transcription processing: {str(e)}")
            return ""
    
    async def _save_to_temp_file(self, content: bytes, content_type: str) -> str:
        """Save content to a temporary file with appropriate extension."""
        # Determine file extension from content type
        extension_map = {
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/mp4': '.m4a',
            'audio/aac': '.aac',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'video/avi': '.avi',
        }
        
        extension = extension_map.get(content_type, '.tmp')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(content)
            return temp_file.name
    
    async def _transcribe_with_whisper(self, file_path: str, language: Optional[str] = None) -> str:
        """Transcribe using local Whisper model."""
        try:
            # Transcribe with Whisper
            options = {}
            if language:
                options['language'] = language
            
            result = self.whisper_model.transcribe(file_path, **options)
            
            # Extract text
            text = result.get('text', '').strip()
            
            # Log detected language and confidence if available
            if 'language' in result:
                logger.info(f"Detected language: {result['language']}")
            
            return text
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise e
    
    async def _transcribe_with_openai_api(self, file_path: str, language: Optional[str] = None) -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            # Check file size (OpenAI has a 25MB limit)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB
                logger.warning("File too large for OpenAI API, trying to compress")
                # Could implement audio compression here
                return ""
            
            # Open file and transcribe
            with open(file_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            return transcript.get('text', '').strip()
            
        except Exception as e:
            logger.error(f"OpenAI API transcription error: {str(e)}")
            raise e
    
    async def transcribe_with_timestamps(self, content: bytes, content_type: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe with word-level timestamps (useful for synchronization)."""
        try:
            if not self.whisper_available:
                logger.warning("Timestamp transcription requires local Whisper")
                return {"text": "", "segments": []}
            
            temp_path = await self._save_to_temp_file(content, content_type)
            
            try:
                options = {"word_timestamps": True}
                if language:
                    options['language'] = language
                
                result = self.whisper_model.transcribe(temp_path, **options)
                
                # Extract segments with timestamps
                segments = []
                for segment in result.get('segments', []):
                    segment_data = {
                        'start': segment.get('start', 0),
                        'end': segment.get('end', 0),
                        'text': segment.get('text', '').strip(),
                    }
                    
                    # Add word-level timestamps if available
                    if 'words' in segment:
                        segment_data['words'] = [
                            {
                                'start': word.get('start', 0),
                                'end': word.get('end', 0),
                                'word': word.get('word', '').strip(),
                                'probability': word.get('probability', 0)
                            }
                            for word in segment['words']
                        ]
                    
                    segments.append(segment_data)
                
                return {
                    "text": result.get('text', '').strip(),
                    "language": result.get('language', ''),
                    "segments": segments
                }
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error in timestamp transcription: {str(e)}")
            return {"text": "", "segments": []}
    
    async def extract_audio_from_video(self, video_content: bytes, content_type: str) -> bytes:
        """Extract audio track from video for transcription."""
        try:
            # This would use ffmpeg to extract audio
            # For now, return the original content
            # In a real implementation, you'd use ffmpeg-python or similar
            logger.warning("Audio extraction from video not implemented")
            return video_content
            
        except Exception as e:
            logger.error(f"Error extracting audio from video: {str(e)}")
            return b""
    
    def is_available(self) -> bool:
        """Check if transcription functionality is available."""
        return self.whisper_available or self.openai_api_available
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages for transcription."""
        # Whisper supports many languages
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 
            'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi'
        ]
    
    async def detect_language(self, content: bytes, content_type: str) -> Optional[str]:
        """Detect the language of audio content."""
        try:
            if not self.whisper_available:
                return None
            
            temp_path = await self._save_to_temp_file(content, content_type)
            
            try:
                # Load audio and detect language
                audio = whisper.load_audio(temp_path)
                audio = whisper.pad_or_trim(audio)
                
                # Make log-Mel spectrogram and move to the same device as the model
                mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)
                
                # Detect the spoken language
                _, probs = self.whisper_model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
                
                logger.info(f"Detected language: {detected_language} (confidence: {probs[detected_language]:.2f})")
                
                return detected_language
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return None
