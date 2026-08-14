import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseSplitCreate(BaseModel):
    user_id: uuid.UUID
    amount: Optional[Decimal] = None
    percentage: Optional[float] = None
    shares: Optional[int] = None


class ExpenseCreate(BaseModel):
    group_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    description: str
    currency: str = "INR"
    split_type: str = "EQUAL"  # EQUAL, EXACT, PERCENTAGE, SHARES
    expense_date: datetime
    splits: list[ExpenseSplitCreate] = []


class ExpenseSplitResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    percentage: Optional[float] = None
    shares: Optional[int] = None

    model_config = {"from_attributes": True}


class ExpenseUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    currency: Optional[str] = None
    split_type: Optional[str] = None
    expense_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    paid_by: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    description: str
    currency: str
    split_type: str
    expense_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    splits: list[ExpenseSplitResponse] = []

    model_config = {"from_attributes": True}