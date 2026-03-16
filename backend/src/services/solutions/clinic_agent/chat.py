# backend/src/services/solutions/clinic_agent/chat.py
# Author: Claude
# Created Date: 2026-03-15
# Updated: 2026-03-15 — v0.12.4: inject account data, pass conversation_id to tools
# Updated: 2026-03-16 — v0.17: synthetic prompt for auto-first-message greet
from __future__ import annotations

import json
import logging
import uuid
from datetime import date
from typing import Generator

from sqlalchemy.orm import Session

from integrations.anthropic import get_anthropic_client
from repositories.clinic.clinic_conversations import ClinicConversationRepository
from repositories.clinic.clinic_customer_accounts import ClinicCustomerAccountRepository
from repositories.solution_templates import SolutionTemplateRepository
from repositories.solutions import SolutionRepository
from services.solutions.clinic_agent.tools import CLINIC_TOOLS
from services.solutions.clinic_agent.tool_executor import execute_tool

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 5


# ── System prompt ────────────────────────────────────────────


def build_system_prompt(db: Session, company_id: int, user_tz: str = "UTC") -> str:
    """Load the system prompt template and inject context, date, and timezone."""
    solution_repo = SolutionRepository(db)
    solution = solution_repo.get_by_slug("clinic-agent")
    if not solution:
        raise RuntimeError("clinic-agent solution not found in DB")

    template_repo = SolutionTemplateRepository(db)
    template = template_repo.get_latest_default(
        solution_id=solution.id,
        type="system_prompt",
        name="clinic-agent-system",
    )
    if not template:
        raise RuntimeError("clinic-agent system prompt template not found in DB")

    prompt_text = template.content.get("prompt", "")

    # Inject customer account context
    account_repo = ClinicCustomerAccountRepository(db)
    account = account_repo.get_by_company(company_id=company_id)
    if account:
        account_data = (
            f"Clinic: {account.clinic_name}\n"
            f"Plan: {account.plan}\n"
            f"Seats: {account.seats}\n"
            f"Billing cycle: {account.billing_cycle}\n"
            f"Next billing date: {account.next_billing_date}\n"
            f"Features enabled: {', '.join(account.features_enabled) if account.features_enabled else 'default'}"
        )
    else:
        account_data = "(No account data available)"

    prompt = prompt_text.replace("{{account_data}}", account_data)
    prompt = prompt.replace("{{current_date}}", date.today().isoformat())
    prompt = prompt.replace("{{timezone}}", user_tz)
    return prompt


# ── Message building ─────────────────────────────────────────


def _build_messages(db: Session, conversation_id: uuid.UUID) -> list[dict]:
    """Convert conversation history into Anthropic API messages format."""
    repo = ClinicConversationRepository(db)
    db_messages = repo.get_messages(conversation_id=conversation_id)

    messages = []
    for m in db_messages:
        if m.role in ("user", "assistant"):
            # Check if metadata contains structured content (tool calls/results)
            if m.metadata_ and m.metadata_.get("content"):
                messages.append({"role": m.role, "content": m.metadata_["content"]})
            else:
                messages.append({"role": m.role, "content": m.content})

    return messages


# ── Streaming with tool loop ─────────────────────────────────


def stream_ai_response(
    db: Session,
    conversation_id: uuid.UUID,
    company_id: int,
    user_email: str,
    user_tz: str = "UTC",
) -> Generator[str, None, None]:
    """
    Stream Anthropic API response with tool call support.
    Yields text deltas. When the AI calls tools, executes them and
    re-calls the API until we get a final text response.
    """
    system_prompt = build_system_prompt(db, company_id, user_tz)
    messages = _build_messages(db, conversation_id)
    client = get_anthropic_client()

    # v0.17: If no messages exist (auto-greet for first-time user),
    # inject a synthetic user message that prompts the welcome.
    # This message is NOT persisted — it only exists for this API call.
    if not messages:
        messages = [
            {
                "role": "user",
                "content": (
                    "[System: This is a brand-new user opening the chat for the first "
                    "time. Greet them warmly, reference their account details from your "
                    "system prompt (clinic name, plan, seats), and offer to help with "
                    "common tasks: software questions, billing, troubleshooting, or "
                    "upgrading. Keep it concise and friendly.]"
                ),
            }
        ]

    for _round in range(MAX_TOOL_ROUNDS):
        # Collect the full response (we need to inspect stop_reason)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
            tools=CLINIC_TOOLS if CLINIC_TOOLS else None,
        )

        # If pure text response (no tool use), stream it
        if response.stop_reason == "end_turn":
            # Re-call with streaming for the final text response
            stream_kwargs = dict(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=messages,
            )
            if CLINIC_TOOLS:
                stream_kwargs["tools"] = CLINIC_TOOLS

            with client.messages.stream(**stream_kwargs) as stream:
                for text in stream.text_stream:
                    yield text
            return

        # Handle tool use
        if response.stop_reason == "tool_use":
            # Build the assistant message content (may contain text + tool_use blocks)
            assistant_content = []
            for block in response.content:
                if block.type == "text" and block.text:
                    # Yield any text that came before the tool call
                    yield block.text
                    yield "\n\n"
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # Append assistant message with tool calls
            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and build tool results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(
                        db=db,
                        company_id=company_id,
                        user_email=user_email,
                        tool_name=block.name,
                        tool_input=block.input,
                        conversation_id=str(conversation_id),
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            db.flush()
            continue

        # Unexpected stop reason — yield whatever text we got
        for block in response.content:
            if hasattr(block, "text") and block.text:
                yield block.text
        return

    # If we hit the round limit, yield a message
    yield "I've reached the limit for actions in a single response. Please send another message to continue."
    