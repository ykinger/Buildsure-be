"""
BuildSure Backend Application Entry Point
"""
import os
from app import create_app
from app.config.settings import config

# Get configuration from environment variable
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config[config_name])

if __name__ == '__main__':
    # Development server configuration
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = config_name == 'development'
    
    print(f"Starting BuildSure Backend API on {host}:{port}")
    print(f"Environment: {config_name}")
    print(f"Debug mode: {debug}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )
