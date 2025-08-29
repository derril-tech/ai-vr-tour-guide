"""
Telemetry Worker FastAPI Application

Collects user behavior data and generates analytics reports.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import TelemetryProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processor: TelemetryProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    processor = TelemetryProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Telemetry worker started successfully")
    yield
    
    if processor:
        await processor.cleanup()
    logger.info("Telemetry worker stopped")

app = FastAPI(
    title="AI VR Tour Guide - Telemetry Worker",
    description="User behavior analytics and reporting",
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

class TelemetryEvent(BaseModel):
    event_type: str
    session_id: str
    user_id: str
    site_id: str
    tenant_id: str
    timestamp: str
    data: Dict[str, Any]
    position: List[float] = None
    comfort_score: float = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "telemetry-worker"}

@app.post("/events/track")
async def track_event(event: TelemetryEvent):
    try:
        result = await processor.track_event(event)
        return result
    except Exception as e:
        logger.error(f"Error tracking event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    site_id: str,
    tenant_id: str,
    report_type: str = "comprehensive",
    date_range: Dict[str, str] = None
):
    try:
        background_tasks.add_task(
            processor.generate_report,
            site_id, tenant_id, report_type, date_range
        )
        return {"status": "accepted", "message": "Report generation started"}
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
