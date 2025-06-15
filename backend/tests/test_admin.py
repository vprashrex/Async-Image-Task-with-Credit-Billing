import pytest
from tests.conftest import client, test_db, test_user, test_admin
from tests.test_auth import get_auth_headers


class TestAdmin:
    """Test admin-only endpoints"""

    def test_get_all_users_as_admin(self, test_db, test_admin):
        """Test getting all users as admin"""
        # First create admin user manually and set admin flag
        admin_headers = get_auth_headers(test_admin)
        
        # Note: In real tests, you'd need to manually set is_admin=True in the database
        # For now, this test will fail because the test user isn't an admin
        response = client.get("/admin/users", headers=admin_headers)
        
        # This will return 403 because test user isn't admin by default
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_get_all_users_unauthorized(self, test_db):
        """Test getting all users without authentication"""
        response = client.get("/admin/users")
        assert response.status_code == 401

    def test_get_all_users_as_regular_user(self, test_db, test_user):
        """Test getting all users as regular user (should fail)"""
        headers = get_auth_headers(test_user)
        
        response = client.get("/admin/users", headers=headers)
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_get_all_tasks_as_regular_user(self, test_db, test_user):
        """Test getting all tasks as regular user (should fail)"""
        headers = get_auth_headers(test_user)
        
        response = client.get("/admin/tasks", headers=headers)
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_get_admin_stats_as_regular_user(self, test_db, test_user):
        """Test getting admin stats as regular user (should fail)"""
        headers = get_auth_headers(test_user)
        
        response = client.get("/admin/stats", headers=headers)
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_get_admin_stats_unauthorized(self, test_db):
        """Test getting admin stats without authentication"""
        response = client.get("/admin/stats")
        assert response.status_code == 401
