"""
Optimized OBC query patterns demonstrating when to use exact equality vs LIKE.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_async_db
from app.models.ontario_chunk import OntarioChunk


async def demonstrate_query_optimization():
    """Demonstrate optimized query patterns."""
    
    async for db in get_async_db():
        try:
            print("=== Optimized OBC Query Patterns ===\n")
            
            # GOOD: Use exact equality for known values
            print("✅ GOOD: Exact equality for hierarchical fields")
            print("Query: Get all articles in Part 1, Section 2, Subsection 1")
            result = await db.execute(
                select(OntarioChunk).where(
                    and_(
                        OntarioChunk.chunk_type == "article",
                        OntarioChunk.part == "1",
                        OntarioChunk.section == "2", 
                        OntarioChunk.subsection == "1"
                    )
                ).limit(3)
            )
            chunks = result.scalars().all()
            for chunk in chunks:
                print(f"  - {chunk.reference}: {chunk.title}")
            print()
            
            # GOOD: Use exact equality for division when you know the exact value
            print("✅ GOOD: Exact equality for known division")
            print("Query: Get all parts in Division A (exact match)")
            result = await db.execute(
                select(OntarioChunk).where(
                    and_(
                        OntarioChunk.chunk_type == "part",
                        OntarioChunk.division == "Division A"
                    )
                )
            )
            parts = result.scalars().all()
            for part in parts:
                print(f"  - Part {part.part}: {part.title}")
            print()
            
            # ACCEPTABLE: Use LIKE only when you need pattern matching
            print("⚠️  ACCEPTABLE: LIKE for actual pattern matching")
            print("Query: Find articles with 'fire' in title (case-insensitive)")
            result = await db.execute(
                select(OntarioChunk).where(
                    and_(
                        OntarioChunk.chunk_type == "article",
                        OntarioChunk.title.ilike("%fire%")  # ilike for case-insensitive
                    )
                ).limit(3)
            )
            fire_articles = result.scalars().all()
            for article in fire_articles:
                print(f"  - {article.reference}: {article.title}")
            print()
            
            # BAD: Using LIKE when exact equality would work
            print("❌ BAD: Using LIKE for exact matches")
            print("Query: OntarioChunk.division.like('%Division A%') - inefficient!")
            print("Better: OntarioChunk.division == 'Division A'")
            print()
            
            # OPTIMIZED: Complex hierarchical query with exact matches
            print("✅ OPTIMIZED: Complex query with exact matches and indexing")
            print("Query: Get specific article with full hierarchy")
            result = await db.execute(
                select(OntarioChunk).where(
                    and_(
                        OntarioChunk.division == "Division A",
                        OntarioChunk.part == "1",
                        OntarioChunk.section == "1", 
                        OntarioChunk.subsection == "1",
                        OntarioChunk.reference == "1.1.1.1"
                    )
                )
            )
            specific_article = result.scalar_one_or_none()
            if specific_article:
                print(f"  Found: {specific_article.reference} - {specific_article.title}")
            print()
            
            # PERFORMANCE TIP: Use IN for multiple values
            print("✅ PERFORMANCE TIP: Use IN for multiple values")
            print("Query: Get articles from multiple sections")
            result = await db.execute(
                select(OntarioChunk).where(
                    and_(
                        OntarioChunk.chunk_type == "article",
                        OntarioChunk.part == "1",
                        OntarioChunk.section.in_(["1", "2", "3"])
                    )
                ).limit(5)
            )
            multi_section_articles = result.scalars().all()
            for article in multi_section_articles:
                print(f"  - {article.reference}: Section {article.section}")
            print()
            
            print("=== Query Optimization Guidelines ===")
            print("✅ DO:")
            print("  - Use == for exact matches (division, part, section, etc.)")
            print("  - Use indexed columns in WHERE clauses")
            print("  - Use IN() for multiple specific values")
            print("  - Use ilike() for case-insensitive pattern matching")
            print("  - Combine conditions with and_() for readability")
            print()
            print("❌ DON'T:")
            print("  - Use LIKE when == would work")
            print("  - Use LIKE with % on both sides unless necessary")
            print("  - Query without using indexed columns")
            print("  - Use OR conditions when IN() would work better")
            
        except Exception as e:
            print(f"Error during demonstration: {e}")
            raise
        finally:
            await db.close()
        break


async def show_query_performance_comparison():
    """Show performance difference between LIKE and exact equality."""
    
    async for db in get_async_db():
        try:
            print("\n=== Performance Comparison ===\n")
            
            import time
            
            # Test exact equality (FAST)
            start_time = time.time()
            result = await db.execute(
                select(func.count(OntarioChunk.id)).where(
                    OntarioChunk.division == "Division A"
                )
            )
            exact_count = result.scalar()
            exact_time = time.time() - start_time
            
            # Test LIKE pattern (SLOWER)
            start_time = time.time()
            result = await db.execute(
                select(func.count(OntarioChunk.id)).where(
                    OntarioChunk.division.like("%Division A%")
                )
            )
            like_count = result.scalar()
            like_time = time.time() - start_time
            
            print(f"Exact equality (==): {exact_count} results in {exact_time:.4f}s")
            print(f"LIKE pattern: {like_count} results in {like_time:.4f}s")
            print(f"Performance difference: {like_time/exact_time:.2f}x slower with LIKE")
            
        except Exception as e:
            print(f"Error during performance test: {e}")
        finally:
            await db.close()
        break


async def main():
    """Main function."""
    try:
        await demonstrate_query_optimization()
        await show_query_performance_comparison()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
