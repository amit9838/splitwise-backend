import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.settlements import SettlementCreate, SettlementResponse

router = APIRouter(prefix="/api/settlements", tags=["settlements"])


@router.get("/group/{group_id}", response_model=list[SettlementResponse])
async def list_settlements(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Settlement).where(Settlement.group_id == group_id).order_by(Settlement.settled_at.desc())
    )
    settlements = result.scalars().all()
    return settlements


@router.post("/", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def record_settlement(
    data: SettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate group exists
    group_result = await db.execute(select(Group).where(Group.id == data.group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Validate paid_to user exists and is a group member
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == data.group_id,
            GroupMember.user_id == data.paid_to,
            GroupMember.is_active == True,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Recipient is not a member of this group")

    # Cannot pay yourself
    if data.paid_to == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot settle with yourself")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Settlement amount must be positive")

    settlement = Settlement(
        group_id=data.group_id,
        paid_by=current_user.id,
        paid_to=data.paid_to,
        amount=data.amount,
        payment_method=data.payment_method,
        note=data.note,
    )
    db.add(settlement)
    await db.flush()
    await db.refresh(settlement)
    return settlement


@router.delete("/{settlement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_settlement(
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Settlement).where(Settlement.id == settlement_id)
    )
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    if settlement.paid_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the payer can delete a settlement")

    await db.delete(settlement)
    await db.flush()
    return JSONResponse(status_code=200, content="Settlement deleted successfully!")