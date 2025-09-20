"""
Test script to demonstrate flexible OBC chunk retrieval capabilities.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_async_db
from app.models.ontario_chunk import OntarioChunk


async def test_retrieval_capabilities():
    """Test various retrieval scenarios."""
    
    async for db in get_async_db():
        try:
            print("=== OBC Chunk Retrieval Test ===\n")
            
            # Test 1: Get all chunks in a specific subsection
            print("1. All chunks in subsection 1.1.1:")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.subsection == "1"
                ).where(
                    OntarioChunk.section == "1"
                ).where(
                    OntarioChunk.part == "1"
                ).limit(5)
            )
            chunks = result.scalars().all()
            for chunk in chunks:
                print(f"  - {chunk.reference} ({chunk.chunk_type}): {chunk.title}")
            print()
            
            # Test 2: Get all articles in a specific section
            print("2. All articles in section 1.2:")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.chunk_type == "article"
                ).where(
                    OntarioChunk.section == "2"
                ).where(
                    OntarioChunk.part == "1"
                ).limit(5)
            )
            articles = result.scalars().all()
            for article in articles:
                print(f"  - {article.reference}: {article.title}")
            print()
            
            # Test 3: Get all parts in Division A
            print("3. All parts in Division A:")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.chunk_type == "part"
                ).where(
                    OntarioChunk.division.like("%Division A%")
                )
            )
            parts = result.scalars().all()
            for part in parts:
                print(f"  - Part {part.part}: {part.title}")
            print()
            
            # Test 4: Get specific article content
            print("4. Content of article 1.1.1.1:")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.reference == "1.1.1.1"
                ).where(
                    OntarioChunk.division.like("%Division A%")
                ).limit(1)
            )
            article = result.scalar_one_or_none()
            if article:
                print(f"  Title: {article.title}")
                print(f"  Content preview: {article.content[:200]}...")
            print()
            
            # Test 5: Count chunks by type and division
            print("5. Chunk counts by division:")
            result = await db.execute(
                select(OntarioChunk.division, OntarioChunk.chunk_type, 
                       func.count(OntarioChunk.id).label('count'))
                .group_by(OntarioChunk.division, OntarioChunk.chunk_type)
                .order_by(OntarioChunk.division, OntarioChunk.chunk_type)
            )
            counts = result.all()
            current_division = None
            for row in counts:
                if row.division != current_division:
                    current_division = row.division
                    print(f"  {current_division}:")
                print(f"    {row.chunk_type}: {row.count}")
            print()
            
            # Test 6: Search for specific content
            print("6. Articles containing 'fire' in title:")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.chunk_type == "article"
                ).where(
                    OntarioChunk.title.like("%fire%")
                ).limit(5)
            )
            fire_articles = result.scalars().all()
            for article in fire_articles:
                print(f"  - {article.reference}: {article.title}")
            print()
            
            print("=== Test completed successfully! ===")
            
        except Exception as e:
            print(f"Error during testing: {e}")
            raise
        finally:
            await db.close()
        break


async def main():
    """Main function."""
    try:
        await test_retrieval_capabilities()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
