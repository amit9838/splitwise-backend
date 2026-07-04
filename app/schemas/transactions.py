import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    user_id: uuid.UUID
    category_id: uuid.UUID
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}