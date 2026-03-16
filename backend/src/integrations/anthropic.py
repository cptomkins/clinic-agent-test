# backend/src/integrations/anthropic.py
# Author: Claude
# Created Date: 2026-03-15
# v0.8.0 — Anthropic API client wrapper for clinic agent
from __future__ import annotations

import anthropic

from core.config import settings


def get_anthropic_client() -> anthropic.Anthropic:
    """Returns a configured synchronous Anthropic client."""
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
