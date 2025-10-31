"""
Knowledge Base query service with best practices for hierarchical data retrieval.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseQueryService:
    """Service for optimized knowledge base queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_content_by_reference(
        self,
        reference: str,
        source: Optional[str] = None
    ) -> Optional[KnowledgeBase]:
        """
        Get specific knowledge base content by its reference number.
        Uses exact equality for optimal performance.
        """
        conditions = [
            KnowledgeBase.reference == reference
        ]

        if source:
            conditions.append(KnowledgeBase.source == source)

        result = await self.db.execute(
            select(KnowledgeBase).where(and_(*conditions))
        )
        return result.scalar_one_or_none()

    async def search_content(
        self,
        search_term: str,
        source: Optional[str] = None,
        case_sensitive: bool = False,
        limit: int = 50
    ) -> List[KnowledgeBase]:
        """
        Search for content in references and content.
        Uses LIKE/ILIKE only when actually needed for pattern matching.
        """
        conditions = []

        # Use exact equality for structured fields
        if source:
            conditions.append(KnowledgeBase.source == source)

        # Use LIKE/ILIKE only for actual text search
        if case_sensitive:
            search_condition = or_(
                KnowledgeBase.reference.like(f"%{search_term}%"),
                KnowledgeBase.content.like(f"%{search_term}%")
            )
        else:
            search_condition = or_(
                KnowledgeBase.reference.ilike(f"%{search_term}%"),
                KnowledgeBase.content.ilike(f"%{search_term}%")
            )

        conditions.append(search_condition)

        result = await self.db.execute(
            select(KnowledgeBase)
            .where(and_(*conditions))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_source_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the knowledge base structure by source.
        Uses exact equality and efficient aggregation.
        """
        # Count by source
        result = await self.db.execute(
            select(
                KnowledgeBase.source,
                func.count(KnowledgeBase.id).label('count')
            )
            .group_by(KnowledgeBase.source)
            .order_by(KnowledgeBase.source)
        )

        summary = {}
        for row in result:
            summary[row.source] = row.count

        return summary

    async def get_multiple_by_reference(
        self,
        references: List[str],
        source: Optional[str] = None
    ) -> List[KnowledgeBase]:
        """
        Get multiple knowledge base items by their references efficiently.
        Uses IN() for optimal performance with multiple values.
        """
        conditions = [
            KnowledgeBase.reference.in_(references)
        ]

        if source:
            conditions.append(KnowledgeBase.source == source)

        result = await self.db.execute(
            select(KnowledgeBase)
            .where(and_(*conditions))
            .order_by(KnowledgeBase.reference)
        )
        return result.scalars().all()

    async def find_by_reference(
        self,
        references: list[str]|str,
        source: str = "OBC"
    ) -> str:
        """
        Get all knowledge base items that contain the reference pattern.
        Uses LIKE for pattern matching and returns concatenated content.
        """
        if isinstance(references, str):
            references = [references]
        content = ""
        for reference in references:
            result = await self.db.execute(
                select(KnowledgeBase)
                .where(KnowledgeBase.source == source)
                .where(KnowledgeBase.reference.like(f"{reference}%"))
                .order_by(KnowledgeBase.reference)
            )
            for item in result.scalars().all():
                content += item.content
        return content


# Example usage functions
async def example_optimized_queries():
    """Examples of how to use the optimized query service."""
    from app.database import get_db

    async for db in get_db():
        service = KnowledgeBaseQueryService(db)

        # ✅ GOOD: Get specific content by reference
        content = await service.get_content_by_reference(
            reference="1.2.1.1",
            source="OBC"
        )

        # ✅ GOOD: Search for content (uses LIKE appropriately)
        fire_content = await service.search_content(
            search_term="fire",
            source="OBC"
        )

        # ✅ GOOD: Get multiple items efficiently
        multiple_items = await service.get_multiple_by_reference(
            references=["1.1.1.1", "1.2.1.1", "1.3.1.1"],
            source="OBC"
        )

        await db.close()
        break
