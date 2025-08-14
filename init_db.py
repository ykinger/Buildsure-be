#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database tables for the BuildSure application.
Run this script to create all database tables.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import BaseModel


def init_database():
    """Initialize the database with all tables."""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            print("✅ Database connection test successful!")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    return True


if __name__ == "__main__":
    print("🚀 Initializing BuildSure database...")
    
    if init_database():
        print("🎉 Database initialization completed successfully!")
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)
