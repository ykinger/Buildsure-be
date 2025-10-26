"""
Script to clean up division values in the ontario_chunks table for better querying.
Converts long descriptive division names to simple "Division A", "Division B", etc.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, distinct
from app.database import get_db
from app.models.ontario_chunk import OntarioChunk


async def clean_division_values():
    """Clean up division values for better querying."""

    async for db in get_db():
        try:
            print("=== Cleaning Division Values ===\n")

            # Show current values
            print("Current division values:")
            result = await db.execute(
                select(distinct(OntarioChunk.division)).order_by(OntarioChunk.division)
            )
            current_divisions = result.scalars().all()
            for div in current_divisions:
                print(f'  "{div}"')
            print()

            # Define the mapping from current values to clean values
            division_mapping = {
                "Division A Compliance, Objectives and Functional Statements": "Division A",
                "Division B Acceptable Solutions": "Division B",
                "Division C Administrative Provisions": "Division C",
                "Index(1)": "Index"
            }

            # Update each division
            total_updated = 0
            for old_value, new_value in division_mapping.items():
                print(f"Updating '{old_value}' -> '{new_value}'")

                # Count how many will be updated
                count_result = await db.execute(
                    select(func.count(OntarioChunk.id)).where(
                        OntarioChunk.division == old_value
                    )
                )
                count = count_result.scalar()

                if count > 0:
                    # Perform the update
                    result = await db.execute(
                        update(OntarioChunk)
                        .where(OntarioChunk.division == old_value)
                        .values(division=new_value)
                    )

                    print(f"  Updated {count} chunks")
                    total_updated += count
                else:
                    print(f"  No chunks found with value '{old_value}'")

            # Commit the changes
            await db.commit()
            print(f"\nTotal chunks updated: {total_updated}")

            # Show updated values
            print("\nUpdated division values:")
            result = await db.execute(
                select(distinct(OntarioChunk.division)).order_by(OntarioChunk.division)
            )
            updated_divisions = result.scalars().all()
            for div in updated_divisions:
                print(f'  "{div}"')

            # Show counts after update
            print("\nChunk counts after update:")
            result = await db.execute(
                select(OntarioChunk.division, func.count(OntarioChunk.id).label('count'))
                .group_by(OntarioChunk.division)
                .order_by(OntarioChunk.division)
            )
            counts = result.all()
            for row in counts:
                print(f"  {row.division}: {row.count} chunks")

            print("\n=== Division values cleaned successfully! ===")
            print("\nNow you can use exact equality queries like:")
            print("  WHERE division = 'Division A'")
            print("  WHERE division = 'Division B'")
            print("  WHERE division = 'Division C'")

        except Exception as e:
            print(f"Error during cleanup: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()
        break


async def test_cleaned_queries():
    """Test queries with the cleaned division values."""

    async for db in get_db():
        try:
            print("\n=== Testing Cleaned Queries ===\n")

            # Test exact equality query
            print("✅ Testing exact equality: division = 'Division A'")
            result = await db.execute(
                select(func.count(OntarioChunk.id)).where(
                    OntarioChunk.division == "Division A"
                )
            )
            count_a = result.scalar()
            print(f"  Found {count_a} chunks in Division A")

            print("✅ Testing exact equality: division = 'Division B'")
            result = await db.execute(
                select(func.count(OntarioChunk.id)).where(
                    OntarioChunk.division == "Division B"
                )
            )
            count_b = result.scalar()
            print(f"  Found {count_b} chunks in Division B")

            # Test getting parts in Division A
            print("\n✅ Testing hierarchical query: Get all parts in Division A")
            result = await db.execute(
                select(OntarioChunk).where(
                    OntarioChunk.division == "Division A"
                ).where(
                    OntarioChunk.chunk_type == "part"
                ).order_by(OntarioChunk.part)
            )
            parts = result.scalars().all()
            for part in parts:
                print(f"  - Part {part.part}: {part.title}")

        except Exception as e:
            print(f"Error during testing: {e}")
        finally:
            await db.close()
        break


async def main():
    """Main function."""
    try:
        await clean_division_values()
        await test_cleaned_queries()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
