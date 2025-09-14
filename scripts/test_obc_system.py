"""
Test script for the OBC knowledge system.
Demonstrates the functionality of the Ontario Building Code ingestion and retrieval system.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_async_db
from app.services.knowledge_service import KnowledgeService


async def test_obc_system():
    """Test the complete OBC system."""
    print("=== Testing Ontario Building Code Knowledge System ===\n")
    
    async for db in get_async_db():
        try:
            service = KnowledgeService(db)
            
            # Test 1: Get article count
            print("1. Testing article count...")
            count = await service.get_obc_article_count()
            print(f"   Total articles in database: {count}\n")
            
            # Test 2: Get specific article
            print("2. Testing specific article retrieval (3.2.1.1)...")
            content = await service.get_obc_context("3.2.1.1")
            print(f"   Content preview: {content[:150]}...\n")
            
            # Test 3: Get subsection
            print("3. Testing subsection retrieval (3.2.1)...")
            content = await service.get_obc_context("3.2.1")
            article_count = len([line for line in content.split('\n') if line.startswith('##')])
            print(f"   Found {article_count} articles in subsection 3.2.1\n")
            
            # Test 4: Get section
            print("4. Testing section retrieval (3.2)...")
            content = await service.get_obc_context("3.2")
            article_count = len([line for line in content.split('\n') if line.startswith('##')])
            print(f"   Found {article_count} articles in section 3.2\n")
            
            # Test 5: Get references for a part
            print("5. Testing reference listing for part 3...")
            references = await service.get_obc_references(part="3")
            print(f"   Found {len(references)} references in part 3")
            print(f"   First 5 references: {references[:5]}\n")
            
            # Test 6: Test non-existent reference
            print("6. Testing non-existent reference...")
            content = await service.get_obc_context("99.99.99.99")
            print(f"   Result: {content}\n")
            
            print("=== All tests completed successfully! ===")
            
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(test_obc_system())
