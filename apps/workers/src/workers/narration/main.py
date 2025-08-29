"""
Narration Worker FastAPI Application

Generates contextual narrations with citations and quiz integration.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import NarrationProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor: NarrationProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    processor = NarrationProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Narration worker started successfully")
    yield
    
    if processor:
        await processor.cleanup()
    logger.info("Narration worker stopped")

app = FastAPI(
    title="AI VR Tour Guide - Narration Worker",
    description="Advanced narration generation with citations and quiz integration",
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

class NarrationRequest(BaseModel):
    site_id: str
    tenant_id: str
    waypoint_id: str
    content_data: Dict[str, Any]
    user_context: Dict[str, Any]
    style: str = "storytelling"
    duration_seconds: int = 60
    language: str = "en"
    include_quiz: bool = True
    citation_style: str = "conversational"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "narration-worker"}

@app.post("/generate")
async def generate_narration(request: NarrationRequest):
    try:
        result = await processor.generate_narration(request)
        return result
    except Exception as e:
        logger.error(f"Error generating narration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inject-quiz")
async def inject_quiz_elements(
    narration_text: str,
    content_data: Dict[str, Any],
    difficulty: str = "medium",
    max_questions: int = 3
):
    try:
        result = await processor.inject_quiz_elements(
            narration_text, content_data, difficulty, max_questions
        )
        return result
    except Exception as e:
        logger.error(f"Error injecting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/adapt-style")
async def adapt_narration_style(
    base_narration: str,
    target_style: str,
    user_preferences: Dict[str, Any]
):
    try:
        result = await processor.adapt_narration_style(
            base_narration, target_style, user_preferences
        )
        return result
    except Exception as e:
        logger.error(f"Error adapting style: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
