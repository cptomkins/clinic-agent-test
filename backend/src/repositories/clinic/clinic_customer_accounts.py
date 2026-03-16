# backend/src/repositories/clinic/clinic_customer_accounts.py
# Author: Claude
# Created Date: 2026-03-15
# v0.11.1 — Repository for mock customer accounts
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from db.models.clinic.clinic_customer_account import ClinicCustomerAccount
from repositories.base import BaseRepository


class ClinicCustomerAccountRepository(BaseRepository[ClinicCustomerAccount]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ClinicCustomerAccount)

    def get_by_company(self, *, company_id: int) -> Optional[ClinicCustomerAccount]:
        return (
            self.db.query(ClinicCustomerAccount)
            .filter(ClinicCustomerAccount.company_id == company_id)
            .first()
        )

    def create_account(
        self,
        *,
        company_id: int,
        clinic_name: str,
        plan: str,
        seats: int,
        billing_cycle: str,
        next_billing_date,
        features_enabled: Optional[dict] = None,
    ) -> ClinicCustomerAccount:
        return self.create({
            "company_id": company_id,
            "clinic_name": clinic_name,
            "plan": plan,
            "seats": seats,
            "billing_cycle": billing_cycle,
            "next_billing_date": next_billing_date,
            "features_enabled": features_enabled,
        })
    