# backend/src/services/solutions/clinic_agent/tools.py
# Author: Claude
# Created Date: 2026-03-15
# Updated: 2026-03-15 — v0.12.1: new tool definitions for product support agent

CLINIC_TOOLS = [
    {
        "name": "search_help_articles",
        "description": (
            "Search the ClinicSoft knowledge base for help articles about software features, "
            "how-to guides, and troubleshooting steps. Use this when the user asks how to do "
            "something in the software, reports an issue, or needs step-by-step guidance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query describing what the user needs help with.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_account_info",
        "description": (
            "Retrieve the customer's current account details including clinic name, plan, "
            "seat count, billing cycle, next billing date, and enabled features. Use this "
            "when the user asks about their plan, account, or what features they have access to."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_billing_history",
        "description": (
            "Retrieve the customer's billing information including current plan pricing, "
            "seat count, billing cycle, and next billing date. Use this when the user asks "
            "about charges, invoices, or payment timing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_upgrade_options",
        "description": (
            "Look up available plan upgrade options and pricing for the customer's current plan. "
            "Returns a comparison of what the next plan offers versus their current plan. "
            "Use this when the user asks about upgrading, plan differences, or pricing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_support_tickets",
        "description": (
            "List the customer's past and current support tickets including subject, status, "
            "priority, and dates. Use this when the user asks about previous support requests "
            "or wants to check on an existing ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_support_ticket",
        "description": (
            "Create a new support ticket and notify the support team via email. Use this when "
            "the user explicitly asks to submit a support request, or when you've been unable "
            "to resolve their issue after multiple attempts and they agree to escalate. Always "
            "confirm with the user before creating a ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Brief summary of the issue (1 sentence).",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed context summary including what the user tried, what went wrong, and any relevant account details.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Ticket priority: low for general questions, medium for functionality issues, high for blocking/urgent issues.",
                },
            },
            "required": ["subject", "description", "priority"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Explicitly hand off the conversation to a human support agent. Creates a support "
            "ticket with full conversation context and notifies the support team. Use this when "
            "the user directly asks to speak with a person, or when the issue requires human "
            "judgment (e.g. billing disputes, account access problems). Always confirm with the "
            "user before escalating."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Brief summary of why the user needs human support.",
                },
                "context_summary": {
                    "type": "string",
                    "description": "Summary of the conversation so far — what the user asked, what was tried, and why escalation is needed.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Urgency level for the support team.",
                },
            },
            "required": ["subject", "context_summary", "priority"],
        },
    },
]
