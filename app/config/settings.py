"""
Application Configuration Settings
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Configuration
    DB_HOST: str = os.environ.get('DB_HOST', 'plm1w6.h.filess.io')
    DB_NAME: str = os.environ.get('DB_NAME', 'buildsure_passagesee')
    DB_USER: str = os.environ.get('DB_USER', 'buildsure_passagesee')
    DB_PASSWORD: str = os.environ.get('DB_PASSWORD', 'd3f8fa3070f91f1a4ba7ac150b9836994e85607b')
    DB_PORT: str = os.environ.get('DB_PORT', '5433')
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construct the database URI for PostgreSQL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    
    # Database Connection Pool Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 2,           # 2 persistent connections
        'max_overflow': 5,        # Up to 5 additional connections when needed
        'pool_timeout': 30,       # 30 seconds to wait for connection
        'pool_recycle': 3600,     # Recreate connections every hour
        'pool_pre_ping': True     # Test connections before use
    }
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.environ.get('GEMINI_MODEL', 'gemini-pro')
    GEMINI_TEMPERATURE: float = float(os.environ.get('GEMINI_TEMPERATURE', '0.7'))
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.environ.get('GEMINI_MAX_OUTPUT_TOKENS', '2048'))
    
    # API configuration
    API_VERSION: str = 'v1'
    
    @staticmethod
    def init_app(app) -> None:
        """Initialize app-specific configuration."""
        pass


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG: bool = True
    DEVELOPMENT: bool = True
    SQLALCHEMY_ECHO: bool = True
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Use SQLite for development."""
        return "sqlite:///buildsure_dev.db"
    
    # Override engine options for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False}  # Allow SQLite to work with Flask threading
    }


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG: bool = False
    PRODUCTION: bool = True


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration object based on environment name."""
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, DevelopmentConfig)()
