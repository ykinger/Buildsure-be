"""
Knowledge Service
Provides functions for retrieving knowledge base content.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models.knowledge_base import KnowledgeBase


class KnowledgeService:
    """Service for retrieving knowledge base content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_knowledge_context(self, reference: str, source: str = "OBC") -> str:
        """
        Retrieve knowledge base content for a given reference.

        Args:
            reference: Knowledge base reference (e.g., "3.2.1.1")
            source: Source filter (default: "OBC")

        Returns:
            Concatenated content of all matching items
        """
        # Build query conditions
        conditions = [
            KnowledgeBase.source == source,
            KnowledgeBase.reference.like(f"{reference}%")
        ]

        # Execute query
        query = select(KnowledgeBase).where(and_(*conditions)).order_by(KnowledgeBase.reference)
        result = await self.db.execute(query)
        items = result.scalars().all()

        if not items:
            return f"No content found for reference: {reference}"

        # Concatenate all matching content
        content_parts = []
        for item in items:
            content_parts.append(f"## {item.reference} - {item.content}")

        return "\n\n".join(content_parts)

    async def get_knowledge_count(self, source: Optional[str] = None) -> int:
        """
        Get the total number of knowledge base items in the database.

        Args:
            source: Optional source filter

        Returns:
            Total count of items
        """
        query = select(KnowledgeBase)

        if source:
            query = query.where(KnowledgeBase.source == source)

        result = await self.db.execute(query)
        items = result.scalars().all()
        return len(items)

    async def get_knowledge_references(self, source: Optional[str] = None) -> List[str]:
        """
        Get all available knowledge base references, optionally filtered by source.

        Args:
            source: Optional source to filter by

        Returns:
            List of reference strings
        """
        query = select(KnowledgeBase.reference)

        if source:
            query = query.where(KnowledgeBase.source == source)

        query = query.order_by(KnowledgeBase.reference)

        result = await self.db.execute(query)
        references = result.scalars().all()

        return list(references)


# Convenience function for getting knowledge context
async def get_knowledge_context(db: AsyncSession, reference: str, source: str = "OBC") -> str:
    """
    Convenience function to get knowledge base context.

    Args:
        db: Database session
        reference: Knowledge base reference
        source: Source filter (default: "OBC")

    Returns:
        Knowledge base content for the reference
    """
    service = KnowledgeService(db)
    return await service.get_knowledge_context(reference, source)
