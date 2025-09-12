"""
Database configuration and session management for FastAPI with SQLAlchemy 2.0
"""
import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Database URL - using SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./buildsure.db")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./buildsure.db")

# Create sync engine for migrations
sync_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create async engine for FastAPI (lazy initialization)
async_engine = None

def get_async_engine():
    """Get or create async engine"""
    global async_engine
    if async_engine is None:
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
    return async_engine

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base class for models
Base = declarative_base()


# Dependency for getting sync database session (for migrations)
def get_db() -> Session:
    """Get synchronous database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency for getting async database session (for FastAPI endpoints)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session"""
    engine = get_async_engine()
    AsyncSessionLocal = sessionmaker(
        bind=engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Create tables
async def create_tables():
    """Create all tables"""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Drop tables (for testing)
async def drop_tables():
    """Drop all tables"""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
