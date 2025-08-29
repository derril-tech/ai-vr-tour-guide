"""
TTS Worker FastAPI Application

Provides text-to-speech with multilingual support and viseme generation.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .processor import TTSProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor: TTSProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    processor = TTSProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("TTS worker started successfully")
    yield
    
    if processor:
        await processor.cleanup()
    logger.info("TTS worker stopped")

app = FastAPI(
    title="AI VR Tour Guide - TTS Worker",
    description="Text-to-speech with multilingual support and viseme generation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    emotion: str = "neutral"
    generate_visemes: bool = True
    audio_format: str = "mp3"
    quality: str = "high"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tts-worker"}

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    try:
        result = await processor.synthesize_speech(request)
        return result
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-visemes")
async def generate_visemes(
    text: str,
    language: str = "en",
    timing_precision: str = "phoneme"
):
    try:
        result = await processor.generate_visemes(text, language, timing_precision)
        return result
    except Exception as e:
        logger.error(f"Error generating visemes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
async def list_available_voices(language: str = None):
    try:
        voices = await processor.list_available_voices(language)
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
