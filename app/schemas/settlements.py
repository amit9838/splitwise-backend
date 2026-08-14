import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SettlementCreate(BaseModel):
    group_id: uuid.UUID
    paid_to: uuid.UUID
    amount: Decimal
    payment_method: str = "cash"
    note: Optional[str] = None


class SettlementResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    paid_by: uuid.UUID
    paid_to: uuid.UUID
    amount: Decimal
    payment_method: str
    note: Optional[str] = None
    settled_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}