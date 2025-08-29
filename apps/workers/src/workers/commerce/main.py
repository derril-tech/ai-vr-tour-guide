"""
Commerce Worker FastAPI Application

Handles tour monetization, licensing, and access control.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import CommerceProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor: CommerceProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    processor = CommerceProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Commerce worker started successfully")
    yield
    
    if processor:
        await processor.cleanup()
    logger.info("Commerce worker stopped")

app = FastAPI(
    title="AI VR Tour Guide - Commerce Worker",
    description="Tour monetization and access control",
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

class PurchaseRequest(BaseModel):
    user_id: str
    tenant_id: str
    sku: str
    payment_method: str
    billing_info: Dict[str, Any]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "commerce-worker"}

@app.post("/purchase")
async def process_purchase(request: PurchaseRequest):
    try:
        result = await processor.process_purchase(request)
        return result
    except Exception as e:
        logger.error(f"Error processing purchase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/access/check")
async def check_access(user_id: str, site_id: str, feature: str = None):
    try:
        result = await processor.check_access(user_id, site_id, feature)
        return result
    except Exception as e:
        logger.error(f"Error checking access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
