"""
Application Settings
Configuration management using Pydantic Settings
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    async_database_url: str = Field(
        ...,  # Required field, no default
        env="ASYNC_DATABASE_URL",
        description="Async database connection URL (PostgreSQL with asyncpg)"
    )
    sql_echo: bool = Field(
        default=False,
        env="SQL_ECHO",
        description="Echo SQL statements to console"
    )
    
    # API Configuration
    api_title: str = Field(
        default="BuildSure API",
        env="API_TITLE",
        description="API title"
    )
    api_version: str = Field(
        default="1.0.0",
        env="API_VERSION",
        description="API version"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode"
    )
    
    # Google Gemini AI Configuration
    gemini_api_key: Optional[str] = Field(
        default=None,
        env="GEMINI_API_KEY",
        description="Gemini API key for Gemini LLM"
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        env="GEMINI_MODEL",
        description="Gemini model to use"
    )
    gemini_temperature: float = Field(
        default=0.7,
        env="GEMINI_TEMPERATURE",
        description="Temperature for Gemini model"
    )
    gemini_max_tokens: int = Field(
        default=1000,
        env="GEMINI_MAX_TOKENS",
        description="Maximum tokens for Gemini responses"
    )
    
    # AI Service Configuration
    ai_fallback_question: str = Field(
        default="What specific information do you need to provide for this section of your building project?",
        env="AI_FALLBACK_QUESTION",
        description="Fallback question when AI service fails"
    )
    ai_timeout_seconds: int = Field(
        default=30,
        env="AI_TIMEOUT_SECONDS",
        description="Timeout for AI service calls in seconds"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
