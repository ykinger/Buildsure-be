"""
BuildSure Flask Application Factory
"""
from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import google.generativeai as genai
import sys
import os
from app.utils.prompt_builder import PromptBuilder 

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
    
    # Configure CORS
    CORS(app, 
         origins=['http://localhost:3000'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Initialize services and repositories
    with app.app_context():
        from app.repositories.project_repository import ProjectRepository
        from app.repositories.code_matrix_repository import CodeMatrixRepository
        from app.services.project_service import ProjectService
        from app.services.ai_service import AIService
        
        # Create repository instances
        project_repository = ProjectRepository(db.session)
        code_matrix_repository = CodeMatrixRepository(db.session)

        # Create Gemini client
        genai.configure(api_key=app.config.get('GEMINI_API_KEY'))
        gemini_model_client = genai.GenerativeModel(app.config.get('GEMINI_MODEL'))

        template_dir = os.path.join(os.getcwd(), 'assets/prompt-parts/')

        ai_service = AIService(gemini_model_client, prompt_builder=PromptBuilder(template_dir=template_dir))
        project_service = ProjectService(project_repository, code_matrix_repository, ai_service)
        
        # Store in app context for dependency injection
        app.extensions['project_repository'] = project_repository
        app.extensions['code_matrix_repository'] = code_matrix_repository
        app.extensions['project_service'] = project_service
        app.extensions['ai_service'] = ai_service
    
    # Register blueprints
    from app.controllers.health_controller import health_bp
    from app.controllers.project_controller import project_bp
    
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(project_bp)
    
    return app
