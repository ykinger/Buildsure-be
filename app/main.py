"""
FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys

# Import all models to ensure they are registered with SQLModel.metadata
import app.models.organization
import app.models.user
import app.models.project
import app.models.data_matrix
import app.models.project_data_matrix
import app.models.knowledge_base
import app.models.data_matrix_knowledge_base
import app.models.message
import app.models.section

from app.routers import (
    organizations_router,
    users_router,
    projects_router,
    sections_router
)
from app.database import test_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Validate database connection
    try:
        print("🔍 Checking database connection...")
        await test_database_connection()
        print("✅ Database connection successful")
    except RuntimeError as e:
        print(f"❌ Database connection failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during database validation: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    yield
    
    # Shutdown
    print("🔒 Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="BuildSure API",
    description="FastAPI backend for BuildSure project management system",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(organizations_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(sections_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to BuildSure API v2.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return HTTPException(
        status_code=500,
        detail=f"Internal server error: {str(exc)}"
    )
