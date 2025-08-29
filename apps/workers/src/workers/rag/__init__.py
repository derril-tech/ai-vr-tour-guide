"""
RAG Worker

Hybrid retrieval system with BM25 + embeddings + reranking for vetted sources.
Provides high-quality, cited information retrieval for the AI tour guide.
"""

from .main import app
from .processor import RAGProcessor
from .hybrid_retriever import HybridRetriever
from .reranker import DocumentReranker
from .source_verifier import SourceVerifier

__all__ = [
    "app",
    "RAGProcessor",
    "HybridRetriever",
    "DocumentReranker",
    "SourceVerifier",
]
