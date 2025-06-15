import pytest
from app.utils.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.utils.file_handler import validate_file, get_file_url
from app.utils.razorpay_utils import verify_razorpay_signature, verify_webhook_signature
from fastapi import UploadFile
import io


class TestAuthUtils:
    """Test authentication utility functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1

    def test_invalid_jwt_token(self):
        """Test verification of invalid JWT token"""
        invalid_token = "invalid.jwt.token"
        payload = verify_token(invalid_token)
        assert payload is None


class TestFileHandler:
    """Test file handling utility functions"""

    def test_get_file_url(self):
        """Test file URL generation"""
        file_path = "./uploads/test.jpg"
        url = get_file_url(file_path)
        
        assert url == "http://localhost:8000/uploads/test.jpg"

    def test_get_file_url_none(self):
        """Test file URL generation with None input"""
        url = get_file_url(None)
        assert url is None

    def test_validate_file_mock(self):
        """Test file validation with mock file"""
        # Create a mock file
        file_content = b"fake image content"
        mock_file = UploadFile(filename="test.jpg", file=io.BytesIO(file_content))
        
        # This should pass validation
        result = validate_file(mock_file)
        assert result is True

    def test_validate_file_invalid_extension(self):
        """Test file validation with invalid extension"""
        file_content = b"fake content"
        mock_file = UploadFile(filename="test.txt", file=io.BytesIO(file_content))
        
        # This should raise an exception
        with pytest.raises(Exception):
            validate_file(mock_file)


class TestRazorpayUtils:
    """Test Razorpay utility functions"""

    def test_verify_razorpay_signature_invalid(self):
        """Test Razorpay signature verification with invalid data"""
        # Test with invalid signature (will fail without proper secret)
        result = verify_razorpay_signature("order_123", "pay_123", "invalid_signature")
        assert result is False

    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid data"""
        # Test with invalid signature (will fail without proper secret)
        result = verify_webhook_signature("payload", "invalid_signature")
        assert result is False
