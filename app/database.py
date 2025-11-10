"""Database connection and session management."""
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

from app.config.settings import settings

# Create async engine using settings
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Connection pool size
    max_overflow=10  # Maximum overflow connections
)

# Create async session maker
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Async database session dependency"""
    async with async_session_maker() as session:
        yield session


async def test_database_connection():
    """
    Test the database connection by executing a simple query.
    Raises an exception if the connection fails.
    """
    try:
        async with engine.begin() as conn:
            # Execute a simple query to test the connection
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to database at '{settings.async_database_url}'. "
            f"Please ensure the database is running and the connection string is correct. "
            f"Error: {str(e)}"
        ) from e


class CustomBase(SQLModel):
    """Custom Base class for models, to allow global customizations"""
    pass
