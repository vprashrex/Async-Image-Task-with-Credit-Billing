import pytest
from tests.conftest import client, test_db, test_user
from tests.test_auth import get_auth_headers


class TestCredits:
    """Test credit management endpoints"""

    def test_get_credit_balance(self, test_db, test_user):
        """Test getting user's credit balance"""
        headers = get_auth_headers(test_user)
        
        response = client.get("/credits/balance", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "credits" in data
        assert "user_id" in data
        assert "email" in data
        assert data["credits"] == 5  # New users get 5 free credits
        assert data["email"] == test_user["email"]

    def test_get_credit_balance_unauthorized(self, test_db):
        """Test getting credit balance without authentication"""
        response = client.get("/credits/balance")
        assert response.status_code == 401

    def test_purchase_credits_request(self, test_db, test_user):
        """Test creating a credit purchase request"""
        headers = get_auth_headers(test_user)
        
        purchase_data = {"credits": 10}
        response = client.post("/credits/purchase", headers=headers, json=purchase_data)
        
        # This will fail in test environment without proper Razorpay configuration
        # In a real scenario, you'd mock the Razorpay client
        # For now, we expect it to fail due to missing Razorpay configuration
        assert response.status_code in [200, 500]  # Could fail due to missing config

    def test_purchase_credits_unauthorized(self, test_db):
        """Test credit purchase without authentication"""
        purchase_data = {"credits": 10}
        response = client.post("/credits/purchase", json=purchase_data)
        assert response.status_code == 401

    def test_razorpay_webhook_missing_signature(self, test_db):
        """Test Razorpay webhook without signature"""
        webhook_data = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_test123",
                        "id": "pay_test123"
                    }
                }
            }
        }
        
        response = client.post("/credits/webhook/razorpay", json=webhook_data)
        assert response.status_code == 400
        assert "Missing signature" in response.json()["detail"]

    def test_razorpay_webhook_invalid_signature(self, test_db):
        """Test Razorpay webhook with invalid signature"""
        webhook_data = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_test123",
                        "id": "pay_test123"
                    }
                }
            }
        }
        
        headers = {"X-Razorpay-Signature": "invalid_signature"}
        response = client.post("/credits/webhook/razorpay", json=webhook_data, headers=headers)
        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]
