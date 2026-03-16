# backend/src/services/solutions/clinic_agent/sample_data.py
# Author: Claude
# Created Date: 2026-03-15
# v0.11.3 — Sample data for product support agent (replaces clinic ops data)
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from repositories.clinic.clinic_customer_accounts import ClinicCustomerAccountRepository
from repositories.clinic.clinic_support_tickets import ClinicSupportTicketRepository


def generate(db: Session, company_id: int) -> None:
    """Generate sample customer account and support ticket history."""
    accounts = ClinicCustomerAccountRepository(db)
    tickets = ClinicSupportTicketRepository(db)

    # Mock customer account
    accounts.create_account(
        company_id=company_id,
        clinic_name="Bright Smile Family Dental",
        plan="standard",
        seats=3,
        billing_cycle="monthly",
        next_billing_date=date.today() + timedelta(days=14),
        features_enabled=[
            "scheduling",
            "patient_records",
            "insurance_claims",
            "appointment_reminders",
            "payment_tracking",
            "basic_reporting",
        ],
    )

    # Past resolved ticket
    resolved = tickets.create_ticket(
        company_id=company_id,
        subject="Cannot export monthly report to PDF",
        description="User reported that clicking Export > PDF on the Reports page "
        "produces a blank file. Issue occurred in Chrome and Firefox. "
        "Resolved by clearing browser cache and updating to latest version.",
        priority="medium",
    )
    tickets.update_status(ticket_id=resolved.id, status="resolved")

    # Open ticket
    tickets.create_ticket(
        company_id=company_id,
        subject="Insurance claim rejected for patient — error code 45",
        description="Claim for patient was rejected by carrier with error code 45 "
        "(invalid subscriber ID). User verified the subscriber ID matches "
        "the insurance card. Awaiting further investigation.",
        priority="high",
    )

    db.flush()
