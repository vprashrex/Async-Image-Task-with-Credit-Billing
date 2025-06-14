import pytest
from tests.conftest import client, test_db, test_user, test_admin


class TestAuth:
    """Test authentication endpoints"""

    def test_signup_success(self, test_db, test_user):
        """Test successful user registration"""
        response = client.post("/auth/signup", json=test_user)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]
        assert data["credits"] == 5  # New users get 5 free credits
        assert data["is_active"] is True
        assert data["is_admin"] is False

    def test_signup_duplicate_email(self, test_db, test_user):
        """Test registration with duplicate email"""
        # Create user first
        client.post("/auth/signup", json=test_user)
        
        # Try to create again
        response = client.post("/auth/signup", json=test_user)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_signup_duplicate_username(self, test_db, test_user):
        """Test registration with duplicate username"""
        # Create user first
        client.post("/auth/signup", json=test_user)
        
        # Try with different email but same username
        duplicate_user = {
            "email": "different@example.com",
            "username": test_user["username"],
            "password": "password123"
        }
        response = client.post("/auth/signup", json=duplicate_user)
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_login_success(self, test_db, test_user):
        """Test successful login"""
        # Create user first
        client.post("/auth/signup", json=test_user)
        
        # Login
        login_data = {
            "username": test_user["email"],  # FastAPI OAuth2 uses username field
            "password": test_user["password"]
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, test_db, test_user):
        """Test login with invalid credentials"""
        # Create user first
        client.post("/auth/signup", json=test_user)
        
        # Try login with wrong password
        login_data = {
            "username": test_user["email"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, test_db):
        """Test login with non-existent user"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


def get_auth_headers(user_data):
    """Helper function to get authentication headers"""
    # Create user
    client.post("/auth/signup", json=user_data)
    
    # Login and get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
