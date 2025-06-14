# Use Python Alpine as base image for smaller size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies required for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    redis \
    libffi-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev \
    git \
    curl \
    build-base \
    file-dev \
    libmagic

# Download a specific version of the uv installer
ADD https://astral.sh/uv/0.7.13/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY requirements.txt ./

# Install dependencies using uv with --system flag
RUN uv pip install --system -r requirements.txt

# Copy alembic configuration
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Copy application code
COPY app/ ./app/
COPY setup_database.py ./
COPY docker-entrypoint.sh ./

# Create uploads directory
RUN mkdir -p /app/uploads/original /app/uploads/processed

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Change ownership of app directory and make alembic executable
RUN chown -R appuser:appgroup /app && \
    chmod +x /root/.local/bin/alembic || true

# Install alembic globally to ensure it's available
RUN uv pip install --system alembic

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]