"""
Billing Router - Stripe Integration
Handles customer management, subscriptions, and payment processing
"""

import logging
import os

import stripe
from config import get_settings
from fastapi import APIRouter, Header, HTTPException, Request
from schemas import (
    BillingInfo,
    BillingPlanType,
    Customer,
    CustomerCreate,
    PaymentIntent,
    PaymentIntentCreate,
    Subscription,
    SubscriptionCreate,
)

router = APIRouter()
logger = logging.getLogger("kortana.billing")

# Initialize Stripe
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


def _stripe_secret_key() -> str | None:
    """Resolve Stripe secret key with env override support."""
    env_value = os.getenv("STRIPE_SECRET_KEY")
    if env_value is not None:
        return env_value
    return get_settings().STRIPE_SECRET_KEY


def _stripe_publishable_key() -> str | None:
    """Resolve Stripe publishable key with env override support."""
    env_value = os.getenv("STRIPE_PUBLISHABLE_KEY")
    if env_value is not None:
        return env_value
    return get_settings().STRIPE_PUBLISHABLE_KEY


def _stripe_webhook_secret() -> str | None:
    """Resolve Stripe webhook secret with env override support."""
    env_value = os.getenv("STRIPE_WEBHOOK_SECRET")
    if env_value is not None:
        return env_value
    return get_settings().STRIPE_WEBHOOK_SECRET


def verify_stripe_configured():
    """Verify Stripe is properly configured"""
    secret_key = _stripe_secret_key()
    if not secret_key:
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured. Please set STRIPE_SECRET_KEY environment variable.",
        )
    stripe.api_key = secret_key


@router.get("/config")
async def get_billing_config():
    """Get billing configuration (public key, available plans)"""
    verify_stripe_configured()

    return {
        "publishable_key": _stripe_publishable_key(),
        "plans": {
            "free": {
                "name": "Free",
                "price": 0,
                "features": ["Basic API access", "100 requests/day"],
            },
            "basic": {
                "name": "Basic",
                "price": 9.99,
                "features": [
                    "Standard API access",
                    "1000 requests/day",
                    "Email support",
                ],
            },
            "pro": {
                "name": "Pro",
                "price": 29.99,
                "features": [
                    "Full API access",
                    "10000 requests/day",
                    "Priority support",
                    "Advanced features",
                ],
            },
            "enterprise": {
                "name": "Enterprise",
                "price": "custom",
                "features": [
                    "Unlimited API access",
                    "Custom limits",
                    "Dedicated support",
                    "SLA guarantee",
                ],
            },
        },
    }


@router.post("/customers", response_model=Customer)
async def create_customer(customer_data: CustomerCreate):
    """Create a new Stripe customer"""
    verify_stripe_configured()

    try:
        customer = stripe.Customer.create(
            email=customer_data.email,
            name=customer_data.name,
            metadata=customer_data.metadata or {},
        )

        return Customer(
            id=customer.id,
            email=customer.email,
            name=customer.name,
            created=customer.created,
            metadata=customer.metadata,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create customer: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create customer")


@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get customer details"""
    verify_stripe_configured()

    try:
        customer = stripe.Customer.retrieve(customer_id)

        return Customer(
            id=customer.id,
            email=customer.email,
            name=customer.name,
            created=customer.created,
            metadata=customer.metadata,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Customer not found")


@router.post("/subscriptions", response_model=Subscription)
async def create_subscription(subscription_data: SubscriptionCreate):
    """Create a new subscription"""
    verify_stripe_configured()

    try:
        subscription = stripe.Subscription.create(
            customer=subscription_data.customer_id,
            items=[{"price": subscription_data.price_id}],
            trial_period_days=subscription_data.trial_period_days,
            metadata=subscription_data.metadata or {},
        )

        return Subscription(
            id=subscription.id,
            customer_id=subscription.customer,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            metadata=subscription.metadata,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create subscription")


@router.get("/subscriptions/{subscription_id}", response_model=Subscription)
async def get_subscription(subscription_id: str):
    """Get subscription details"""
    verify_stripe_configured()

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        return Subscription(
            id=subscription.id,
            customer_id=subscription.customer,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            metadata=subscription.metadata,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve subscription {subscription_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Subscription not found")


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, at_period_end: bool = True):
    """Cancel a subscription"""
    verify_stripe_configured()

    try:
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id, cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.cancel(subscription_id)

        return {
            "id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to cancel subscription")


@router.post("/payment-intents", response_model=PaymentIntent)
async def create_payment_intent(payment_data: PaymentIntentCreate):
    """Create a payment intent for one-time payments"""
    verify_stripe_configured()

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=payment_data.amount,
            currency=payment_data.currency,
            customer=payment_data.customer_id,
            description=payment_data.description,
            metadata=payment_data.metadata or {},
        )

        return PaymentIntent(
            id=payment_intent.id,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status=payment_intent.status,
            client_secret=payment_intent.client_secret,
            customer_id=payment_intent.customer,
            description=payment_intent.description,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create payment intent: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create payment intent")


@router.post("/webhooks")
async def handle_webhook(
    request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhooks"""
    verify_stripe_configured()

    webhook_secret = _stripe_webhook_secret()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event["type"]
    event_data = event["data"]["object"]

    # Log event using proper logging
    logger.info(
        f"Received webhook event: {event_type}", extra={"event_id": event["id"]}
    )

    if event_type == "customer.subscription.created":
        logger.info(f"Subscription created: {event_data['id']}")
    elif event_type == "customer.subscription.updated":
        logger.info(f"Subscription updated: {event_data['id']}")
    elif event_type == "customer.subscription.deleted":
        logger.info(f"Subscription deleted: {event_data['id']}")
    elif event_type == "invoice.payment_succeeded":
        logger.info(f"Payment succeeded: {event_data['id']}")
    elif event_type == "invoice.payment_failed":
        logger.warning(f"Payment failed: {event_data['id']}")

    return {"received": True, "event_type": event_type}


@router.get("/billing-info/{customer_id}", response_model=BillingInfo)
async def get_billing_info(customer_id: str):
    """Get billing information for a customer"""
    verify_stripe_configured()

    try:
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer_id, status="active", limit=1
        )

        if subscriptions.data:
            subscription = subscriptions.data[0]

            # Determine plan type from subscription metadata
            if subscription.metadata and "plan_type" in subscription.metadata:
                plan_type_str = subscription.metadata["plan_type"]
                try:
                    plan_type = BillingPlanType(plan_type_str)
                except ValueError:
                    logger.warning(
                        f"Invalid plan type in metadata: {plan_type_str}, defaulting to FREE"
                    )
                    # Default to FREE as safer option for invalid metadata
                    plan_type = BillingPlanType.FREE
            else:
                # If subscription exists but no metadata, log warning and check price
                logger.warning(
                    f"Active subscription {subscription.id} missing plan_type metadata"
                )
                # Default to FREE to avoid overcharging; admin should fix metadata
                plan_type = BillingPlanType.FREE

            return BillingInfo(
                customer_id=customer_id,
                subscription_id=subscription.id,
                subscription_status=subscription.status,
                current_period_end=subscription.current_period_end,
                cancel_at_period_end=subscription.cancel_at_period_end,
                plan_type=plan_type,
            )
        else:
            return BillingInfo(customer_id=customer_id, plan_type=BillingPlanType.FREE)
    except stripe.error.StripeError as e:
        logger.error(
            f"Failed to retrieve billing info for customer {customer_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=404, detail="Failed to retrieve billing information"
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=404, detail=str(e))
