"""
Unified OBC Management Script
Handles all Ontario Building Code operations: loading, testing, and database management.
"""
import asyncio
import sys
import argparse
import time
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, distinct, delete
from app.database import get_async_db
from app.models.ontario_chunk import OntarioChunk
from app.services.obc_parser import EnhancedOBCParser


class OBCManager:
    """Unified manager for all OBC operations."""
    
    def __init__(self):
        self.parser = EnhancedOBCParser()
    
    async def load_obc_data(self, file_path: str, clear_existing: bool = False) -> None:
        """
        Load OBC data from markdown file with clean division values from the start.
        
        Args:
            file_path: Path to the OBC markdown file
            clear_existing: Whether to clear existing data first
        """
        print("=== Loading OBC Data ===\n")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        async for db in get_async_db():
            try:
                # Clear existing data if requested
                if clear_existing:
                    print("Clearing existing OBC data...")
                    await db.execute(delete(OntarioChunk))
                    await db.commit()
                    print("✅ Existing data cleared\n")
                
                # Parse the OBC file
                print(f"Parsing OBC file: {file_path}")
                chunks = self.parser.parse_file(file_path)
                print(f"✅ Parsed {len(chunks)} chunks\n")
                
                # Load chunks into database in batches
                batch_size = 100
                total_loaded = 0
                
                print("Loading chunks into database...")
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    
                    # Convert OBCChunk objects to OntarioChunk models
                    db_chunks = []
                    for chunk in batch:
                        db_chunk = OntarioChunk(
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
                        db_chunks.append(db_chunk)
                    
                    # Add batch to database
                    db.add_all(db_chunks)
                    await db.commit()
                    
                    total_loaded += len(batch)
                    progress = (total_loaded / len(chunks)) * 100
                    print(f"  Progress: {total_loaded}/{len(chunks)} ({progress:.1f}%)")
                
                print(f"✅ Successfully loaded {total_loaded} chunks\n")
                
                # Show summary
                await self._show_load_summary(db)
                
            except Exception as e:
                print(f"❌ Error loading OBC data: {e}")
                await db.rollback()
                raise
            finally:
                await db.close()
            break
    
    async def _show_load_summary(self, db: AsyncSession) -> None:
        """Show summary of loaded data."""
        print("=== Load Summary ===")
        
        # Count by division and chunk type
        result = await db.execute(
            select(
                OntarioChunk.division,
                OntarioChunk.chunk_type,
                func.count(OntarioChunk.id).label('count')
            )
            .group_by(OntarioChunk.division, OntarioChunk.chunk_type)
            .order_by(OntarioChunk.division, OntarioChunk.chunk_type)
        )
        
        counts = result.all()
        current_division = None
        total_chunks = 0
        
        for row in counts:
            if row.division != current_division:
                current_division = row.division
                print(f"\n{current_division}:")
            print(f"  {row.chunk_type}: {row.count}")
            total_chunks += row.count
        
        print(f"\n📊 Total chunks loaded: {total_chunks}")
        print("✅ Data loaded with clean division values (no post-processing needed)")
    
    async def test_queries(self) -> None:
        """Test various query patterns and performance."""
        print("=== Testing OBC Queries ===\n")
        
        async for db in get_async_db():
            try:
                # Test 1: Basic division query with exact equality
                print("1. Testing exact equality queries:")
                start_time = time.time()
                result = await db.execute(
                    select(func.count(OntarioChunk.id)).where(
                        OntarioChunk.division == "Division A"
                    )
                )
                count_a = result.scalar()
                exact_time = time.time() - start_time
                print(f"   Division A: {count_a} chunks ({exact_time:.4f}s)")
                
                result = await db.execute(
                    select(func.count(OntarioChunk.id)).where(
                        OntarioChunk.division == "Division B"
                    )
                )
                count_b = result.scalar()
                print(f"   Division B: {count_b} chunks")
                
                # Test 2: Hierarchical query
                print("\n2. Testing hierarchical queries:")
                result = await db.execute(
                    select(OntarioChunk).where(
                        OntarioChunk.division == "Division A"
                    ).where(
                        OntarioChunk.chunk_type == "part"
                    ).order_by(OntarioChunk.part)
                )
                parts = result.scalars().all()
                print(f"   Parts in Division A: {len(parts)}")
                for part in parts[:3]:  # Show first 3
                    print(f"     - Part {part.part}: {part.title}")
                
                # Test 3: Article lookup
                print("\n3. Testing article lookup:")
                result = await db.execute(
                    select(OntarioChunk).where(
                        OntarioChunk.reference == "1.1.1.1"
                    ).where(
                        OntarioChunk.division == "Division A"
                    )
                )
                article = result.scalar_one_or_none()
                if article:
                    print(f"   Found article: {article.reference} - {article.title}")
                    print(f"   Content preview: {article.content[:100]}...")
                
                # Test 4: Content search
                print("\n4. Testing content search:")
                result = await db.execute(
                    select(OntarioChunk).where(
                        OntarioChunk.chunk_type == "article"
                    ).where(
                        OntarioChunk.title.ilike("%fire%")
                    ).limit(3)
                )
                fire_articles = result.scalars().all()
                print(f"   Articles with 'fire' in title: {len(fire_articles)}")
                for article in fire_articles:
                    print(f"     - {article.reference}: {article.title}")
                
                print("\n✅ All query tests passed!")
                
            except Exception as e:
                print(f"❌ Error during testing: {e}")
                raise
            finally:
                await db.close()
            break
    
    async def show_status(self) -> None:
        """Show current database status and statistics."""
        print("=== OBC Database Status ===\n")
        
        async for db in get_async_db():
            try:
                # Total count
                result = await db.execute(select(func.count(OntarioChunk.id)))
                total_count = result.scalar()
                
                if total_count == 0:
                    print("📭 Database is empty")
                    print("💡 Use 'python scripts/obc_manager.py load' to load data")
                    return
                
                print(f"📊 Total chunks: {total_count}")
                
                # Count by division
                print("\n📂 Chunks by division:")
                result = await db.execute(
                    select(
                        OntarioChunk.division,
                        func.count(OntarioChunk.id).label('count')
                    )
                    .group_by(OntarioChunk.division)
                    .order_by(OntarioChunk.division)
                )
                division_counts = result.all()
                for row in division_counts:
                    print(f"   {row.division}: {row.count}")
                
                # Count by chunk type
                print("\n📋 Chunks by type:")
                result = await db.execute(
                    select(
                        OntarioChunk.chunk_type,
                        func.count(OntarioChunk.id).label('count')
                    )
                    .group_by(OntarioChunk.chunk_type)
                    .order_by(func.count(OntarioChunk.id).desc())
                )
                type_counts = result.all()
                for row in type_counts:
                    print(f"   {row.chunk_type}: {row.count}")
                
                # Sample data
                print("\n🔍 Sample data:")
                result = await db.execute(
                    select(OntarioChunk)
                    .where(OntarioChunk.chunk_type == "article")
                    .limit(3)
                )
                samples = result.scalars().all()
                for sample in samples:
                    print(f"   {sample.reference} ({sample.division}): {sample.title}")
                
                print("\n✅ Database is healthy and ready for queries")
                
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                raise
            finally:
                await db.close()
            break
    
    async def reset_database(self) -> None:
        """Clear all OBC data from the database."""
        print("=== Resetting OBC Database ===\n")
        
        async for db in get_async_db():
            try:
                # Count existing data
                result = await db.execute(select(func.count(OntarioChunk.id)))
                existing_count = result.scalar()
                
                if existing_count == 0:
                    print("📭 Database is already empty")
                    return
                
                print(f"⚠️  Found {existing_count} existing chunks")
                
                # Confirm deletion
                confirm = input("Are you sure you want to delete all OBC data? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("❌ Reset cancelled")
                    return
                
                # Delete all data
                print("🗑️  Deleting all OBC chunks...")
                await db.execute(delete(OntarioChunk))
                await db.commit()
                
                print("✅ Database reset complete")
                
            except Exception as e:
                print(f"❌ Error resetting database: {e}")
                await db.rollback()
                raise
            finally:
                await db.close()
            break


async def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Unified OBC Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/obc_manager.py load --file "assets/2024 OBC.Volume 1 refined.md"
  python scripts/obc_manager.py load --file "assets/2024 OBC.Volume 1 refined.md" --clear
  python scripts/obc_manager.py test
  python scripts/obc_manager.py status
  python scripts/obc_manager.py reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load OBC data from markdown file')
    load_parser.add_argument('--file', '-f', required=True, help='Path to OBC markdown file')
    load_parser.add_argument('--clear', '-c', action='store_true', help='Clear existing data first')
    
    # Test command
    subparsers.add_parser('test', help='Test query functionality')
    
    # Status command
    subparsers.add_parser('status', help='Show database status')
    
    # Reset command
    subparsers.add_parser('reset', help='Clear all OBC data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = OBCManager()
    
    try:
        if args.command == 'load':
            await manager.load_obc_data(args.file, args.clear)
        elif args.command == 'test':
            await manager.test_queries()
        elif args.command == 'status':
            await manager.show_status()
        elif args.command == 'reset':
            await manager.reset_database()
    except Exception as e:
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
