# backend/src/repositories/clinic/clinic_support_tickets.py
# Author: Claude
# Created Date: 2026-03-15
# v0.11.1 — Repository for support ticket tracking
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from db.models.clinic.clinic_support_ticket import ClinicSupportTicket
from repositories.base import BaseRepository


class ClinicSupportTicketRepository(BaseRepository[ClinicSupportTicket]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ClinicSupportTicket)

    def create_ticket(
        self,
        *,
        company_id: int,
        subject: str,
        description: str,
        priority: str = "medium",
        conversation_id: Optional[uuid.UUID] = None,
    ) -> ClinicSupportTicket:
        return self.create({
            "company_id": company_id,
            "conversation_id": conversation_id,
            "subject": subject,
            "description": description,
            "priority": priority,
            "status": "open",
        })

    def list_by_company(self, *, company_id: int) -> List[ClinicSupportTicket]:
        return (
            self.db.query(ClinicSupportTicket)
            .filter(ClinicSupportTicket.company_id == company_id)
            .order_by(ClinicSupportTicket.created_at.desc())
            .all()
        )

    def get_by_id(self, *, ticket_id: uuid.UUID) -> Optional[ClinicSupportTicket]:
        return self.get(ticket_id)

    def update_status(
        self, *, ticket_id: uuid.UUID, status: str
    ) -> Optional[ClinicSupportTicket]:
        ticket = self.get(ticket_id)
        if not ticket:
            return None
        update_data = {"status": status}
        if status == "resolved":
            update_data["resolved_at"] = datetime.now(timezone.utc)
        return self.update(ticket, update_data)
    