# backend/src/repositories/clinic/clinic_conversations.py
# Author: Claude
# Created Date: 2026-03-15
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from db.models.clinic.clinic_conversation import ClinicConversation
from db.models.clinic.clinic_message import ClinicMessage
from repositories.base import BaseRepository


class ClinicConversationRepository(BaseRepository[ClinicConversation]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ClinicConversation)

    def create_conversation(
        self, *, user_id: uuid.UUID, company_id: int
    ) -> ClinicConversation:
        return self.create({"user_id": user_id, "company_id": company_id})

    def get_active_for_user(self, *, user_id: uuid.UUID) -> Optional[ClinicConversation]:
        return (
            self.db.query(ClinicConversation)
            .filter(ClinicConversation.user_id == user_id)
            .order_by(ClinicConversation.created_at.desc())
            .first()
        )

    def list_for_user(self, *, user_id: uuid.UUID) -> List[ClinicConversation]:
        return (
            self.db.query(ClinicConversation)
            .filter(ClinicConversation.user_id == user_id)
            .order_by(ClinicConversation.created_at.desc())
            .all()
        )

    def add_message(
        self,
        *,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ClinicMessage:
        msg = ClinicMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata,
        )
        self.db.add(msg)
        self.db.flush()
        return msg

    def get_messages(self, *, conversation_id: uuid.UUID) -> List[ClinicMessage]:
        return (
            self.db.query(ClinicMessage)
            .filter(ClinicMessage.conversation_id == conversation_id)
            .order_by(ClinicMessage.created_at.asc())
            .all()
        )
