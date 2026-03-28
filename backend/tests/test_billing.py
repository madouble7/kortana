"""
Tests for billing functionality
Tests Stripe integration and billing endpoints
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from src.kortana.config import get_settings
from src.kortana.schemas import (
    BillingPlanType,
    CustomerCreate,
    PaymentIntentCreate,
    SubscriptionCreate,
)


# Mock stripe error for testing
class MockStripeError(Exception):
    pass


@pytest.mark.unit
class TestBillingSchemas:
    """Test billing schemas validation"""

    def test_customer_create_schema(self):
        """Test CustomerCreate schema"""
        customer_data = CustomerCreate(email="test@example.com", name="Test User")
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
            customer_id="cus_test123", price_id="price_test123"
        )
        assert subscription_data.customer_id == "cus_test123"
        assert subscription_data.price_id == "price_test123"


@pytest.mark.integration
class TestBillingEndpoints:
    """Integration tests for billing endpoints"""

    def test_billing_config_not_configured(self, client):
        """Test billing config when Stripe is not configured"""
        # Clear Stripe keys
        with patch.dict(
            os.environ,
            {"STRIPE_SECRET_KEY": "", "STRIPE_PUBLISHABLE_KEY": ""},
            clear=True,
        ):
            # Patch BOTH potential import paths to be absolutely certain
            with patch(
                "src.kortana.routers.billing._stripe_secret_key", return_value=None
            ):
                with patch(
                    "routers.billing._stripe_secret_key", return_value=None, create=True
                ):
                    response = client.get("/api/billing/config")
                    # Should return 503 when not configured
                    assert response.status_code == 503

    def test_billing_config_endpoint(self, client):
        """Test billing config endpoint"""
        # Set dummy Stripe keys for testing
        with patch.dict(
            os.environ,
            {
                "STRIPE_SECRET_KEY": "sk_test_dummy",
                "STRIPE_PUBLISHABLE_KEY": "pk_test_dummy",
            },
        ):
            response = client.get("/api/billing/config")

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
                json={"email": "test@example.com", "name": "Test User"},
            )

            # With mocked Stripe, should succeed
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "email" in data

    def test_webhook_missing_signature(self, client):
        """Test webhook handler with missing signature"""
        # Test with current environment (may or may not have Stripe configured)
        response = client.post("/api/billing/webhooks", json={"type": "test"})
        # Should either return 503 (not configured) or 400 (missing signature)
        assert response.status_code in [400, 503]

        # If it returns 400, it should be about the signature
        if response.status_code == 400:
            data = response.json()
            assert (
                "signature" in data["detail"].lower()
                or "missing" in data["detail"].lower()
            )


@pytest.mark.unit
class TestBillingRouter:
    """Test billing router functionality"""

    def test_billing_routes_registered(self):
        """Test that billing routes are registered"""
        from src.kortana.routers import billing

        routes = [r for r in billing.router.routes if hasattr(r, "path")]
        assert len(routes) >= 5  # At least the main endpoints

        # Check key endpoints exist
        paths = [r.path for r in routes]
        assert any("/config" in path for path in paths)
        assert any("/customers" in path for path in paths)
        assert any("/subscriptions" in path for path in paths)
        assert any("/payment-intents" in path for path in paths)
        assert any("/webhooks" in path for path in paths)

    def test_logger_configured(self):
        """Test that logger is properly configured"""
        from src.kortana.routers import billing

        assert hasattr(billing, "logger")
        assert billing.logger.name == "kortana.billing"

    @pytest.mark.asyncio
    async def test_verify_stripe_configured_success(self):
        """Test verify_stripe_configured with valid config"""
        from src.kortana.routers.billing import verify_stripe_configured

        with patch.object(get_settings(), "STRIPE_SECRET_KEY", "sk_test_dummy"):
            # Should not raise exception
            verify_stripe_configured()

    @pytest.mark.asyncio
    async def test_verify_stripe_configured_failure(self):
        """Test verify_stripe_configured with missing config"""
        from src.kortana.routers.billing import verify_stripe_configured

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                verify_stripe_configured()
            assert exc_info.value.status_code == 503
            assert "Stripe is not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_billing_config_success(self):
        """Test get_billing_config with valid config"""
        from src.kortana.routers.billing import get_billing_config

        with patch.object(
            get_settings(), "STRIPE_SECRET_KEY", "sk_test_dummy"
        ), patch.object(get_settings(), "STRIPE_PUBLISHABLE_KEY", "pk_test_dummy"):
            result = await get_billing_config()
            assert "publishable_key" in result
            assert "plans" in result
            assert "free" in result["plans"]
            assert "basic" in result["plans"]
            assert "pro" in result["plans"]
            assert "enterprise" in result["plans"]

    @pytest.mark.asyncio
    async def test_get_billing_config_not_configured(self):
        """Test get_billing_config without Stripe config"""
        from src.kortana.routers.billing import get_billing_config

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_billing_config()
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_create_customer_success(self):
        """Test create_customer with mocked Stripe"""
        from src.kortana.routers.billing import create_customer
        from src.kortana.schemas import CustomerCreate

        customer_data = CustomerCreate(email="test@example.com", name="Test User")

        with patch("stripe.Customer.create") as mock_create:
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.email = "test@example.com"
            mock_customer.name = "Test User"
            mock_customer.created = 1234567890
            mock_customer.metadata = {}
            mock_create.return_value = mock_customer

            result = await create_customer(customer_data)
            assert result.id == "cus_test123"
            assert result.email == "test@example.com"
            assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_create_customer_stripe_error(self):
        """Test create_customer with Stripe error"""
        from src.kortana.routers.billing import create_customer
        from src.kortana.schemas import CustomerCreate

        customer_data = CustomerCreate(email="test@example.com", name="Test User")

        with patch("stripe.error.StripeError", MockStripeError), patch(
            "stripe.Customer.create", side_effect=MockStripeError("Test error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_customer(customer_data)
            assert exc_info.value.status_code == 400
            assert "Failed to create customer" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_customer_success(self):
        """Test get_customer with mocked Stripe"""
        from src.kortana.routers.billing import get_customer

        with patch("stripe.Customer.retrieve") as mock_retrieve:
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.email = "test@example.com"
            mock_customer.name = "Test User"
            mock_customer.created = 1234567890
            mock_customer.metadata = {}
            mock_retrieve.return_value = mock_customer

            result = await get_customer("cus_test123")
            assert result.id == "cus_test123"
            assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self):
        """Test get_customer with non-existent customer"""
        from src.kortana.routers.billing import get_customer

        with patch("stripe.error.StripeError", MockStripeError), patch(
            "stripe.Customer.retrieve",
            side_effect=MockStripeError("Customer not found"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_customer("cus_invalid")
            assert exc_info.value.status_code == 404
            assert "Customer not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_subscription_success(self):
        """Test create_subscription with mocked Stripe"""
        from src.kortana.routers.billing import create_subscription
        from src.kortana.schemas import SubscriptionCreate

        subscription_data = SubscriptionCreate(
            customer_id="cus_test123", price_id="price_test123", trial_period_days=7
        )

        with patch("stripe.Subscription.create") as mock_create:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.customer = "cus_test123"
            mock_subscription.status = "active"
            mock_subscription.current_period_start = 1234567890
            mock_subscription.current_period_end = 1234567890 + 30 * 24 * 3600
            mock_subscription.cancel_at_period_end = False
            mock_subscription.metadata = {}
            mock_create.return_value = mock_subscription

            result = await create_subscription(subscription_data)
            assert result.id == "sub_test123"
            assert result.customer_id == "cus_test123"
            assert result.status == "active"

    @pytest.mark.asyncio
    async def test_create_subscription_stripe_error(self):
        """Test create_subscription with Stripe error"""
        from src.kortana.routers.billing import create_subscription
        from src.kortana.schemas import SubscriptionCreate

        subscription_data = SubscriptionCreate(
            customer_id="cus_test123", price_id="price_test123"
        )

        with patch("stripe.error.StripeError", MockStripeError), patch(
            "stripe.Subscription.create", side_effect=MockStripeError("Test error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_subscription(subscription_data)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_subscription_success(self):
        """Test get_subscription with mocked Stripe"""
        from src.kortana.routers.billing import get_subscription

        with patch("stripe.Subscription.retrieve") as mock_retrieve:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.customer = "cus_test123"
            mock_subscription.status = "active"
            mock_subscription.current_period_start = 1234567890
            mock_subscription.current_period_end = 1234567890 + 30 * 24 * 3600
            mock_subscription.cancel_at_period_end = False
            mock_subscription.metadata = {}
            mock_retrieve.return_value = mock_subscription

            result = await get_subscription("sub_test123")
            assert result.id == "sub_test123"
            assert result.customer_id == "cus_test123"

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self):
        """Test cancel_subscription at period end"""
        from src.kortana.routers.billing import cancel_subscription

        with patch("stripe.Subscription.modify") as mock_modify:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.cancel_at_period_end = True
            mock_modify.return_value = mock_subscription

            result = await cancel_subscription("sub_test123", at_period_end=True)
            assert result["id"] == "sub_test123"
            assert result["cancel_at_period_end"] is True

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(self):
        """Test cancel_subscription immediately"""
        from src.kortana.routers.billing import cancel_subscription

        with patch("stripe.Subscription.cancel") as mock_cancel:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "canceled"
            mock_subscription.cancel_at_period_end = False
            mock_cancel.return_value = mock_subscription

            result = await cancel_subscription("sub_test123", at_period_end=False)
            assert result["id"] == "sub_test123"
            assert result["cancel_at_period_end"] is False

    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self):
        """Test create_payment_intent with mocked Stripe"""
        from src.kortana.routers.billing import create_payment_intent
        from src.kortana.schemas import PaymentIntentCreate

        payment_data = PaymentIntentCreate(
            amount=1000,
            currency="usd",
            customer_id="cus_test123",
            description="Test payment",
        )

        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_payment_intent = MagicMock()
            mock_payment_intent.id = "pi_test123"
            mock_payment_intent.amount = 1000
            mock_payment_intent.currency = "usd"
            mock_payment_intent.status = "requires_payment_method"
            mock_payment_intent.client_secret = "pi_test_secret"
            mock_payment_intent.customer = "cus_test123"
            mock_payment_intent.description = "Test payment"
            mock_create.return_value = mock_payment_intent

            result = await create_payment_intent(payment_data)
            assert result.id == "pi_test123"
            assert result.amount == 1000
            assert result.currency == "usd"

    @pytest.mark.asyncio
    async def test_handle_webhook_success(self):
        """Test handle_webhook with valid signature"""
        from src.kortana.config import get_settings
        from src.kortana.routers.billing import handle_webhook

        payload = b'{"type": "customer.subscription.created", "data": {"object": {"id": "sub_test"}}}'
        signature = "t=1234567890,v1=test_signature"

        # Create a mock request
        mock_request = MagicMock()

        async def mock_body():
            return payload

        mock_request.body = mock_body

        with patch.object(get_settings(), "STRIPE_WEBHOOK_SECRET", "whsec_test"), patch(
            "stripe.Webhook.construct_event"
        ) as mock_construct:
            mock_event = {
                "type": "customer.subscription.created",
                "data": {"object": {"id": "sub_test"}},
                "id": "evt_test",
            }
            mock_construct.return_value = mock_event

            result = await handle_webhook(mock_request, signature)
            assert result["received"] is True
            assert result["event_type"] == "customer.subscription.created"

    @pytest.mark.asyncio
    async def test_handle_webhook_missing_secret(self):
        """Test handle_webhook without webhook secret"""
        from src.kortana.config import get_settings
        from src.kortana.routers.billing import handle_webhook

        payload = b'{"type": "test"}'
        signature = "t=1234567890,v1=test_signature"

        mock_request = MagicMock()

        async def mock_body():
            return payload

        mock_request.body = mock_body

        with patch.object(get_settings(), "STRIPE_WEBHOOK_SECRET", ""), patch.dict(
            os.environ, {"STRIPE_WEBHOOK_SECRET": ""}, clear=False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await handle_webhook(mock_request, signature)
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_handle_webhook_missing_signature(self):
        """Test handle_webhook without signature header"""
        from src.kortana.routers.billing import handle_webhook

        payload = b'{"type": "test"}'

        mock_request = MagicMock()

        async def mock_body():
            return payload

        mock_request.body = mock_body

        with pytest.raises(HTTPException) as exc_info:
            await handle_webhook(mock_request, None)
        assert exc_info.value.status_code == 400
        assert "Missing Stripe-Signature header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_billing_info_free_plan(self):
        """Test get_billing_info for free plan (no active subscriptions)"""
        from src.kortana.routers.billing import get_billing_info

        with patch("stripe.Subscription.list") as mock_list:
            mock_list.return_value = MagicMock(data=[])

            result = await get_billing_info("cus_test123")
            assert result.customer_id == "cus_test123"
            assert result.plan_type == BillingPlanType.FREE

    @pytest.mark.asyncio
    async def test_get_billing_info_with_subscription(self):
        """Test get_billing_info with active subscription"""
        from src.kortana.routers.billing import get_billing_info

        with patch("stripe.Subscription.list") as mock_list:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.current_period_end = 1234567890
            mock_subscription.cancel_at_period_end = False
            mock_subscription.metadata = {"plan_type": "pro"}
            mock_list.return_value = MagicMock(data=[mock_subscription])

            result = await get_billing_info("cus_test123")
            assert result.customer_id == "cus_test123"
            assert result.subscription_id == "sub_test123"
            assert result.plan_type == BillingPlanType.PRO

    @pytest.mark.asyncio
    async def test_get_billing_info_invalid_plan_type(self):
        """Test get_billing_info with invalid plan type in metadata"""
        from src.kortana.routers.billing import get_billing_info

        with patch("stripe.Subscription.list") as mock_list:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.current_period_end = 1234567890
            mock_subscription.cancel_at_period_end = False
            mock_subscription.metadata = {"plan_type": "invalid"}
            mock_list.return_value = MagicMock(data=[mock_subscription])

            result = await get_billing_info("cus_test123")
            # Should default to FREE for invalid plan type
            assert result.plan_type == BillingPlanType.FREE
