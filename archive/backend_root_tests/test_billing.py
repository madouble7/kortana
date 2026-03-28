"""
Test billing functionality
Tests Stripe integration and billing endpoints
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_settings

def test_billing_configuration():
    """Test that billing configuration is loaded"""
    settings = get_settings()
    
    print("\n" + "=" * 60)
    print("🧪 Testing Billing Configuration")
    print("=" * 60)
    
    # Check Stripe keys
    stripe_configured = bool(settings.STRIPE_SECRET_KEY)
    print(f"\n✓ Stripe Secret Key: {'✅ Configured' if stripe_configured else '❌ Not configured'}")
    print(f"✓ Stripe Publishable Key: {'✅ Configured' if settings.STRIPE_PUBLISHABLE_KEY else '❌ Not configured'}")
    print(f"✓ Stripe Webhook Secret: {'✅ Configured' if settings.STRIPE_WEBHOOK_SECRET else '❌ Not configured'}")
    
    if stripe_configured:
        # Test Stripe connection
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Try to retrieve account info
            account = stripe.Account.retrieve()
            print("\n✅ Stripe Connection: SUCCESS")
            print(f"   Account ID: {account.id}")
            print(f"   Country: {account.country}")
            print(f"   Currency: {account.default_currency}")
        except ImportError:
            print("\n⚠️  Stripe package not installed")
            print("   Run: pip install stripe")
        except Exception as e:
            print("\n❌ Stripe Connection: FAILED")
            print(f"   Error: {str(e)}")
    else:
        print("\n⚠️  Stripe not configured - billing features will not work")
        print("   Set STRIPE_SECRET_KEY in .env file")
    
    print("\n" + "=" * 60)
    print("✓ Billing configuration test complete")
    print("=" * 60 + "\n")
    
    return stripe_configured


def test_billing_router_import():
    """Test that billing router can be imported"""
    print("\n" + "=" * 60)
    print("🧪 Testing Billing Router Import")
    print("=" * 60)
    
    try:
        from routers import billing
        print("\n✅ Billing router imported successfully")
        print(f"   Router endpoints: {len(billing.router.routes)} routes")
        
        # List endpoints
        print("\n   Available endpoints:")
        for route in billing.router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    print(f"      {method} {route.path}")
        
        return True
    except ImportError as e:
        print(f"\n❌ Failed to import billing router: {e}")
        return False
    finally:
        print("\n" + "=" * 60)
        print("✓ Billing router import test complete")
        print("=" * 60 + "\n")


def test_billing_schemas():
    """Test that billing schemas are defined"""
    print("\n" + "=" * 60)
    print("🧪 Testing Billing Schemas")
    print("=" * 60)
    
    try:
        from schemas import (
            BillingPlanType,
            CustomerCreate,
            Customer,
            SubscriptionCreate,
            Subscription,
            PaymentIntentCreate,
            PaymentIntent,
            BillingInfo,
        )
        
        print("\n✅ All billing schemas imported successfully")
        print("\n   Available schemas:")
        print("      - BillingPlanType (Enum)")
        print("      - CustomerCreate")
        print("      - Customer")
        print("      - SubscriptionCreate")
        print("      - Subscription")
        print("      - PaymentIntentCreate")
        print("      - PaymentIntent")
        print("      - BillingInfo")
        
        # Test creating a schema instance
        customer_data = CustomerCreate(
            email="test@example.com",
            name="Test User"
        )
        print(f"\n✅ Schema validation works: {customer_data.email}")
        
        return True
    except ImportError as e:
        print(f"\n❌ Failed to import billing schemas: {e}")
        return False
    finally:
        print("\n" + "=" * 60)
        print("✓ Billing schemas test complete")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 BILLING FUNCTIONALITY TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_billing_configuration()))
    results.append(("Router Import", test_billing_router_import()))
    results.append(("Schemas", test_billing_schemas()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    sys.exit(0 if passed == total else 1)
