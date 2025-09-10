#!/usr/bin/env python3
"""
Database Environment Switcher

This script helps you easily switch between development (SQLite) and production (PostgreSQL) environments.
"""

import os
import sys
from pathlib import Path

def update_env_file(env_type):
    """Update the .env file for the specified environment type."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found. Please create one from .env.example")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update FLASK_ENV
    updated_lines = []
    for line in lines:
        if line.startswith('FLASK_ENV='):
            updated_lines.append(f'FLASK_ENV={env_type}\n')
        else:
            updated_lines.append(line)
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    return True

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['development', 'production']:
        print("Usage: python switch_db_env.py [development|production]")
        print("\n  development - Use SQLite database (buildsure_dev.db)")
        print("  production  - Use PostgreSQL database (remote)")
        sys.exit(1)
    
    env_type = sys.argv[1]
    
    if update_env_file(env_type):
        if env_type == 'development':
            print("✅ Switched to DEVELOPMENT environment")
            print("   Database: SQLite (buildsure_dev.db)")
            print("   Run: python run.py")
        else:
            print("✅ Switched to PRODUCTION environment") 
            print("   Database: PostgreSQL (remote)")
            print("   Make sure your PostgreSQL credentials are set in .env")
        
        print(f"\n💡 Current FLASK_ENV: {env_type}")
    else:
        print("❌ Failed to update environment")
        sys.exit(1)

if __name__ == '__main__':
    main()
