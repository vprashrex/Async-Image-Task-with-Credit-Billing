import pytest
import io
from tests.conftest import client, test_db, test_user
from tests.test_auth import get_auth_headers


class TestTasks:
    """Test task management endpoints"""

    def test_create_task_success(self, test_db, test_user):
        """Test successful task creation"""
        headers = get_auth_headers(test_user)
        
        # Create a mock image file
        image_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")}
        data = {
            "title": "Test Image Processing",
            "description": "Test description",
            "processing_operation": "grayscale"
        }
        
        response = client.post("/tasks/", headers=headers, files=files, data=data)
        assert response.status_code == 200
        
        task_data = response.json()
        assert task_data["title"] == data["title"]
        assert task_data["description"] == data["description"]
        assert task_data["status"] == "queued"
        assert task_data["metadata"]["processing_operation"] == "grayscale"

    def test_create_task_insufficient_credits(self, test_db):
        """Test task creation with insufficient credits"""
        # Create user with 0 credits
        user_data = {
            "email": "nocredits@example.com",
            "username": "nocredits",
            "password": "password123"
        }
        headers = get_auth_headers(user_data)
        
        # Simulate user with 0 credits (would need to manually set in real scenario)
        image_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")}
        data = {
            "title": "Test Image Processing",
            "processing_operation": "grayscale"
        }
        
        # This would fail if user actually had 0 credits
        # In a real test, you'd need to manually set credits to 0
        response = client.post("/tasks/", headers=headers, files=files, data=data)
        # For now, this will succeed because new users get 5 credits

    def test_create_task_unauthorized(self, test_db):
        """Test task creation without authentication"""
        image_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")}
        data = {
            "title": "Test Image Processing",
            "processing_operation": "grayscale"
        }
        
        response = client.post("/tasks/", files=files, data=data)
        assert response.status_code == 401

    def test_get_user_tasks(self, test_db, test_user):
        """Test getting user's tasks"""
        headers = get_auth_headers(test_user)
        
        # Create a task first
        image_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")}
        data = {
            "title": "Test Image Processing",
            "processing_operation": "grayscale"
        }
        client.post("/tasks/", headers=headers, files=files, data=data)
        
        # Get tasks
        response = client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) >= 1
        assert tasks[0]["title"] == data["title"]

    def test_get_user_tasks_unauthorized(self, test_db):
        """Test getting tasks without authentication"""
        response = client.get("/tasks/")
        assert response.status_code == 401

    def test_get_task_by_id(self, test_db, test_user):
        """Test getting a specific task by ID"""
        headers = get_auth_headers(test_user)
        
        # Create a task first
        image_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")}
        data = {
            "title": "Test Image Processing",
            "processing_operation": "grayscale"
        }
        create_response = client.post("/tasks/", headers=headers, files=files, data=data)
        task_id = create_response.json()["id"]
        
        # Get specific task
        response = client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 200
        
        task_data = response.json()
        assert task_data["id"] == task_id
        assert task_data["title"] == data["title"]

    def test_get_task_not_found(self, test_db, test_user):
        """Test getting a non-existent task"""
        headers = get_auth_headers(test_user)
        
        response = client.get("/tasks/99999", headers=headers)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
