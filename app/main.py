"""
FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import (
    organizations_router,
    users_router,
    projects_router,
    sections_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    yield
    # Shutdown
    pass


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
