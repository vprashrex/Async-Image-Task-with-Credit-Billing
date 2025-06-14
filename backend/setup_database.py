#!/usr/bin/env python3
"""
Database Setup Script for Virtual Space Tech Backend

This script sets up the PostgreSQL database using Alembic migrations.
Run this script to initialize your database schema.

Usage:
    python setup_database.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


def main():
    """Main setup function"""
    
    # Import after adding to path
    try:
        from app.utils.database_setup import setup_database
        from app.config import settings
        
        print(f"📊 Database URL: {settings.DATABASE_URL}")
        print()
        
        if setup_database():
            print("\n🎉 Database setup completed successfully!")
            print("\n📋 What was created:")
            print("✅ Users table - for user authentication and credits")
            print("✅ Tasks table - for image processing tasks")
            print("✅ Payments table - for payment tracking")
            print("\n🔗 Next steps:")
            print("1. Start the development server: uvicorn app.main:app --reload")
            print("2. Visit http://localhost:8000/docs for API documentation")
            print("3. Test the endpoints with sample data")
        else:
            print("\n❌ Database setup failed!")
            print("\n🔍 Troubleshooting:")
            print("1. Make sure PostgreSQL is running")
            print("2. Check your DATABASE_URL in .env file")
            print("3. Ensure the database exists")
            print("4. Check database user permissions")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
