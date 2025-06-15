from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.routes import auth, tasks, credits, admin
from app.utils.database_setup import setup_database
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# try:
#     # Try to setup database using Alembic migrations
#     from app.utils.database_setup import setup_database
#     setup_database()
#     logger.info("✅ Database setup completed using Alembic")
# except Exception as e:
#     logger.error(f"⚠️  Database setup failed: {e}")
#     logger.error("📝 Please check your DATABASE_URL and ensure PostgreSQL is running")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A secure, production-ready backend for async image processing SaaS",
    # version="1.0.0",
    # #docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    # redoc_url="/redoc" if settings.DEBUG else None,  # Disable redoc in production
    # openapi_url="/openapi.json" if settings.DEBUG else None  # Disable OpenAPI in production
)


# Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.BACKEND_CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "Cookie",
        "Set-Cookie",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
    ],
    expose_headers=[
        "Set-Cookie",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
    ]
)

# Mount static files for serving uploaded images
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(credits.router)
app.include_router(admin.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Virtual Space Tech - Image Processing SaaS API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTTPException(status_code=404, detail="Endpoint not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
