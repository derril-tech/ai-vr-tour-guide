"""
Database connection and operations for workers.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import asyncpg
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    logging.warning("Database libraries not available")

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        
        if HAS_DATABASE:
            self.engine = create_async_engine(database_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
    
    async def create_document(self, document_data: Dict[str, Any]) -> str:
        """Create a new document record."""
        if not HAS_DATABASE:
            logger.warning("Database not available, skipping document creation")
            return document_data["id"]
        
        try:
            async with self.session_factory() as session:
                # Insert document
                query = """
                INSERT INTO content.documents (
                    id, tenant_id, site_id, title, content, content_type, 
                    source_url, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                now = datetime.utcnow()
                await session.execute(query, [
                    document_data["id"],
                    document_data["tenant_id"],
                    document_data["site_id"],
                    document_data["title"],
                    document_data["content"],
                    document_data["content_type"],
                    document_data.get("source_url"),
                    document_data.get("metadata", {}),
                    now,
                    now
                ])
                
                await session.commit()
                logger.info(f"Created document {document_data['id']}")
                return document_data["id"]
                
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise e
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document record."""
        if not HAS_DATABASE:
            logger.warning("Database not available, skipping document update")
            return True
        
        try:
            async with self.session_factory() as session:
                # Build update query dynamically
                set_clauses = []
                params = []
                param_idx = 1
                
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                
                # Add updated_at
                set_clauses.append(f"updated_at = ${param_idx}")
                params.append(datetime.utcnow())
                param_idx += 1
                
                # Add document_id for WHERE clause
                params.append(document_id)
                
                query = f"""
                UPDATE content.documents 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                """
                
                result = await session.execute(query, params)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Updated document {document_id}")
                    return True
                else:
                    logger.warning(f"Document {document_id} not found for update")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise e
    
    async def delete_document(self, document_id: str, tenant_id: str) -> bool:
        """Delete a document and its embeddings."""
        if not HAS_DATABASE:
            logger.warning("Database not available, skipping document deletion")
            return True
        
        try:
            async with self.session_factory() as session:
                # Delete embeddings first
                await session.execute(
                    "DELETE FROM content.document_embeddings WHERE document_id = $1",
                    [document_id]
                )
                
                # Delete document
                result = await session.execute(
                    "DELETE FROM content.documents WHERE id = $1 AND tenant_id = $2",
                    [document_id, tenant_id]
                )
                
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Deleted document {document_id}")
                    return True
                else:
                    logger.warning(f"Document {document_id} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise e
    
    async def get_document(self, document_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        if not HAS_DATABASE:
            logger.warning("Database not available")
            return None
        
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    """
                    SELECT id, tenant_id, site_id, title, content, content_type,
                           source_url, metadata, created_at, updated_at
                    FROM content.documents 
                    WHERE id = $1 AND tenant_id = $2
                    """,
                    [document_id, tenant_id]
                )
                
                row = result.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "tenant_id": row[1],
                        "site_id": row[2],
                        "title": row[3],
                        "content": row[4],
                        "content_type": row[5],
                        "source_url": row[6],
                        "metadata": row[7],
                        "created_at": row[8],
                        "updated_at": row[9]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise e
    
    async def create_embeddings(self, embeddings: List[Dict[str, Any]]) -> int:
        """Create document embedding records."""
        if not HAS_DATABASE:
            logger.warning("Database not available, skipping embeddings creation")
            return 0
        
        try:
            async with self.session_factory() as session:
                query = """
                INSERT INTO content.document_embeddings (
                    id, document_id, chunk_index, content, embedding, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                
                now = datetime.utcnow()
                count = 0
                
                for emb in embeddings:
                    await session.execute(query, [
                        emb["id"],
                        emb["document_id"],
                        emb["chunk_index"],
                        emb["content"],
                        emb["embedding"],
                        emb.get("metadata", {}),
                        now
                    ])
                    count += 1
                
                await session.commit()
                logger.info(f"Created {count} embeddings")
                return count
                
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise e
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()


# Global database instance
_database: Optional[Database] = None


async def get_database() -> Database:
    """Get database instance."""
    global _database
    
    if _database is None:
        from .config import get_settings
        settings = get_settings()
        _database = Database(settings.database_url)
    
    return _database
