"""
RAG Worker FastAPI Application

Provides hybrid retrieval with BM25 + embeddings + reranking for high-quality,
cited information retrieval.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .processor import RAGProcessor
from ..shared.database import get_database
from ..shared.nats_client import get_nats_client
from ..shared.storage import get_storage_client
from ..shared.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global processor instance
processor: RAGProcessor = None


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
    processor = RAGProcessor(db, nats, storage, settings)
    await processor.initialize()
    
    logger.info("RAG worker started successfully")
    yield
    
    # Cleanup
    if processor:
        await processor.cleanup()
    logger.info("RAG worker stopped")


# Create FastAPI app
app = FastAPI(
    title="AI VR Tour Guide - RAG Worker",
    description="Hybrid retrieval with BM25 + embeddings + reranking",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RetrievalRequest(BaseModel):
    """Request model for document retrieval."""
    query: str
    site_id: str
    tenant_id: str
    max_results: int = 10
    retrieval_mode: str = "hybrid"  # "bm25", "vector", "hybrid"
    rerank: bool = True
    source_filter: List[str] = []  # Filter by source types
    min_score: float = 0.0
    include_metadata: bool = True


class IndexRequest(BaseModel):
    """Request model for document indexing."""
    documents: List[Dict[str, Any]]
    site_id: str
    tenant_id: str
    update_existing: bool = True


class RetrievalResponse(BaseModel):
    """Response model for retrieval requests."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    retrieval_time_ms: int
    retrieval_mode: str
    reranked: bool


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-worker"}


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(request: RetrievalRequest):
    """
    Retrieve relevant documents using hybrid search.
    
    Combines BM25 lexical search with vector semantic search,
    then applies reranking for optimal results.
    """
    try:
        result = await processor.retrieve_documents(request)
        return RetrievalResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in document retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def index_documents(
    background_tasks: BackgroundTasks,
    request: IndexRequest
):
    """
    Index documents for retrieval.
    
    Creates both BM25 and vector indexes for hybrid search.
    """
    try:
        # Process indexing in background
        background_tasks.add_task(
            processor.index_documents,
            request
        )
        
        return {
            "status": "accepted",
            "message": "Document indexing started",
            "document_count": len(request.documents),
            "site_id": request.site_id
        }
        
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rerank")
async def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    model: str = "cross_encoder"
):
    """
    Rerank documents for a given query.
    
    Uses cross-encoder models for precise relevance scoring.
    """
    try:
        reranked_docs = await processor.rerank_documents(query, documents, model)
        
        return {
            "query": query,
            "reranked_documents": reranked_docs,
            "model_used": model,
            "document_count": len(reranked_docs)
        }
        
    except Exception as e:
        logger.error(f"Error reranking documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    tenant_id: str,
    max_results: int = 5,
    similarity_threshold: float = 0.7
):
    """Find documents similar to a given document."""
    try:
        similar_docs = await processor.find_similar_documents(
            document_id, tenant_id, max_results, similarity_threshold
        )
        
        return {
            "document_id": document_id,
            "similar_documents": similar_docs,
            "similarity_threshold": similarity_threshold,
            "result_count": len(similar_docs)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify/sources")
async def verify_sources(
    sources: List[Dict[str, Any]],
    verification_level: str = "standard"  # "basic", "standard", "strict"
):
    """
    Verify the credibility and accuracy of sources.
    
    Checks source authority, recency, citations, and cross-references.
    """
    try:
        verification_results = await processor.verify_sources(sources, verification_level)
        
        return {
            "verification_level": verification_level,
            "sources_verified": len(sources),
            "results": verification_results,
            "overall_credibility": sum(r.get("credibility_score", 0) for r in verification_results) / len(verification_results) if verification_results else 0
        }
        
    except Exception as e:
        logger.error(f"Error verifying sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/retrieval")
async def get_retrieval_analytics(
    site_id: str,
    tenant_id: str,
    days: int = 7
):
    """Get retrieval analytics and performance metrics."""
    try:
        analytics = await processor.get_retrieval_analytics(site_id, tenant_id, days)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/index/{site_id}")
async def delete_site_index(site_id: str, tenant_id: str):
    """Delete all indexed documents for a site."""
    try:
        await processor.delete_site_index(site_id, tenant_id)
        return {"status": "deleted", "site_id": site_id}
        
    except Exception as e:
        logger.error(f"Error deleting site index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embeddings/generate")
async def generate_embeddings(
    texts: List[str],
    model: str = "text-embedding-ada-002"
):
    """Generate embeddings for given texts."""
    try:
        embeddings = await processor.generate_embeddings(texts, model)
        
        return {
            "model": model,
            "embeddings": embeddings,
            "text_count": len(texts),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0
        }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
