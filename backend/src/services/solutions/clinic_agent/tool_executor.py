# backend/src/services/solutions/clinic_agent/tool_executor.py
# Author: Claude
# Created Date: 2026-03-15
# Updated: 2026-03-15 — v0.12.2: implement dispatch for product support tools
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from repositories.clinic.clinic_customer_accounts import ClinicCustomerAccountRepository
from repositories.clinic.clinic_support_tickets import ClinicSupportTicketRepository
from services.solutions.clinic_agent.kb_loader import search_kb
from integrations.postmark import send_sync_postmark


# Plan pricing reference (mirrors plans-and-upgrading.md)
PLAN_PRICING = {
    "free": {"price": 0, "label": "Free", "max_seats": 1},
    "standard": {"price": 49, "label": "Standard", "max_seats": 10},
    "pro": {"price": 89, "label": "Pro", "max_seats": None},
}

PLAN_ORDER = ["free", "standard", "pro"]

SUPPORT_EMAIL = "info@harborautomation.com"


def execute_tool(
    db: Session,
    company_id: int,
    user_email: str,
    tool_name: str,
    tool_input: dict,
    conversation_id: str | None = None,
) -> str:
    """Dispatch a tool call to the appropriate handler and return JSON result."""
    handlers = {
        "search_help_articles": _search_help_articles,
        "get_account_info": _get_account_info,
        "get_billing_history": _get_billing_history,
        "check_upgrade_options": _check_upgrade_options,
        "list_support_tickets": _list_support_tickets,
        "create_support_ticket": _create_support_ticket,
        "escalate_to_human": _escalate_to_human,
    }

    handler = handlers.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = handler(
            db=db,
            company_id=company_id,
            user_email=user_email,
            tool_input=tool_input,
            conversation_id=conversation_id,
        )
        result_json = json.dumps(result, default=str)
        return result_json
    except Exception as e:
        return json.dumps({"error": f"Tool failed: {str(e)}"})


# ── Tool handlers ────────────────────────────────────────────


def _search_help_articles(
    db: Session, company_id: int, user_email: str, tool_input: dict, **kwargs
) -> dict:
    query = tool_input.get("query", "")
    if not query:
        return {"error": "Query is required."}

    results = search_kb(query, max_results=3)
    if not results:
        return {
            "results": [],
            "message": "No matching help articles found. Consider rephrasing or escalating to support.",
        }

    return {
        "results": [
            {
                "heading": r["heading"],
                "source": r["source_file"].replace(".md", "").replace("-", " ").title(),
                "content": r["content"],
            }
            for r in results
        ],
    }


def _get_account_info(
    db: Session, company_id: int, user_email: str, tool_input: dict, **kwargs
) -> dict:
    repo = ClinicCustomerAccountRepository(db)
    account = repo.get_by_company(company_id=company_id)
    if not account:
        return {"error": "No customer account found for this company."}

    return {
        "clinic_name": account.clinic_name,
        "plan": account.plan,
        "seats": account.seats,
        "billing_cycle": account.billing_cycle,
        "next_billing_date": account.next_billing_date.isoformat()
            if account.next_billing_date else None,
        "features_enabled": account.features_enabled or [],
    }


def _get_billing_history(
    db: Session, company_id: int, user_email: str, tool_input: dict, **kwargs
) -> dict:
    repo = ClinicCustomerAccountRepository(db)
    account = repo.get_by_company(company_id=company_id)
    if not account:
        return {"error": "No customer account found for this company."}

    plan_info = PLAN_PRICING.get(account.plan, {})
    per_seat = plan_info.get("price", 0)
    total = per_seat * account.seats

    return {
        "plan": account.plan,
        "per_seat_price": per_seat,
        "seats": account.seats,
        "monthly_total": total,
        "billing_cycle": account.billing_cycle,
        "next_billing_date": account.next_billing_date.isoformat()
            if account.next_billing_date else None,
        "note": "For detailed invoice history, go to Settings > Billing & Plan > Invoice History.",
    }


