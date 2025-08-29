"""
Core ingestion processor that orchestrates document and media processing.
"""

import asyncio
import logging
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from .parsers import DocumentParser, MediaParser
from .ocr import OCRProcessor
from .transcription import TranscriptionProcessor
from ..shared.database import Database
from ..shared.nats_client import NATSClient
from ..shared.storage import StorageClient
from ..shared.config import Settings

logger = logging.getLogger(__name__)


class IngestProcessor:
    """Main processor for document and media ingestion."""
    
    def __init__(self, db: Database, nats: NATSClient, storage: StorageClient, settings: Settings):
        self.db = db
        self.nats = nats
        self.storage = storage
        self.settings = settings
        
        # Initialize processors
        self.doc_parser = DocumentParser()
        self.media_parser = MediaParser()
        self.ocr_processor = OCRProcessor()
        self.transcription_processor = TranscriptionProcessor()
        
        # Processing status cache
        self.processing_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the processor."""
        logger.info("Initializing ingest processor")
        
        # Subscribe to NATS topics
        await self.nats.subscribe("doc.ingest", self._handle_ingest_message)
        await self.nats.subscribe("doc.reprocess", self._handle_reprocess_message)
        
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up ingest processor")
        
    def _generate_document_id(self, content: bytes, filename: str) -> str:
        """Generate a unique document ID based on content hash."""
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        return f"doc_{content_hash}_{uuid4().hex[:8]}"
        
    async def process_document(self, request, content: bytes, filename: str) -> Dict[str, Any]:
        """Process a document file."""
        document_id = self._generate_document_id(content, filename)
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing document {document_id}: {filename}")
            
            # Update processing status
            self.processing_status[document_id] = {
                "status": "processing",
                "stage": "parsing",
                "start_time": start_time,
                "filename": filename
            }
            
            # Determine content type
            content_type = request.content_type or mimetypes.guess_type(filename)[0]
            
            # Store original file
            file_key = f"documents/{request.tenant_id}/{document_id}/{filename}"
            await self.storage.upload_file(file_key, content, content_type)
            
            # Parse document content
            parsed_content = await self.doc_parser.parse(content, content_type, filename)
            
            # OCR if needed (for images or scanned PDFs)
            if parsed_content.get("needs_ocr", False):
                self.processing_status[document_id]["stage"] = "ocr"
                ocr_text = await self.ocr_processor.extract_text(content, content_type)
                parsed_content["text"] = ocr_text
                
            # Create document record
            document_data = {
                "id": document_id,
                "tenant_id": request.tenant_id,
                "site_id": request.site_id,
                "title": request.title,
                "content": parsed_content.get("text", ""),
                "content_type": content_type,
                "source_url": request.source_url,
                "metadata": {
                    **request.metadata,
                    "filename": filename,
                    "file_size": len(content),
                    "file_key": file_key,
                    "parsed_metadata": parsed_content.get("metadata", {}),
                    "processing_time_ms": 0  # Will be updated
                }
            }
            
            # Save to database
            await self.db.create_document(document_data)
            
            # Chunk content for embeddings
            self.processing_status[document_id]["stage"] = "chunking"
            chunks = await self._chunk_content(
                parsed_content.get("text", ""),
                document_id,
                request.tenant_id
            )
            
            # Publish to embedding worker
            await self.nats.publish("index.upsert", {
                "document_id": document_id,
                "tenant_id": request.tenant_id,
                "chunks": chunks
            })
            
            # Update processing status
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.processing_status[document_id] = {
                "status": "completed",
                "stage": "done",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "processing_time_ms": processing_time,
                "chunks_created": len(chunks),
                "filename": filename
            }
            
            # Update document with processing time
            await self.db.update_document(document_id, {
                "metadata": {
                    **document_data["metadata"],
                    "processing_time_ms": processing_time
                }
            })
            
            logger.info(f"Document {document_id} processed successfully in {processing_time}ms")
            
            return {
                "document_id": document_id,
                "status": "completed",
                "chunks_created": len(chunks),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Update error status
            self.processing_status[document_id] = {
                "status": "error",
                "stage": "failed",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "error": str(e),
                "filename": filename
            }
            
            raise e
            
    async def process_media(self, request, content: bytes, filename: str) -> Dict[str, Any]:
        """Process a media file."""
        document_id = self._generate_document_id(content, filename)
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing media {document_id}: {filename}")
            
            # Update processing status
            self.processing_status[document_id] = {
                "status": "processing",
                "stage": "parsing",
                "start_time": start_time,
                "filename": filename
            }
            
            # Determine content type
            content_type = request.content_type or mimetypes.guess_type(filename)[0]
            media_type = request.metadata.get("media_type", "unknown")
            
            # Store original file
            file_key = f"media/{request.tenant_id}/{document_id}/{filename}"
            await self.storage.upload_file(file_key, content, content_type)
            
            # Parse media content
            parsed_content = await self.media_parser.parse(content, content_type, filename)
            
            extracted_text = ""
            
            # Process based on media type
            if media_type == "image":
                # OCR for images
                self.processing_status[document_id]["stage"] = "ocr"
                extracted_text = await self.ocr_processor.extract_text(content, content_type)
                
            elif media_type in ["audio", "video"]:
                # Transcription for audio/video
                self.processing_status[document_id]["stage"] = "transcription"
                extracted_text = await self.transcription_processor.transcribe(content, content_type)
                
            # Create document record
            document_data = {
                "id": document_id,
                "tenant_id": request.tenant_id,
                "site_id": request.site_id,
                "title": request.title,
                "content": extracted_text,
                "content_type": content_type,
                "source_url": request.source_url,
                "metadata": {
                    **request.metadata,
                    "filename": filename,
                    "file_size": len(content),
                    "file_key": file_key,
                    "media_type": media_type,
                    "parsed_metadata": parsed_content.get("metadata", {}),
                    "processing_time_ms": 0
                }
            }
            
            # Save to database
            await self.db.create_document(document_data)
            
            # Chunk content if we have text
            chunks = []
            if extracted_text:
                self.processing_status[document_id]["stage"] = "chunking"
                chunks = await self._chunk_content(
                    extracted_text,
                    document_id,
                    request.tenant_id
                )
                
                # Publish to embedding worker
                await self.nats.publish("index.upsert", {
                    "document_id": document_id,
                    "tenant_id": request.tenant_id,
                    "chunks": chunks
                })
            
            # Update processing status
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.processing_status[document_id] = {
                "status": "completed",
                "stage": "done",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "processing_time_ms": processing_time,
                "chunks_created": len(chunks),
                "filename": filename
            }
            
            logger.info(f"Media {document_id} processed successfully in {processing_time}ms")
            
            return {
                "document_id": document_id,
                "status": "completed",
                "chunks_created": len(chunks),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing media {document_id}: {str(e)}")
            
            # Update error status
            self.processing_status[document_id] = {
                "status": "error",
                "stage": "failed",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "error": str(e),
                "filename": filename
            }
            
            raise e
            
    async def process_url(self, request) -> Dict[str, Any]:
        """Process content from a URL."""
        # Implementation for URL processing
        # This would fetch content from the URL and process it
        pass
        
    async def _chunk_content(self, text: str, document_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Chunk text content for embedding."""
        if not text.strip():
            return []
            
        # Simple chunking strategy - can be enhanced with more sophisticated methods
        chunk_size = 1000
        chunk_overlap = 200
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk_text = text[start:start + break_point + 1]
                    end = start + break_point + 1
                    
            chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "content": chunk_text.strip(),
                "metadata": {
                    "start_char": start,
                    "end_char": end,
                    "chunk_size": len(chunk_text)
                }
            })
            
            start = end - chunk_overlap
            chunk_index += 1
            
        return chunks
        
    async def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """Get the processing status of a document."""
        return self.processing_status.get(document_id, {"status": "not_found"})
        
    async def delete_document(self, document_id: str, tenant_id: str):
        """Delete a document and its associated data."""
        # Delete from database
        await self.db.delete_document(document_id, tenant_id)
        
        # Delete from storage
        # This would delete the stored files
        
        # Publish deletion event
        await self.nats.publish("doc.deleted", {
            "document_id": document_id,
            "tenant_id": tenant_id
        })
        
    async def _handle_ingest_message(self, message: Dict[str, Any]):
        """Handle ingest messages from NATS."""
        # Handle async ingest requests
        pass
        
    async def _handle_reprocess_message(self, message: Dict[str, Any]):
        """Handle reprocess messages from NATS."""
        # Handle reprocessing requests
        pass
