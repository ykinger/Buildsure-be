#!/usr/bin/env python3
"""Reset Alembic version table."""
import asyncio
from app.database import engine
from sqlalchemy import text


async def reset():
    """Reset alembic version table."""
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM alembic_version"))
        print("✓ Cleared alembic_version table")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset())
