"""
Optimized OBC query service with best practices for hierarchical data retrieval.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.ontario_chunk import OntarioChunk


class OBCQueryService:
    """Service for optimized OBC chunk queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chunks_by_hierarchy(
        self,
        division: Optional[str] = None,
        part: Optional[str] = None,
        section: Optional[str] = None,
        subsection: Optional[str] = None,
        article: Optional[str] = None,
        chunk_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[OntarioChunk]:
        """
        Get chunks by exact hierarchical match.
        Uses exact equality (==) for optimal performance.
        """
        conditions = []

        # Use exact equality for all hierarchical fields
        if division:
            conditions.append(OntarioChunk.division == division)
        if part:
            conditions.append(OntarioChunk.part == part)
        if section:
            conditions.append(OntarioChunk.section == section)
        if subsection:
            conditions.append(OntarioChunk.subsection == subsection)
        if article:
            conditions.append(OntarioChunk.article == article)
        if chunk_type:
            conditions.append(OntarioChunk.chunk_type == chunk_type)

        query = select(OntarioChunk)
        if conditions:
            query = query.where(and_(*conditions))

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_article_by_reference(
        self,
        reference: str,
        division: Optional[str] = None
    ) -> Optional[OntarioChunk]:
        """
        Get a specific article by its reference number.
        Uses exact equality for optimal performance.
        """
        conditions = [
            OntarioChunk.reference == reference,
            OntarioChunk.chunk_type == "article"
        ]

        if division:
            conditions.append(OntarioChunk.division == division)

        result = await self.db.execute(
            select(OntarioChunk).where(and_(*conditions))
        )
        return result.scalar_one_or_none()

    async def get_all_articles_in_subsection(
        self,
        division: str,
        part: str,
        section: str,
        subsection: str
    ) -> List[OntarioChunk]:
        """
        Get all articles within a specific subsection.
        Uses exact equality for optimal performance.
        """
        result = await self.db.execute(
            select(OntarioChunk).where(
                and_(
                    OntarioChunk.division == division,
                    OntarioChunk.part == part,
                    OntarioChunk.section == section,
                    OntarioChunk.subsection == subsection,
                    OntarioChunk.chunk_type == "article"
                )
            ).order_by(OntarioChunk.reference)
        )
        return result.scalars().all()

    async def get_all_subsections_in_section(
        self,
        division: str,
        part: str,
        section: str
    ) -> List[OntarioChunk]:
        """
        Get all subsections within a specific section.
        Uses exact equality for optimal performance.
        """
        result = await self.db.execute(
            select(OntarioChunk).where(
                and_(
                    OntarioChunk.division == division,
                    OntarioChunk.part == part,
                    OntarioChunk.section == section,
                    OntarioChunk.chunk_type == "subsection"
                )
            ).order_by(OntarioChunk.subsection)
        )
        return result.scalars().all()

    async def search_content(
        self,
        search_term: str,
        chunk_type: Optional[str] = None,
        division: Optional[str] = None,
        case_sensitive: bool = False,
        limit: int = 50
    ) -> List[OntarioChunk]:
        """
        Search for content in titles and content.
        Uses LIKE/ILIKE only when actually needed for pattern matching.
        """
        conditions = []

        # Use exact equality for structured fields
        if chunk_type:
            conditions.append(OntarioChunk.chunk_type == chunk_type)
        if division:
            conditions.append(OntarioChunk.division == division)

        # Use LIKE/ILIKE only for actual text search
        if case_sensitive:
            search_condition = or_(
                OntarioChunk.title.like(f"%{search_term}%"),
                OntarioChunk.content.like(f"%{search_term}%")
            )
        else:
            search_condition = or_(
                OntarioChunk.title.ilike(f"%{search_term}%"),
                OntarioChunk.content.ilike(f"%{search_term}%")
            )

        conditions.append(search_condition)

        result = await self.db.execute(
            select(OntarioChunk)
            .where(and_(*conditions))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_hierarchy_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the hierarchical structure.
        Uses exact equality and efficient aggregation.
        """
        # Count by division and chunk type
        result = await self.db.execute(
            select(
                OntarioChunk.division,
                OntarioChunk.chunk_type,
                func.count(OntarioChunk.id).label('count')
            )
            .group_by(OntarioChunk.division, OntarioChunk.chunk_type)
            .order_by(OntarioChunk.division, OntarioChunk.chunk_type)
        )

        summary = {}
        for row in result:
            if row.division not in summary:
                summary[row.division] = {}
            summary[row.division][row.chunk_type] = row.count

        return summary

    async def get_parts_in_division(self, division: str) -> List[OntarioChunk]:
        """
        Get all parts in a specific division.
        Uses exact equality for optimal performance.
        """
        result = await self.db.execute(
            select(OntarioChunk).where(
                and_(
                    OntarioChunk.division == division,
                    OntarioChunk.chunk_type == "part"
                )
            ).order_by(OntarioChunk.part)
        )
        return result.scalars().all()

    async def get_sections_in_part(
        self,
        division: str,
        part: str
    ) -> List[OntarioChunk]:
        """
        Get all sections in a specific part.
        Uses exact equality for optimal performance.
        """
        result = await self.db.execute(
            select(OntarioChunk).where(
                and_(
                    OntarioChunk.division == division,
                    OntarioChunk.part == part,
                    OntarioChunk.chunk_type == "section"
                )
            ).order_by(OntarioChunk.section)
        )
        return result.scalars().all()

    async def get_multiple_articles(
        self,
        references: List[str],
        division: Optional[str] = None
    ) -> List[OntarioChunk]:
        """
        Get multiple articles by their references efficiently.
        Uses IN() for optimal performance with multiple values.
        """
        conditions = [
            OntarioChunk.reference.in_(references),
            OntarioChunk.chunk_type == "article"
        ]

        if division:
            conditions.append(OntarioChunk.division == division)

        result = await self.db.execute(
            select(OntarioChunk)
            .where(and_(*conditions))
            .order_by(OntarioChunk.reference)
        )
        return result.scalars().all()

    async def find_by_reference(
        self,
        references: list[str]|str,
        division: str = "Division B"
    ) -> List[OntarioChunk]:
        """
        Get all chunks in a specific division that contain the reference pattern.
        Uses LIKE for pattern matching and returns results ordered by reference.
        """
        if isinstance(references, str):
            references = [references]
        content = ""
        # print("getting", references)
        for reference in references:
            result = await self.db.execute(
                select(OntarioChunk)
                .where(OntarioChunk.division == division)
                #TODO: ref=ref OR ref like 'ref.%'
                .where(OntarioChunk.reference.like(f"{reference}%"))
                .order_by(OntarioChunk.reference)
            )
            for chunk in result.scalars().all():
                content += chunk.content
        return content


# Example usage functions
async def example_optimized_queries():
    """Examples of how to use the optimized query service."""
    from app.database import get_db

    async for db in get_db():
        service = OBCQueryService(db)

        # ✅ GOOD: Get all articles in a specific subsection
        articles = await service.get_all_articles_in_subsection(
            division="Division A",
            part="1",
            section="2",
            subsection="1"
        )

        # ✅ GOOD: Get a specific article by reference
        article = await service.get_article_by_reference(
            reference="1.2.1.1",
            division="Division A"
        )

        # ✅ GOOD: Search for content (uses LIKE appropriately)
        fire_articles = await service.search_content(
            search_term="fire",
            chunk_type="article",
            division="Division A"
        )

        # ✅ GOOD: Get multiple articles efficiently
        multiple_articles = await service.get_multiple_articles(
            references=["1.1.1.1", "1.2.1.1", "1.3.1.1"],
            division="Division A"
        )

        await db.close()
        break
