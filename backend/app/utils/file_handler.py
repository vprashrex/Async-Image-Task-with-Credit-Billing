import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Try to import magic for MIME type detection
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, using basic file validation")

# Security constants
MAX_FILENAME_LENGTH = 255
DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar', '.php', '.py', '.sh'}


def validate_file(file: UploadFile) -> bool:
    """Enhanced file validation with security checks"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Check filename length
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=400, detail="Filename too long")
    
    # Sanitize filename (remove dangerous chars)
    sanitized_filename = "".join(c for c in file.filename if c.isalnum() or c in '._-')
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check for dangerous file extensions
    file_extension = Path(file.filename).suffix.lower()
    if file_extension in DANGEROUS_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed for security reasons")
    
    # Check allowed extensions
    if file_extension.lstrip('.') not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content for validation
    file.file.seek(0)  # Reset file pointer
    file_content = file.file.read(1024)  # Read first 1KB for validation
    file.file.seek(0)  # Reset file pointer
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed")
    
    # Validate MIME type if magic is available
    if MAGIC_AVAILABLE:
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in settings.ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. File appears to be {mime_type}, but only images are allowed"
                )
        except Exception as e:
            logger.warning(f"MIME type detection failed: {e}")
    
    # Additional image header validation
    if not _is_valid_image_header(file_content):
        raise HTTPException(status_code=400, detail="Invalid image file format")
    
    return True


def _is_valid_image_header(content: bytes) -> bool:
    """Validate image file headers"""
    if len(content) < 12:
        return False
        
    # JPEG
    if content.startswith(b'\xff\xd8\xff'):
        return True
    # PNG
    if content.startswith(b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'):
        return True
    # GIF
    if content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
        return True
    # WebP
    if len(content) >= 12 and content[8:12] == b'WEBP':
        return True
    
    return False


def save_file(file: UploadFile, subfolder: str = "images") -> str:
    """Save uploaded file with enhanced security"""
    # Validate file first
    validate_file(file)
    
    # Sanitize filename
    original_filename = file.filename
    file_extension = Path(original_filename).suffix.lower()
    
    # Create unique filename to prevent conflicts and path traversal
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create subfolder path with validation
    if not subfolder or '..' in subfolder or os.path.isabs(subfolder):
        raise HTTPException(status_code=400, detail="Invalid subfolder")
    
    folder_path = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Full file path
    file_path = os.path.join(folder_path, unique_filename)
    
    # Ensure we're not writing outside the upload directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        # Save file with limited size reading
        with open(file_path, "wb") as buffer:
            file.file.seek(0)
            written = 0
            chunk_size = 8192  # 8KB chunks
            
            while written < settings.MAX_FILE_SIZE:
                chunk = file.file.read(min(chunk_size, settings.MAX_FILE_SIZE - written))
                if not chunk:
                    break
                buffer.write(chunk)
                written += len(chunk)
                
            if written >= settings.MAX_FILE_SIZE:
                # Remove the file if it exceeds size limit
                os.remove(file_path)
                raise HTTPException(status_code=400, detail="File too large")
                
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"File save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    return file_path


def get_file_url(file_path: Optional[str], base_url: str = "http://localhost:8000") -> Optional[str]:
    """Convert file path to URL"""
    
    base_url = settings.SERVER_URI
    
    if not file_path:
        return None
    
    # Convert backslashes to forward slashes for URL
    url_path = file_path.replace("\\", "/").replace("./", "/")
    return f"{base_url}{url_path}"


def delete_file(file_path: str) -> bool:
    """Delete a file from the filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False
