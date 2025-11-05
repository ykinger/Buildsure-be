#!/usr/bin/env python3
"""Test PostgreSQL database connectivity and operations."""
import asyncio
from app.database import get_db, engine
from app.models import Organization, User
from sqlalchemy import text


async def test_connection():
    """Test database connection and basic operations."""
    print("Testing PostgreSQL connection...")
    
    try:
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Connected to PostgreSQL: {version}")
        
        # Test table existence
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
        
        # Test basic CRUD operations
        async for session in get_db():
            # Create test organization (with explicit ID since it's not auto-generated)
            import uuid
            test_org = Organization(
                id=str(uuid.uuid4()),
                name="Test Organization"
            )
            session.add(test_org)
            await session.commit()
            await session.refresh(test_org)
            print(f"✓ Created test organization with ID: {test_org.id}")
            
            # Read organization
            org = await session.get(Organization, test_org.id)
            print(f"✓ Read organization: {org.name}")
            
            # Update organization
            org.name = "Updated Test Organization"
            await session.commit()
            print(f"✓ Updated organization name")
            
            # Delete organization
            await session.delete(org)
            await session.commit()
            print(f"✓ Deleted test organization")
            
            break
        
        print("\n✓ All tests passed! PostgreSQL migration successful.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
