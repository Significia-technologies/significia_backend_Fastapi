"""
Billing Routes — Super Admin Dashboard
───────────────────────────────────────
These endpoints are restricted to Super Admins (Significia staff).
The DomainGuardMiddleware ensures they can only be accessed from app.significia.com.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_super_admin
from app.services.billing_service import BillingService
from app.models.user import User

router = APIRouter()


@router.get("/overview")
def billing_overview(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin),
):
    """
    Billing overview for all tenants.
    Shows plan, client count, bridge status, latest invoice status.
    """
    return BillingService.get_billing_overview(db)


@router.get("/tenant/{tenant_id}/usage")
def tenant_usage(
    tenant_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin),
):
    """Get usage history for a specific tenant."""
    return BillingService.get_tenant_usage_history(db, tenant_id, days)


@router.post("/tenant/{tenant_id}/plan")
def update_plan(
    tenant_id: uuid.UUID,
    plan: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin),
):
    """Update a tenant's billing plan."""
    new_plan = plan.get("plan")
    if not new_plan:
        raise HTTPException(400, "Plan name is required")
    return BillingService.update_tenant_plan(db, tenant_id, new_plan)


@router.get("/stats")
def platform_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin),
):
    """
    Platform-wide statistics.
    Total tenants, active bridges, total clients, revenue by plan.
    """
    return BillingService.get_platform_stats(db)