def _check_upgrade_options(
    db: Session, company_id: int, user_email: str, tool_input: dict, **kwargs
) -> dict:
    repo = ClinicCustomerAccountRepository(db)
    account = repo.get_by_company(company_id=company_id)
    if not account:
        return {"error": "No customer account found for this company."}

    current_plan = account.plan
    current_idx = PLAN_ORDER.index(current_plan) if current_plan in PLAN_ORDER else 0

    if current_idx >= len(PLAN_ORDER) - 1:
        return {
            "current_plan": current_plan,
            "message": "You're already on the highest plan (Pro). No upgrades available.",
        }

    # Also pull KB content for plan details
    kb_results = search_kb("plan comparison upgrade pricing", max_results=1)
    plan_details = kb_results[0]["content"] if kb_results else None

    upgrade_options = []
    for plan_slug in PLAN_ORDER[current_idx + 1:]:
        info = PLAN_PRICING[plan_slug]
        upgrade_options.append({
            "plan": plan_slug,
            "label": info["label"],
            "per_seat_price": info["price"],
            "max_seats": info["max_seats"],
        })

    return {
        "current_plan": current_plan,
        "current_price": PLAN_PRICING.get(current_plan, {}).get("price", 0),
        "upgrade_options": upgrade_options,
        "plan_details": plan_details,
        "upgrade_instructions": "Go to Settings > Billing & Plan > Change Plan to upgrade. Changes take effect immediately with prorated billing.",
    }


def _list_support_tickets(
    db: Session, company_id: int, user_email: str, tool_input: dict, **kwargs
) -> dict:
    repo = ClinicSupportTicketRepository(db)
    tickets = repo.list_by_company(company_id=company_id)

    return {
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in tickets
        ],
    }


def _create_support_ticket(
    db: Session, company_id: int, user_email: str, tool_input: dict, conversation_id: str | None = None, **kwargs
) -> dict:
    subject = tool_input.get("subject", "Support request")
    description = tool_input.get("description", "")
    priority = tool_input.get("priority", "medium")

    repo = ClinicSupportTicketRepository(db)
    ticket = repo.create_ticket(
        company_id=company_id,
        subject=subject,
        description=description,
        priority=priority,
        conversation_id=conversation_id,
    )
    db.flush()

    # Send notification email to support team
    _send_support_email(
        subject=f"[{priority.upper()}] New support ticket: {subject}",
        body=f"Ticket ID: {ticket.id}\nFrom: {user_email}\nPriority: {priority}\n\n{description}",
        user_email=user_email,
    )

    return {
        "ticket_id": str(ticket.id),
        "status": "open",
        "message": f"Support ticket created successfully. A team member will review your request.",
    }


def _escalate_to_human(
    db: Session, company_id: int, user_email: str, tool_input: dict, conversation_id: str | None = None, **kwargs
) -> dict:
    subject = tool_input.get("subject", "Escalation request")
    context_summary = tool_input.get("context_summary", "")
    priority = tool_input.get("priority", "medium")

    repo = ClinicSupportTicketRepository(db)
    ticket = repo.create_ticket(
        company_id=company_id,
        subject=f"[ESCALATION] {subject}",
        description=context_summary,
        priority=priority,
        conversation_id=conversation_id,
    )
    db.flush()

    _send_support_email(
        subject=f"[ESCALATION - {priority.upper()}] {subject}",
        body=f"Ticket ID: {ticket.id}\nFrom: {user_email}\nPriority: {priority}\n\nConversation context:\n{context_summary}",
        user_email=user_email,
    )

    return {
        "ticket_id": str(ticket.id),
        "status": "open",
        "message": "Your conversation has been escalated to our support team. Someone will follow up with you shortly.",
    }


# ── Helpers ──────────────────────────────────────────────────


def _send_support_email(subject: str, body: str, user_email: str) -> None:
    """Send a support notification email via Postmark. Failures are logged, not raised."""
    try:
        html = body.replace("\n", "<br>")
        html = f"<p>{html}</p><hr><p>Reply-to: {user_email}</p>"
        send_sync_postmark(
            to=SUPPORT_EMAIL,
            subject=subject,
            html=html,
            cc=user_email,
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to send email: {str(e)}"})
        