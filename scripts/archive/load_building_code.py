#!/usr/bin/env python3
"""
Ontario Building Code Loader Script
Loads and processes Ontario Building Code markdown files into the database.
"""
import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_db, get_async_engine
from app.models.guideline_chunk import GuidelineChunk as DBGuidelineChunk
from app.services.guideline_processor import GuidelineProcessor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def clear_existing_chunks(session: AsyncSession) -> int:
    """Clear existing guideline chunks from the database."""
    try:
        # Count existing chunks
        count_result = await session.execute(select(DBGuidelineChunk))
        existing_count = len(count_result.scalars().all())

        if existing_count > 0:
            logger.info(f"Found {existing_count} existing chunks. Clearing...")
            # Delete all existing chunks
            await session.execute(delete(DBGuidelineChunk))
            await session.commit()
            logger.info(f"Cleared {existing_count} existing chunks")
            return existing_count
        else:
            logger.info("No existing chunks found")
            return 0
    except Exception as e:
        logger.error(f"Error clearing existing chunks: {str(e)}")
        await session.rollback()
        raise


async def save_chunks_to_database(chunks, session: AsyncSession) -> int:
    """Save processed chunks to the database."""
    saved_count = 0
    batch_size = 50

    try:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            for chunk in batch:
                db_chunk = DBGuidelineChunk(
                    section_reference=chunk.section_reference,
                    section_title=chunk.section_title,
                    section_level=chunk.section_level,
                    chunk_text=chunk.chunk_text
                )
                session.add(db_chunk)

            await session.commit()
            saved_count += len(batch)
            logger.info(f"Saved batch {i//batch_size + 1}: {saved_count}/{len(chunks)} chunks")

        logger.info(f"Successfully saved {saved_count} chunks to database")
        return saved_count

    except Exception as e:
        logger.error(f"Error saving chunks to database: {str(e)}")
        await session.rollback()
        raise


async def load_building_code(file_path: str, clear_existing: bool = True) -> None:
    """Main function to load building code from markdown file."""
    logger.info(f"Starting Ontario Building Code loading process")
    logger.info(f"File: {file_path}")
    logger.info(f"Clear existing: {clear_existing}")

    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Initialize processor
    processor = GuidelineProcessor()

    try:
        # Process the markdown file
        logger.info("Processing markdown file...")
        chunks = processor.process_markdown_file(file_path)

        if not chunks:
            logger.error("No chunks were processed from the file")
            sys.exit(1)

        # Get processing statistics
        stats = processor.get_processing_stats(chunks)
        logger.info("Processing Statistics:")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Sections by level: {stats['sections_by_level']}")
        logger.info(f"  Average content length: {stats['average_content_length']} characters")
        logger.info(f"  Total content length: {stats['total_content_length']} characters")

        # Get database session
        engine = get_async_engine()
        async with AsyncSession(engine) as session:
            # Clear existing chunks if requested
            if clear_existing:
                cleared_count = await clear_existing_chunks(session)

            # Save new chunks
            saved_count = await save_chunks_to_database(chunks, session)

            logger.info("=" * 50)
            logger.info("LOADING COMPLETE!")
            logger.info(f"File processed: {file_path}")
            if clear_existing:
                logger.info(f"Existing chunks cleared: {cleared_count}")
            logger.info(f"New chunks saved: {saved_count}")
            logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Load Ontario Building Code markdown file into database"
    )
    parser.add_argument(
        "file_path",
        help="Path to the Ontario Building Code markdown file"
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing chunks in database (default: clear existing)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('app.services.guideline_processor').setLevel(logging.DEBUG)

    # Run the async function
    asyncio.run(load_building_code(
        file_path=args.file_path,
        clear_existing=not args.keep_existing
    ))


if __name__ == "__main__":
    main()
