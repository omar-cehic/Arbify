
import stripe
import os
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.subscription import UserSubscription, SubscriptionPlan, SubscriptionPayment

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
ENDPOINT_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
# Price ID from Stripe Dashboard (hardcoded fallback or env var)
# Ideally, this should be in the DB or Env. 
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_1SpeyYB127tSmODxEHcWugMm") 

if not STRIPE_PRICE_ID:
    # Just in case the fallback failed or was empty string
    STRIPE_PRICE_ID = "price_1SpeyYB127tSmODxEHcWugMm" 

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_customer(self, user: User) -> str:
        """
        Get existing Stripe Customer ID from UserSubscription or create a new one in Stripe.
        """
        # Check if user already has a subscription record with a customer_id
        subscription = self.db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
        
        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id

        # Check by email in Stripe (to avoid duplicates if DB was wiped)
        existing_customers = stripe.Customer.list(email=user.email, limit=1)
        if existing_customers.data:
            customer_id = existing_customers.data[0].id
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user.id)}
            )
            customer_id = customer.id

        # Create/Update subscription record in DB to store this customer_id
        if not subscription:
            # Find default 'Pro' plan
            plan = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.name == 'Pro').first()
            if not plan:
                # Fallback if seed didn't run - this is risky but handles the edge case
                logger.warning("Pro plan not found in DB. Creating minimal record.")
                plan = SubscriptionPlan(name='Pro', price_monthly=29.00)
                self.db.add(plan)
                self.db.flush()

            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="pending",
                stripe_customer_id=customer_id
            )
            self.db.add(subscription)
        else:
            subscription.stripe_customer_id = customer_id
        
        self.db.commit()
        return customer_id

    def create_checkout_session(self, user: User, success_url: str, cancel_url: str):
        """
        Create a Stripe Checkout Session for the Pro Plan.
        """
        try:
            if not STRIPE_PRICE_ID:
                raise HTTPException(status_code=500, detail="Stripe Price ID is not configured (STRIPE_PRICE_ID)")

            customer_id = self._get_or_create_customer(user)

            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id)
                }
            )
            return checkout_session.url
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def create_portal_session(self, user: User, return_url: str):
        """
        Create a Stripe Customer Portal session for managing subscriptions.
        """
        try:
            customer_id = self._get_or_create_customer(user)
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return portal_session.url
        except Exception as e:
            logger.error(f"Error creating portal session: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def sync_subscription(self, session_id: str):
        """
        Manually sync a checkout session to ensure immediate status update.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                self._handle_checkout_completed(session)
                return True
            return False
        except Exception as e:
            logger.error(f"Error syncing subscription: {str(e)}")
            return False

    def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Handle incoming Stripe webhooks to update subscription status.
        """
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, ENDPOINT_SECRET
            )
        except ValueError as e:
            # Invalid payload
            logger.error("Invalid Stripe webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error("Invalid Stripe webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the specific event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_checkout_completed(session)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            self._handle_subscription_updated(subscription)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self._handle_subscription_deleted(subscription)
        
        return {"status": "success"}

    def _handle_checkout_completed(self, session):
        """
        Fulfill the purchase...
        """
        client_reference_id = session.get('client_reference_id') # If we used it
        stripe_customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Metadata is most reliable for user_id
        user_id = session.get('metadata', {}).get('user_id')
        
        if not user_id and stripe_customer_id:
             # Try to find by customer_id
             sub = self.db.query(UserSubscription).filter(UserSubscription.stripe_customer_id == stripe_customer_id).first()
             if sub:
                 # Update status
                 sub.status = 'active'
                 sub.stripe_subscription_id = subscription_id
                 self.db.commit()
                 logger.info(f"Updated subscription for customer {stripe_customer_id} to ACTIVE")
                 return

        if user_id:
            sub = self.db.query(UserSubscription).filter(UserSubscription.user_id == int(user_id)).first()
            if sub:
                sub.status = 'active'
                sub.stripe_customer_id = stripe_customer_id
                sub.stripe_subscription_id = subscription_id
                self.db.commit()
                logger.info(f"Updated subscription for user {user_id} to ACTIVE")

    def _handle_subscription_updated(self, stripe_sub):
        """
        Sync status (active, past_due, canceled)
        """
        stripe_sub_id = stripe_sub['id']
        status = stripe_sub['status']
        
        sub = self.db.query(UserSubscription).filter(UserSubscription.stripe_subscription_id == stripe_sub_id).first()
        if sub:
            sub.status = status
            self.db.commit()
            logger.info(f"Synced subscription {stripe_sub_id} status to {status}")

    def _handle_subscription_deleted(self, stripe_sub):
        """
        Handle cancellation
        """
        stripe_sub_id = stripe_sub['id']
        sub = self.db.query(UserSubscription).filter(UserSubscription.stripe_subscription_id == stripe_sub_id).first()
        if sub:
            sub.status = 'canceled'
            self.db.commit()
            logger.info(f"Subscription {stripe_sub_id} marked as CANCELED")