"""
Knowledge Retriever Agent

Retrieves relevant information from the knowledge base using hybrid search
(BM25 + embeddings + reranking) with source verification and citation tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever

from .base import BaseAgent, TourContext

logger = logging.getLogger(__name__)


class KnowledgeRetrieverAgent(BaseAgent):
    """Agent responsible for retrieving relevant knowledge with citations."""
    
    def __init__(self):
        super().__init__(
            name="KnowledgeRetriever",
            description="Retrieves relevant information using hybrid search with source verification"
        )
        
        # Initialize components
        self.llm = OpenAI(temperature=0.1)
        self.embeddings = OpenAIEmbeddings()
        
        # Retrieval components (will be initialized with site data)
        self.vector_store = None
        self.bm25_retriever = None
        self.ensemble_retriever = None
        self.compression_retriever = None
        
        # Source verification settings
        self.min_relevance_score = 0.7
        self.max_results = 10
        self.citation_required = True
        
    async def process(self, context: TourContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process knowledge retrieval request."""
        try:
            query = input_data.get("query", "")
            query_type = input_data.get("query_type", "general")  # general, factual, contextual
            max_results = input_data.get("max_results", self.max_results)
            
            if not query:
                return {"success": False, "error": "No query provided"}
            
            # Initialize retrievers for the site if not already done
            await self._ensure_retrievers_initialized(context.site_id, context.tenant_id)
            
            # Perform hybrid retrieval
            retrieved_docs = await self._hybrid_retrieve(query, max_results)
            
            # Rerank and filter results
            ranked_results = await self._rerank_results(query, retrieved_docs, query_type)
            
            # Verify sources and add citations
            verified_results = await self._verify_and_cite_sources(ranked_results, context)
            
            # Extract key information
            key_info = await self._extract_key_information(query, verified_results)
            
            return {
                "success": True,
                "query": query,
                "results": verified_results,
                "key_information": key_info,
                "result_count": len(verified_results),
                "sources": [r["source"] for r in verified_results],
                "confidence_score": self._calculate_confidence_score(verified_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error in knowledge retrieval: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_info": await self._get_fallback_information(context, input_data.get("query", ""))
            }
    
    async def _ensure_retrievers_initialized(self, site_id: str, tenant_id: str):
        """Ensure retrievers are initialized for the site."""
        if self.vector_store is None:
            # Load site documents
            documents = await self._load_site_documents(site_id, tenant_id)
            
            if documents:
                # Initialize vector store
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                
                # Initialize BM25 retriever
                self.bm25_retriever = BM25Retriever.from_documents(documents)
                
                # Create ensemble retriever (combines vector and BM25)
                vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=[self.bm25_retriever, vector_retriever],
                    weights=[0.4, 0.6]  # Favor vector search slightly
                )
                
                # Add compression/reranking
                compressor = LLMChainExtractor.from_llm(self.llm)
                self.compression_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor,
                    base_retriever=self.ensemble_retriever
                )
                
                self.logger.info(f"Initialized retrievers for site {site_id} with {len(documents)} documents")
            else:
                self.logger.warning(f"No documents found for site {site_id}")
    
    async def _hybrid_retrieve(self, query: str, max_results: int) -> List[Document]:
        """Perform hybrid retrieval using ensemble of retrievers."""
        if not self.compression_retriever:
            return []
        
        try:
            # Use compression retriever for best results
            docs = await self.compression_retriever.aget_relevant_documents(query)
            
            # Limit results
            return docs[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in hybrid retrieval: {str(e)}")
            
            # Fallback to basic vector search
            if self.vector_store:
                return self.vector_store.similarity_search(query, k=max_results)
            
            return []
    
    async def _rerank_results(self, query: str, documents: List[Document], query_type: str) -> List[Dict[str, Any]]:
        """Rerank results based on relevance and query type."""
        ranked_results = []
        
        for i, doc in enumerate(documents):
            # Calculate relevance score
            relevance_score = await self._calculate_relevance_score(query, doc, query_type)
            
            # Extract metadata
            metadata = doc.metadata or {}
            
            result = {
                "content": doc.page_content,
                "relevance_score": relevance_score,
                "rank": i + 1,
                "document_id": metadata.get("document_id", f"doc_{i}"),
                "source_type": metadata.get("source_type", "unknown"),
                "title": metadata.get("title", "Untitled"),
                "chunk_index": metadata.get("chunk_index", 0),
                "metadata": metadata
            }
            
            # Only include results above minimum relevance threshold
            if relevance_score >= self.min_relevance_score:
                ranked_results.append(result)
        
        # Sort by relevance score
        ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return ranked_results
    
    async def _calculate_relevance_score(self, query: str, document: Document, query_type: str) -> float:
        """Calculate relevance score for a document."""
        # This is a simplified scoring function
        # In a real implementation, you might use a trained reranking model
        
        content = document.page_content.lower()
        query_lower = query.lower()
        
        # Basic keyword matching
        query_words = query_lower.split()
        content_words = content.split()
        
        # Calculate word overlap
        overlap = len(set(query_words) & set(content_words))
        word_score = overlap / len(query_words) if query_words else 0
        
        # Boost score based on query type
        type_boost = 1.0
        if query_type == "factual":
            # Look for specific facts, dates, numbers
            if any(word.isdigit() or word in ["when", "where", "who", "what"] for word in query_words):
                if any(word.isdigit() for word in content_words):
                    type_boost = 1.2
        elif query_type == "contextual":
            # Favor longer, more detailed content
            if len(content_words) > 100:
                type_boost = 1.1
        
        # Consider document metadata
        metadata = document.metadata or {}
        metadata_boost = 1.0
        
        # Boost authoritative sources
        if metadata.get("source_type") in ["academic", "official", "expert"]:
            metadata_boost = 1.15
        
        # Boost recent content
        if metadata.get("date"):
            # This would check recency in a real implementation
            pass
        
        final_score = word_score * type_boost * metadata_boost
        return min(1.0, final_score)
    
    async def _verify_and_cite_sources(self, results: List[Dict[str, Any]], context: TourContext) -> List[Dict[str, Any]]:
        """Verify sources and add proper citations."""
        verified_results = []
        
        for result in results:
            # Verify source credibility
            source_verification = await self._verify_source_credibility(result, context)
            
            # Add citation information
            citation = self._generate_citation(result)
            
            # Add verification and citation to result
            verified_result = {
                **result,
                "source_verification": source_verification,
                "citation": citation,
                "source": {
                    "title": result.get("title", "Unknown"),
                    "type": result.get("source_type", "unknown"),
                    "document_id": result.get("document_id"),
                    "credibility_score": source_verification.get("credibility_score", 0.5),
                    "verification_status": source_verification.get("status", "unverified")
                }
            }
            
            # Only include verified sources if citation is required
            if not self.citation_required or source_verification.get("status") == "verified":
                verified_results.append(verified_result)
        
        return verified_results
    
    async def _verify_source_credibility(self, result: Dict[str, Any], context: TourContext) -> Dict[str, Any]:
        """Verify the credibility of a source."""
        metadata = result.get("metadata", {})
        
        # Source credibility factors
        credibility_score = 0.5  # Base score
        verification_factors = []
        
        # Check source type
        source_type = metadata.get("source_type", "unknown")
        if source_type in ["academic", "official", "museum", "expert"]:
            credibility_score += 0.3
            verification_factors.append("authoritative_source")
        elif source_type in ["news", "educational"]:
            credibility_score += 0.2
            verification_factors.append("reliable_source")
        
        # Check for author credentials
        if metadata.get("author"):
            credibility_score += 0.1
            verification_factors.append("attributed_author")
        
        # Check for publication date
        if metadata.get("date"):
            credibility_score += 0.1
            verification_factors.append("dated_content")
        
        # Check for citations/references
        if metadata.get("references") or "reference" in result.get("content", "").lower():
            credibility_score += 0.1
            verification_factors.append("contains_references")
        
        # Determine verification status
        if credibility_score >= 0.8:
            status = "verified"
        elif credibility_score >= 0.6:
            status = "likely_reliable"
        else:
            status = "unverified"
        
        return {
            "status": status,
            "credibility_score": min(1.0, credibility_score),
            "verification_factors": verification_factors,
            "verification_date": datetime.utcnow().isoformat()
        }
    
    def _generate_citation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proper citation for a source."""
        metadata = result.get("metadata", {})
        
        citation = {
            "format": "apa",  # Could be configurable
            "title": result.get("title", "Untitled"),
            "author": metadata.get("author", "Unknown Author"),
            "date": metadata.get("date", "n.d."),
            "source_type": result.get("source_type", "unknown"),
            "document_id": result.get("document_id"),
            "chunk_reference": f"Section {result.get('chunk_index', 0) + 1}"
        }
        
        # Generate formatted citation
        if citation["author"] != "Unknown Author":
            formatted = f"{citation['author']} ({citation['date']}). {citation['title']}."
        else:
            formatted = f"{citation['title']} ({citation['date']})."
        
        citation["formatted"] = formatted
        
        return citation
    
    async def _extract_key_information(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key information from retrieved results."""
        if not results:
            return {"summary": "No relevant information found."}
        
        # Combine content from top results
        combined_content = "\n\n".join([r["content"] for r in results[:3]])
        
        # Use LLM to extract key information
        extraction_prompt = f"""
Based on the following retrieved information, extract the key points that answer this query: "{query}"

Retrieved Information:
{combined_content}

Please provide:
1. A concise summary (2-3 sentences)
2. Key facts (bullet points)
3. Important dates or numbers (if any)
4. Main concepts or themes

Key Information:
"""
        
        try:
            key_info_response = await self.llm.agenerate([extraction_prompt])
            key_info_text = key_info_response.generations[0][0].text.strip()
            
            return {
                "summary": key_info_text,
                "source_count": len(results),
                "confidence": self._calculate_confidence_score(results),
                "extraction_method": "llm_extraction"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting key information: {str(e)}")
            
            # Fallback to simple summary
            return {
                "summary": f"Found {len(results)} relevant sources about: {query}",
                "source_count": len(results),
                "confidence": self._calculate_confidence_score(results),
                "extraction_method": "fallback"
            }
    
    def _calculate_confidence_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for the retrieval."""
        if not results:
            return 0.0
        
        # Average relevance score
        avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results)
        
        # Source credibility factor
        avg_credibility = sum(
            r.get("source_verification", {}).get("credibility_score", 0.5) 
            for r in results
        ) / len(results)
        
        # Result count factor (more results = higher confidence, up to a point)
        count_factor = min(1.0, len(results) / 5.0)
        
        # Combined confidence score
        confidence = (avg_relevance * 0.4 + avg_credibility * 0.4 + count_factor * 0.2)
        
        return min(1.0, confidence)
    
    async def _load_site_documents(self, site_id: str, tenant_id: str) -> List[Document]:
        """Load documents for a site from the knowledge base."""
        # This would query the database for site documents
        # For now, return mock documents
        
        mock_documents = [
            Document(
                page_content="This is a historical building constructed in 1850. It served as the main administrative center for the region.",
                metadata={
                    "document_id": "doc_1",
                    "title": "Historical Overview",
                    "source_type": "official",
                    "author": "Site Historian",
                    "date": "2023-01-15",
                    "chunk_index": 0
                }
            ),
            Document(
                page_content="The architecture features Gothic Revival elements with pointed arches and ribbed vaults. The construction used local limestone.",
                metadata={
                    "document_id": "doc_2", 
                    "title": "Architectural Analysis",
                    "source_type": "academic",
                    "author": "Dr. Architecture Expert",
                    "date": "2023-03-20",
                    "chunk_index": 0
                }
            ),
            Document(
                page_content="Daily life in the 19th century involved early morning routines, manual labor, and community gatherings in the evening.",
                metadata={
                    "document_id": "doc_3",
                    "title": "Social History",
                    "source_type": "educational",
                    "author": "History Department",
                    "date": "2023-02-10",
                    "chunk_index": 0
                }
            )
        ]
        
        return mock_documents
    
    async def _get_fallback_information(self, context: TourContext, query: str) -> Dict[str, Any]:
        """Get fallback information when retrieval fails."""
        return {
            "message": "Unable to retrieve specific information at this time.",
            "suggestion": "Please try rephrasing your question or ask about general site information.",
            "general_info": {
                "site_id": context.site_id,
                "available_topics": ["history", "architecture", "daily_life", "significance"]
            }
        }
