"""
Knowledge Service
Provides functions for retrieving Ontario Building Code content.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models.ontario_chunk import OntarioChunk


class KnowledgeService:
    """Service for retrieving OBC knowledge."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_obc_context(self, reference: str) -> str:
        """
        Retrieve OBC content for a given reference.
        
        Supports hierarchical retrieval:
        - "3" -> All articles in part 3
        - "3.2" -> All articles in section 3.2
        - "3.2.1" -> All articles in subsection 3.2.1
        - "3.2.1.1" -> Specific article 3.2.1.1
        
        Args:
            reference: OBC reference (e.g., "3", "3.2", "3.2.1", "3.2.1.1")
            
        Returns:
            Concatenated content of all matching articles
        """
        # Parse the reference to determine the level
        parts = reference.split('.')
        
        # Build query conditions based on reference level
        conditions = []
        
        if len(parts) >= 1 and parts[0]:
            conditions.append(OntarioChunk.part == parts[0])
        
        if len(parts) >= 2 and parts[1]:
            conditions.append(OntarioChunk.section == parts[1])
        
        if len(parts) >= 3 and parts[2]:
            conditions.append(OntarioChunk.subsection == parts[2])
        
        if len(parts) >= 4 and parts[3]:
            conditions.append(OntarioChunk.article == parts[3])
        
        # If no valid conditions, return empty
        if not conditions:
            return ""
        
        # Execute query
        query = select(OntarioChunk).where(and_(*conditions)).order_by(OntarioChunk.reference)
        result = await self.db.execute(query)
        chunks = result.scalars().all()
        
        if not chunks:
            return f"No content found for reference: {reference}"
        
        # Concatenate all matching content
        content_parts = []
        for chunk in chunks:
            content_parts.append(f"## {chunk.reference} - {chunk.content}")
        
        return "\n\n".join(content_parts)
    
    async def get_obc_article_count(self) -> int:
        """
        Get the total number of OBC articles in the database.
        
        Returns:
            Total count of articles
        """
        query = select(OntarioChunk)
        result = await self.db.execute(query)
        chunks = result.scalars().all()
        return len(chunks)
    
    async def get_obc_references(self, part: Optional[str] = None) -> List[str]:
        """
        Get all available OBC references, optionally filtered by part.
        
        Args:
            part: Optional part number to filter by (e.g., "3")
            
        Returns:
            List of reference strings
        """
        query = select(OntarioChunk.reference)
        
        if part:
            query = query.where(OntarioChunk.part == part)
        
        query = query.order_by(OntarioChunk.reference)
        
        result = await self.db.execute(query)
        references = result.scalars().all()
        
        return list(references)


# Convenience function for getting OBC context
async def get_obc_context(db: AsyncSession, reference: str) -> str:
    """
    Convenience function to get OBC context.
    
    Args:
        db: Database session
        reference: OBC reference
        
    Returns:
        OBC content for the reference
    """
    service = KnowledgeService(db)
    return await service.get_obc_context(reference)
