import stripe
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrgPlan
from app.api.deps import get_current_user, get_current_org, require_role

router = APIRouter(prefix="/billing", tags=["Billing"])

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICES = {
    "starter": settings.STRIPE_PRICE_STARTER or "price_starter_monthly",
    "professional": settings.STRIPE_PRICE_PROFESSIONAL or "price_professional_monthly",
    "enterprise": None,
}

PLAN_LIMITS = {
    "starter": 10,
    "professional": 50,
    "enterprise": 999999,
}


class CheckoutRequest(BaseModel):
    plan: str = "professional"


@router.get("/current-plan")
async def get_current_plan(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    return {
        "plan": org.plan.value,
        "max_verifications": org.max_verifications_per_month,
        "stripe_customer_id": org.stripe_customer_id,
        "stripe_subscription_id": org.stripe_subscription_id,
    }


@router.post("/create-checkout-session")
async def create_checkout_session(
    data: CheckoutRequest,
    user: User = Depends(require_role(["owner", "admin"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    price_id = PLAN_PRICES.get(data.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Contact sales for Enterprise plan")

    try:
        # Create or get Stripe customer
        if not org.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=org.name,
                metadata={"org_id": str(org.id)},
            )
            org.stripe_customer_id = customer.id
            await db.flush()

        session = stripe.checkout.Session.create(
            customer=org.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/dashboard/billing?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/billing?canceled=true",
            metadata={"org_id": str(org.id), "plan": data.plan},
        )

        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        org_id = session.get("metadata", {}).get("org_id")
        plan = session.get("metadata", {}).get("plan", "professional")

        if org_id:
            result = await db.execute(select(Organization).where(Organization.id == org_id))
            org = result.scalar_one_or_none()
            if org:
                org.plan = OrgPlan(plan)
                org.stripe_subscription_id = session.get("subscription")
                org.max_verifications_per_month = PLAN_LIMITS.get(plan, 10)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        result = await db.execute(
            select(Organization).where(Organization.stripe_customer_id == customer_id)
        )
        org = result.scalar_one_or_none()
        if org:
            org.plan = OrgPlan.starter
            org.stripe_subscription_id = None
            org.max_verifications_per_month = 10

    await db.commit()
    return {"status": "ok"}


@router.post("/portal-session")
async def create_portal_session(
    user: User = Depends(require_role(["owner", "admin"])),
    org: Organization = Depends(get_current_org),
):
    if not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard/billing",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
