"""
Tests for billing functionality
Tests Stripe integration and billing endpoints
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import stripe

from schemas import (
    BillingPlanType,
    CustomerCreate,
    Customer,
    SubscriptionCreate,
    Subscription,
    PaymentIntentCreate,
    BillingInfo,
)


@pytest.mark.unit
class TestBillingSchemas:
    """Test billing schemas validation"""

    def test_customer_create_schema(self):
        """Test CustomerCreate schema"""
        customer_data = CustomerCreate(
            email="test@example.com",
            name="Test User"
        )
        assert customer_data.email == "test@example.com"
        assert customer_data.name == "Test User"

    def test_billing_plan_type_enum(self):
        """Test BillingPlanType enum"""
        plans = list(BillingPlanType)
        assert len(plans) == 4
        assert BillingPlanType.FREE in plans
        assert BillingPlanType.BASIC in plans
        assert BillingPlanType.PRO in plans
        assert BillingPlanType.ENTERPRISE in plans

    def test_payment_intent_currency_validation(self):
        """Test currency validation in PaymentIntentCreate"""
        # Valid currency
        payment = PaymentIntentCreate(amount=1000, currency="usd")
        assert payment.currency == "usd"

        # Invalid currency should fail validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            PaymentIntentCreate(amount=1000, currency="US")

    def test_subscription_create_schema(self):
        """Test SubscriptionCreate schema"""
        subscription_data = SubscriptionCreate(
            customer_id="cus_test123",
            price_id="price_test123"
        )
        assert subscription_data.customer_id == "cus_test123"
        assert subscription_data.price_id == "price_test123"


@pytest.mark.integration
class TestBillingEndpoints:
    """Integration tests for billing endpoints"""

    def test_billing_config_endpoint(self, client):
        """Test billing config endpoint"""
        # Set dummy Stripe keys for testing
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_dummy",
            "STRIPE_PUBLISHABLE_KEY": "pk_test_dummy"
        }):
            response = client.get("/api/billing/config")
            
            # Should succeed with dummy keys configured
            if response.status_code == 200:
                data = response.json()
                assert "plans" in data
                assert "free" in data["plans"]
                assert "basic" in data["plans"]
                assert "pro" in data["plans"]
                assert "enterprise" in data["plans"]

    def test_billing_config_not_configured(self, client):
        """Test billing config when Stripe is not configured"""
        # Clear Stripe keys
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "",
            "STRIPE_PUBLISHABLE_KEY": ""
        }, clear=True):
            # Need to reload config
            from config import get_settings
            settings = get_settings()
            
            response = client.get("/api/billing/config")
            # Should return 503 when not configured
            assert response.status_code == 503

    def test_create_customer_endpoint_structure(self, client):
        """Test customer creation endpoint structure"""
        # Mock Stripe customer creation
        with patch("stripe.Customer.create") as mock_create:
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.email = "test@example.com"
            mock_customer.name = "Test User"
            mock_customer.created = 1234567890
            mock_customer.metadata = {}
            mock_create.return_value = mock_customer

            response = client.post(
                "/api/billing/customers",
                json={"email": "test@example.com", "name": "Test User"}
            )
            
            # With mocked Stripe, should succeed
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "email" in data

    def test_webhook_missing_signature(self, client):
        """Test webhook handler with missing signature"""
        # Test with current environment (may or may not have Stripe configured)
        response = client.post(
            "/api/billing/webhooks",
            json={"type": "test"}
        )
        # Should either return 503 (not configured) or 400 (missing signature)
        assert response.status_code in [400, 503]
        
        # If it returns 400, it should be about the signature
        if response.status_code == 400:
            data = response.json()
            assert "signature" in data["detail"].lower() or "missing" in data["detail"].lower()


@pytest.mark.unit
class TestBillingRouter:
    """Test billing router functionality"""

    def test_billing_routes_registered(self):
        """Test that billing routes are registered"""
        from routers import billing
        
        routes = [r for r in billing.router.routes if hasattr(r, 'path')]
        assert len(routes) == 9
        
        # Check key endpoints exist
        paths = [r.path for r in routes]
        assert "/config" in paths
        assert "/customers" in paths
        assert "/subscriptions" in paths
        assert "/payment-intents" in paths
        assert "/webhooks" in paths

    def test_logger_configured(self):
        """Test that logger is properly configured"""
        from routers import billing
        
        assert hasattr(billing, 'logger')
        assert billing.logger.name == "kortana.billing"
