"""
Billing Service
───────────────
Handles billing operations for the Super Admin dashboard.
Provides billing overview, usage history, and plan management.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.tenant import Tenant
from app.models.token_usage import TokenUsage
from app.models.billing import BillingRecord, PLAN_LIMITS


class BillingService:

    @staticmethod
    def get_billing_overview(db: Session) -> list:
        """
        Get billing overview for all tenants.
        Used by Super Admin dashboard.
        """
        tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()

        overview = []
        for t in tenants:
            plan_info = PLAN_LIMITS.get(t.billing_plan, PLAN_LIMITS["free"])

            # Get latest billing record
            latest_bill = db.query(BillingRecord).filter(
                BillingRecord.tenant_id == t.id
            ).order_by(BillingRecord.created_at.desc()).first()

            overview.append({
                "tenant_id": str(t.id),
                "tenant_name": t.name,
                "billing_plan": t.billing_plan,
                "max_client_permit": t.max_client_permit,
                "current_client_count": t.current_client_count,
                "plan_price_annual": plan_info["price_annual"],
                "bridge_status": t.bridge_status,
                "custom_domain": t.custom_domain,
                "subdomain": t.subdomain,
                "latest_invoice_status": latest_bill.status if latest_bill else "NONE",
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })

        return overview

    @staticmethod
    def get_tenant_usage_history(
        db: Session,
        tenant_id: uuid.UUID,
        days: int = 30,
    ) -> list:
        """Get usage history for a specific tenant over the last N days."""
        since = datetime.utcnow() - timedelta(days=days)

        records = db.query(TokenUsage).filter(
            TokenUsage.tenant_id == tenant_id,
            TokenUsage.recorded_at >= since,
        ).order_by(TokenUsage.recorded_at.desc()).all()

        return [
            {
                "metric": r.metric,
                "value": r.value,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in records
        ]

    @staticmethod
    def update_tenant_plan(
        db: Session,
        tenant_id: uuid.UUID,
        new_plan: str,
    ) -> dict:
        """Update a tenant's billing plan."""
        if new_plan not in PLAN_LIMITS:
            raise HTTPException(400, f"Invalid plan: {new_plan}")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(404, "Tenant not found")

        old_plan = tenant.billing_plan
        plan_info = PLAN_LIMITS[new_plan]

        tenant.billing_plan = new_plan
        tenant.max_client_permit = plan_info["max_clients"]

        # Create billing record for the plan change
        bill = BillingRecord(
            tenant_id=tenant.id,
            plan=new_plan,
            billing_period_start=date.today(),
            billing_period_end=date.today() + timedelta(days=365),
            amount=plan_info["price_annual"],
            client_count_at_billing=tenant.current_client_count,
            status="PENDING",
            notes=f"Plan changed from {old_plan} to {new_plan}",
        )
        db.add(bill)
        db.commit()

        return {
            "tenant_id": str(tenant.id),
            "old_plan": old_plan,
            "new_plan": new_plan,
            "max_client_permit": plan_info["max_clients"],
            "annual_price": plan_info["price_annual"],
        }

    @staticmethod
    def get_platform_stats(db: Session) -> dict:
        """Get platform-wide stats for the Super Admin dashboard."""
        total_tenants = db.query(Tenant).count()
        active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
        active_bridges = db.query(Tenant).filter(Tenant.bridge_status == "ACTIVE").count()
        total_clients = db.query(func.sum(Tenant.current_client_count)).scalar() or 0

        # Revenue by plan
        plan_distribution = {}
        for plan_name, plan_info in PLAN_LIMITS.items():
            count = db.query(Tenant).filter(Tenant.billing_plan == plan_name).count()
            plan_distribution[plan_name] = {
                "count": count,
                "revenue": count * plan_info["price_annual"],
            }

        return {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "active_bridges": active_bridges,
            "total_clients_across_all_ias": total_clients,
            "plan_distribution": plan_distribution,
        }
