import os
import subprocess
from app.config import settings
from sqlalchemy import create_engine, text
from app.database import Base, engine

def test_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_alembic_migrations():
    """Run Alembic migrations to create/update database schema"""
    try:
        print("🚀 Running Alembic migrations...")
        
        # Set the working directory to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Try different alembic commands in order of preference
        alembic_commands = [
            ["python", "-m", "alembic", "upgrade", "head"],
            ["alembic", "upgrade", "head"],
            ["/root/.local/bin/alembic", "upgrade", "head"]
        ]
        
        for cmd in alembic_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                    timeout=60  # Add timeout to prevent hanging
                )
                
                if result.returncode == 0:
                    print("✅ Alembic migrations completed successfully!")
                    if result.stdout:
                        print(result.stdout)
                    return True
                else:
                    print(f"⚠️  Command {' '.join(cmd)} failed: {result.stderr}")
                    continue
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"⚠️  Command {' '.join(cmd)} not available or timed out: {e}")
                continue
                
        print("❌ All Alembic commands failed")
        return False
            
    except Exception as e:
        print(f"❌ Error running Alembic migrations: {e}")
        return False

def create_tables_directly():
    """Create tables directly using SQLAlchemy (fallback method)"""
    try:
        print("🔧 Creating tables directly with SQLAlchemy...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def setup_database():
    """Setup database with Alembic migrations"""
    print("🏗️  Setting up database...")
    
    # Test connection first
    if not test_database_connection():
        return False
    
    # Try to run Alembic migrations first
    if run_alembic_migrations():
        return True
    
    # Fallback to direct table creation
    print("📋 Falling back to direct table creation...")
    return create_tables_directly()