
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.user import User
from app.services.stripe_service import StripeService
from app.core.config import FRONTEND_URL # Ensure this is available

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a Stripe Checkout URL for the Pro Plan.
    """
    service = StripeService(db)
    
    # Define redirect URLs
    # Assuming frontend has /success and /cancel routes
    # Usually locally: http://localhost:5173/subscriptions?success=true&session_id={CHECKOUT_SESSION_ID}
    success_url = f"{FRONTEND_URL}/subscriptions?success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{FRONTEND_URL}/subscriptions?canceled=true"
    
    checkout_url = service.create_checkout_session(current_user, success_url, cancel_url)
    
    return {"url": checkout_url}

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    """
    Handle Stripe Webhooks
    """
    payload = await request.body()
    service = StripeService(db)
    
    try:
        return service.handle_webhook(payload, stripe_signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    """
    Get all active subscription plans.
    """
    from app.models.subscription import SubscriptionPlan
    # Ensure default Pro plan exists
    plans = db.query(SubscriptionPlan).all()
    if not plans:
        # Fallback seed if empty
        pro_plan = SubscriptionPlan(
            name='Pro', 
            price_monthly=39.99,
            description='The ultimate tool for sports arbitrage',
            features='Real-time Alerts,Unlimited Strategies,Auto-Calculator' # Simplified storage if needed
        )
        db.add(pro_plan)
        db.commit()
        plans = [pro_plan]
    
    return plans

@router.get("/my-subscription")
def get_my_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Get current user's subscription details
    """
    from app.models.subscription import UserSubscription, SubscriptionPlan
    
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == current_user.id).first()
    
    if not sub:
        return None
        
    # Eager load plan
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    
    return {
        "status": sub.status,
        "plan": plan,
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "trial_days_remaining": 0 # No trials for now
    }

@router.post("/checkout")
async def create_checkout_alias(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Alias for create-checkout-session to match frontend expectation.
    Frontend sends { "plan_id": ... }
    """
    # Simply call the main logic
    service = StripeService(db)
    success_url = f"{FRONTEND_URL}/subscriptions?success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{FRONTEND_URL}/subscriptions?canceled=true"
    
    url = service.create_checkout_session(current_user, success_url, cancel_url)
    return {"checkout_url": url}

@router.post("/sync-subscription")
def sync_subscription(
    session_id: str,
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Force sync subscription status from Stripe Session ID.
    """
    service = StripeService(db)
    synced = service.sync_subscription(session_id)
    if not synced:
        raise HTTPException(status_code=400, detail="Could not sync subscription")
    return {"status": "synced"}

    return {"status": "synced"}

@router.post("/create-portal-session")
def create_portal_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Customer Portal session.
    """
    service = StripeService(db)
    return_url = f"{FRONTEND_URL}/subscriptions"
    portal_url = service.create_portal_session(current_user, return_url)
    return {"url": portal_url}

@router.post("/cancel")
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Cancel the user's subscription at period end.
    """
    import stripe
    from app.models.subscription import UserSubscription
    
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")
    
    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True
        )
        sub.cancel_at_period_end = True
        db.commit()
        return {"message": "Subscription will be canceled at the end of the billing period"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trial-eligibility")
def check_trial_eligibility():
    return {"eligible": False, "has_used_trial": True}

@router.post("/cleanup-pending")
def cleanup_pending():
    return {"status": "cleaned"}