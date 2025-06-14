#!/bin/sh

# Docker entrypoint script for Virtual Space Tech Backend

echo "🐳 Starting Virtual Space Tech Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
while ! python -c "
import os
import time
from sqlalchemy import create_engine, text
from app.config import settings
try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database is ready!')
    exit(0)
except Exception as e:
    print(f'❌ Database not ready: {e}')
    exit(1)
"; do
    echo "⏳ Database not ready, waiting 2 seconds..."
    sleep 2
done

# Setup database
echo "🏗️  Setting up database..."
python -c "
from app.utils.database_setup import setup_database
setup_database()
"

# Start the application
echo "🚀 Starting FastAPI application..."
exec "$@"
