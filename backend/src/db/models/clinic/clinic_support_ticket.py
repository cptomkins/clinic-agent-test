# backend/src/db/models/clinic/clinic_support_ticket.py
# Author: Claude
# Created Date: 2026-03-15
# v0.11.0 — Support ticket tracking for product support agent
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class ClinicSupportTicket(Base):
    __tablename__ = "clinic_support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinic_conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open, in_progress, resolved
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_clinic_support_tickets_company_id", "company_id"),
    )
