#!/usr/bin/env python3
"""
Virtual Space Tech Backend Setup Script
This script helps set up the development environment
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    requirements = {
        "python": "python --version",
        "pip": "pip --version",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version"
    }
    
    missing = []
    for tool, command in requirements.items():
        try:
            subprocess.run(command.split(), capture_output=True, check=True)
            print(f"✅ {tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} is not installed")
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing requirements: {', '.join(missing)}")
        print("Please install the missing tools and run this script again.")
        return False
    
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    activate_script = "venv\\Scripts\\activate" if os.name == 'nt' else "venv/bin/activate"
    
    commands = [
        f"{activate_script} && pip install --upgrade pip",
        f"{activate_script} && pip install -r requirements.txt"
    ]
    
    for command in commands:
        if not run_command(command, f"Running: {command.split('&&')[-1].strip()}"):
            return False
    
    return True

def setup_environment_file():
    """Set up environment file"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        if run_command("copy .env.example .env" if os.name == 'nt' else "cp .env.example .env", 
                      "Creating .env file from template"):
            print("📝 Please edit .env file with your actual configuration values")
            return True
    else:
        print("❌ .env.example file not found")
        return False

def create_uploads_directory():
    """Create uploads directory"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    print("✅ Uploads directory created")
    return True

def setup_database():
    """Set up database"""
    print("🔄 Setting up database...")
    print("📝 For local PostgreSQL:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Update DATABASE_URL in .env file")
    print("   3. Run: docker-compose up -d db")
    print("   4. Run migrations: alembic upgrade head")
    
    print("\n📝 Alternative setup:")
    print("   1. Run: python -c \"from app.utils.database_setup import setup_database; setup_database()\"")
    
    return True

def show_next_steps():
    """Show next steps to user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your actual configuration values")
    print("2. Set up your database (PostgreSQL with Alembic)")
    print("3. Start the development server:")
    print("   - Local: uvicorn app.main:app --reload")
    print("   - Docker: docker-compose up")
    print("4. Visit http://localhost:8000/docs for API documentation")
    print("5. Run tests: pytest")
    
    print("\n🔗 Useful commands:")
    print("   - Start all services: docker-compose up")
    print("   - Start only database: docker-compose up -d db redis")
    print("   - Run tests: pytest")
    print("   - Run with coverage: pytest --cov=app tests/")
    print("   - Run migrations: alembic upgrade head")
    print("   - Create new migration: alembic revision --autogenerate -m \"description\"")

def main():
    """Main setup function"""
    print("🚀 Virtual Space Tech Backend Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup steps
    steps = [
        setup_virtual_environment,
        install_dependencies,
        setup_environment_file,
        create_uploads_directory,
        setup_database
    ]
    
    for step in steps:
        if not step():
            print(f"\n❌ Setup failed at step: {step.__name__}")
            sys.exit(1)
    
    show_next_steps()

if __name__ == "__main__":
    main()
