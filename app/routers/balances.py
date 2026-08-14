import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User
from app.services.balance_calculator import BalanceCalculator

router = APIRouter(prefix="/api/balances", tags=["balances"])


@router.get("/group/{group_id}")
async def get_group_balances(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get raw balances and simplified settlements for a group."""
    # Validate group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Calculate raw balances
    balances = await BalanceCalculator.get_group_balances(group_id, db)

    # Get member info for display
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.is_active == True,
        )
    )
    members = member_result.scalars().all()
    member_map = {}
    for m in members:
        if m.user:
            member_map[str(m.user_id)] = {
                "user_id": str(m.user_id),
                "email": m.user.email,
                "full_name": m.user.full_name,
            }

    # Build balance details
    balance_details = []
    for user_id, amount in balances.items():
        user_info = member_map.get(user_id, {"user_id": user_id, "email": "unknown", "full_name": None})
        balance_details.append({
            "user_id": user_id,
            "email": user_info["email"],
            "full_name": user_info["full_name"],
            "net_balance": float(amount),
            "status": "owed" if amount > 0 else ("owes" if amount < 0 else "settled"),
        })

    # Simplify debts
    settlements = BalanceCalculator.simplify_debts(balances)

    return {
        "group_id": str(group_id),
        "group_name": group.name,
        "balances": balance_details,
        "simplified_settlements": [
            {
                "from_user_id": s["from_user_id"],
                "to_user_id": s["to_user_id"],
                "amount": float(s["amount"]),
            }
            for s in settlements
        ],
        "total_settlements": len(settlements),
    }


@router.get("/me")
async def get_my_balances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all balances across all groups for the current user."""
    # Get user's active group memberships
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.user_id == current_user.id,
            GroupMember.is_active == True,
        )
    )
    memberships = member_result.scalars().all()

    all_balances = []
    total_owed_to_me = 0.0
    total_i_owe = 0.0

    for membership in memberships:
        group_result = await db.execute(
            select(Group).where(Group.id == membership.group_id)
        )
        group = group_result.scalar_one_or_none()
        if not group or not group.is_active:
            continue

        balances = await BalanceCalculator.get_group_balances(group.id, db)
        my_balance = float(balances.get(str(current_user.id), 0))

        if my_balance > 0:
            total_owed_to_me += my_balance
        else:
            total_i_owe += abs(my_balance)

        settlements = BalanceCalculator.simplify_debts(balances)
        my_settlements = [
            s for s in settlements
            if s["from_user_id"] == str(current_user.id) or s["to_user_id"] == str(current_user.id)
        ]

        all_balances.append({
            "group_id": str(group.id),
            "group_name": group.name,
            "my_net_balance": my_balance,
            "my_settlements": [
                {
                    "from_user_id": s["from_user_id"],
                    "to_user_id": s["to_user_id"],
                    "amount": float(s["amount"]),
                }
                for s in my_settlements
            ],
        })

    return {
        "user_id": str(current_user.id),
        "total_owed_to_me": total_owed_to_me,
        "total_i_owe": total_i_owe,
        "net_balance": total_owed_to_me - total_i_owe,
        "groups": all_balances,
    }