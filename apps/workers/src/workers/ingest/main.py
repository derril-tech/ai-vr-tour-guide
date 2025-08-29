"""
Ingest Worker FastAPI Application

Handles document and media ingestion for the AI VR Tour Guide platform.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import IngestProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global processor instance
processor: IngestProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global processor
    
    # Initialize services
    settings = get_settings()
    db = await get_database()
    nats = await get_nats_client()
    storage = get_storage_client()
    
    # Initialize processor
    processor = IngestProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("Ingest worker started successfully")
    yield
    
    # Cleanup
    if processor:
        await processor.cleanup()
    logger.info("Ingest worker stopped")


# Create FastAPI app
app = FastAPI(
    title="AI VR Tour Guide - Ingest Worker",
    description="Document and media ingestion pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    site_id: str
    tenant_id: str
    title: str
    source_url: str = None
    content_type: str = None
    metadata: Dict[str, Any] = {}


class IngestResponse(BaseModel):
    """Response model for ingestion requests."""
    document_id: str
    status: str
    message: str
    chunks_created: int = 0
    processing_time_ms: int = 0


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ingest-worker"}


@app.post("/ingest/document", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    site_id: str = Form(...),
    tenant_id: str = Form(...),
    title: str = Form(...),
    source_url: str = Form(None),
    metadata: str = Form("{}")  # JSON string
):
    """
    Ingest a document file.
    
    Supports: PDF, DOCX, TXT, HTML, MD
    """
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        request = IngestRequest(
            site_id=site_id,
            tenant_id=tenant_id,
            title=title,
            source_url=source_url,
            content_type=file.content_type,
            metadata=metadata_dict
        )
        
        # Read file content
        content = await file.read()
        
        # Process document in background
        background_tasks.add_task(
            processor.process_document,
            request,
            content,
            file.filename
        )
        
        return IngestResponse(
            document_id="pending",  # Will be updated when processing completes
            status="accepted",
            message="Document queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/media", response_model=IngestResponse)
async def ingest_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    site_id: str = Form(...),
    tenant_id: str = Form(...),
    title: str = Form(...),
    media_type: str = Form(...),  # image, audio, video
    metadata: str = Form("{}")
):
    """
    Ingest a media file.
    
    Supports: Images (JPG, PNG, WEBP), Audio (MP3, WAV, M4A), Video (MP4, WEBM)
    """
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        request = IngestRequest(
            site_id=site_id,
            tenant_id=tenant_id,
            title=title,
            content_type=file.content_type,
            metadata={**metadata_dict, "media_type": media_type}
        )
        
        # Read file content
        content = await file.read()
        
        # Process media in background
        background_tasks.add_task(
            processor.process_media,
            request,
            content,
            file.filename
        )
        
        return IngestResponse(
            document_id="pending",
            status="accepted", 
            message="Media queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error ingesting media: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/url")
async def ingest_from_url(
    background_tasks: BackgroundTasks,
    request: IngestRequest
):
    """
    Ingest content from a URL.
    
    Supports web pages, documents, and media files.
    """
    try:
        if not request.source_url:
            raise HTTPException(status_code=400, detail="source_url is required")
        
        # Process URL in background
        background_tasks.add_task(
            processor.process_url,
            request
        )
        
        return IngestResponse(
            document_id="pending",
            status="accepted",
            message="URL queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error ingesting URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ingest/status/{document_id}")
async def get_ingest_status(document_id: str):
    """Get the status of a document ingestion."""
    try:
        status = await processor.get_processing_status(document_id)
        return status
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/ingest/{document_id}")
async def delete_document(document_id: str, tenant_id: str):
    """Delete a document and its associated data."""
    try:
        await processor.delete_document(document_id, tenant_id)
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
