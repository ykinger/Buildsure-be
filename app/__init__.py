"""
BuildSure Flask Application Factory
"""
from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment name ('development', 'production', 'testing')
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from app.config.settings import get_config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.controllers.health_controller import health_bp
    from app.controllers.ai_controller import ai_bp
    from app.controllers.project_controller import project_bp
    
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')
    app.register_blueprint(project_bp, url_prefix='/api/v1')
    
    return app
