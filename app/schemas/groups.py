import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    member_ids: list[uuid.UUID] = []
    simplify_debts: bool = True


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    simplify_debts: Optional[bool] = None
    is_active: Optional[bool] = None


class MemberInfo(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user: Optional[MemberInfo] = None
    joined_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    simplify_debts: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    members: list[GroupMemberResponse] = []

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID