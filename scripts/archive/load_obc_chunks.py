"""
Enhanced OBC Data Ingestion Script
Parses OBC markdown content and populates the ontario_chunks table with hierarchical chunks.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, text
from app.database import get_db
from app.models.ontario_chunk import OntarioChunk
from app.services.obc_parser import EnhancedOBCParser


async def clear_existing_data(db: AsyncSession):
    """Clear existing ontario_chunks data."""
    print("Clearing existing ontario_chunks data...")

    # Delete all existing records using SQLAlchemy delete
    result = await db.execute(delete(OntarioChunk))
    await db.commit()

    print(f"Cleared existing data.")


async def ingest_obc_data(file_path: str):
    """
    Ingest OBC data from markdown file into the database.

    Args:
        file_path: Path to the OBC markdown file
    """
    print(f"Starting OBC data ingestion from {file_path}")

    # Parse the OBC file
    parser = EnhancedOBCParser()
    chunks = parser.parse_file(file_path)

    print(f"Parsed {len(chunks)} chunks from OBC file")

    # Get database session
    async for db in get_db():
        try:
            # Clear existing data
            await clear_existing_data(db)

            # Insert new data
            print("Inserting new chunks...")

            chunk_counts = {
                'division': 0,
                'part': 0,
                'section': 0,
                'subsection': 0,
                'article': 0,
                'index': 0
            }

            for i, chunk in enumerate(chunks):
                ontario_chunk = OntarioChunk(
                    reference=chunk.reference,
                    division=chunk.division,
                    part=chunk.part,
                    section=chunk.section,
                    subsection=chunk.subsection,
                    article=chunk.article,
                    chunk_type=chunk.chunk_type,
                    title=chunk.title,
                    content=chunk.content
                )

                db.add(ontario_chunk)
                chunk_counts[chunk.chunk_type] += 1

                # Commit in batches of 50
                if (i + 1) % 50 == 0:
                    await db.commit()
                    print(f"Inserted {i + 1} chunks...")

            # Final commit
            await db.commit()

            print(f"Successfully inserted {len(chunks)} chunks into ontario_chunks table")
            print("Chunk breakdown:")
            for chunk_type, count in chunk_counts.items():
                if count > 0:
                    print(f"  {chunk_type}: {count}")

        except Exception as e:
            await db.rollback()
            print(f"Error during ingestion: {e}")
            raise
        finally:
            await db.close()
        break  # Exit the async generator loop


async def main():
    """Main function."""
    # Default OBC file path
    obc_file_path = "assets/2024 OBC.Volume 1 refined.md"

    # Check if file exists
    if not os.path.exists(obc_file_path):
        print(f"Error: OBC file not found at {obc_file_path}")
        sys.exit(1)

    try:
        await ingest_obc_data(obc_file_path)
        print("OBC data ingestion completed successfully!")
    except Exception as e:
        print(f"Error during ingestion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
