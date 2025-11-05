"""Database connection and session management."""
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# TODO: Not here, move to app or config module and pass loaded config to this module and avoid os.getenv calls here
load_dotenv()

# Database URL - Let's fail if not provided
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

# Print sql statements we execute?
SQL_ECHO=os.getenv("SQL_ECHO", "false").lower() == "true"

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=SQL_ECHO,
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

class CustomBase(SQLModel):
    """Custom Base class for models, to allow global customizations"""
    pass
