"""
Guardrails Worker FastAPI Application

Provides content safety, cultural sensitivity, and citation enforcement.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import GuardrailsProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor: GuardrailsProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    processor = GuardrailsProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Guardrails worker started successfully")
    yield
    
    if processor:
        await processor.cleanup()
    logger.info("Guardrails worker stopped")

app = FastAPI(
    title="AI VR Tour Guide - Guardrails Worker",
    description="Content safety and citation enforcement",
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

class ContentCheckRequest(BaseModel):
    content: str
    content_type: str = "narration"
    language: str = "en"
    cultural_context: str = "general"
    strictness_level: str = "medium"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "guardrails-worker"}

@app.post("/check-content")
async def check_content(request: ContentCheckRequest):
    try:
        result = await processor.check_content(request)
        return result
    except Exception as e:
        logger.error(f"Error checking content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enforce-citations")
async def enforce_citations(
    content: str,
    sources: List[Dict[str, Any]],
    citation_style: str = "inline"
):
    try:
        result = await processor.enforce_citations(content, sources, citation_style)
        return result
    except Exception as e:
        logger.error(f"Error enforcing citations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
