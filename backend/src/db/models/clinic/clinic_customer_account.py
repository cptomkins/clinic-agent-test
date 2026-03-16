# backend/src/db/models/clinic/clinic_customer_account.py
# Author: Claude
# Created Date: 2026-03-15
# v0.11.0 — Mock customer account for product support agent
from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class ClinicCustomerAccount(Base):
    __tablename__ = "clinic_customer_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    clinic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # free, standard, pro
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, annual
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False)
    features_enabled: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    