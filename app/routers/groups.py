import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User
from app.schemas.groups import (
    AddMemberRequest,
    GroupCreate,
    GroupMemberResponse,
    GroupResponse,
    GroupUpdate,
    MemberInfo,
)

router = APIRouter(prefix="/api/groups", tags=["groups"])


async def _group_to_response(group: Group, db: AsyncSession) -> GroupResponse:
    """Build a GroupResponse with members populated."""
    members_result = await db.execute(
        select(GroupMember)
        .options(selectinload(GroupMember.user))
        .where(GroupMember.group_id == group.id)
    )
    members = members_result.scalars().all()

    member_responses = []
    for m in members:
        member_info = None
        if m.user:
            member_info = MemberInfo(
                id=m.user.id,
                email=m.user.email,
                full_name=m.user.full_name,
            )
        member_responses.append(
            GroupMemberResponse(
                id=m.id,
                user_id=m.user_id,
                user=member_info,
                joined_at=m.joined_at,
                is_active=m.is_active,
            )
        )

    return GroupResponse(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        simplify_debts=group.simplify_debts,
        is_active=group.is_active,
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=member_responses,
    )


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get groups where user is a member
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.user_id == current_user.id,
            GroupMember.is_active == True,
        )
    )
    memberships = member_result.scalars().all()
    group_ids = [m.group_id for m in memberships]

    if not group_ids:
        return []

    result = await db.execute(
        select(Group).where(Group.id.in_(group_ids))
    )
    groups = result.scalars().all()

    responses = []
    for group in groups:
        responses.append(await _group_to_response(group, db))
    return responses


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return await _group_to_response(group, db)


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate member list: no duplicates and creator must not be included
    unique_member_ids = set(data.member_ids)
    if len(unique_member_ids) != len(data.member_ids):
        raise HTTPException(status_code=400, detail="Duplicate member ids provided")

    if current_user.id in unique_member_ids:
        raise HTTPException(
            status_code=400,
            detail="Creator is added automatically and must not be in member_ids",
        )

    # Validate all members exist (if any provided)
    if unique_member_ids:
        result = await db.execute(select(User).where(User.id.in_(unique_member_ids)))
        found_users = result.scalars().all()
        if len(found_users) != len(unique_member_ids):
            raise HTTPException(status_code=404, detail="One or more members not found")

    group = Group(
        name=data.name,
        created_by=current_user.id,
        simplify_debts=data.simplify_debts,
    )
    db.add(group)
    await db.flush()
    await db.refresh(group)

    # Add creator as member
    creator_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
    )
    db.add(creator_member)

    # Add other members
    for member_id in unique_member_ids:
        db.add(GroupMember(group_id=group.id, user_id=member_id))

    await db.flush()

    return await _group_to_response(group, db)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if data.name is not None:
        group.name = data.name
    if data.simplify_debts is not None:
        group.simplify_debts = data.simplify_debts
    if data.is_active is not None:
        group.is_active = data.is_active

    await db.flush()
    await db.refresh(group)
    return await _group_to_response(group, db)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only group creator can delete the group")

    group_name = group.name
    await db.delete(group)
    await db.flush()
    return JSONResponse(status_code=200, content=f"Group '{group_name}' deleted successfully!")


@router.post("/{group_id}/members", response_model=GroupResponse)
async def add_member(
    group_id: uuid.UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == data.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this group")

    member = GroupMember(
        group_id=group_id,
        user_id=data.user_id,
    )
    db.add(member)
    await db.flush()
    return await _group_to_response(group, db)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only group creator can remove members")

    if user_id == group.created_by:
        raise HTTPException(status_code=400, detail="Cannot remove the group creator")

    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in group")

    await db.delete(member)
    await db.flush()
    return JSONResponse(status_code=200, content="Member removed successfully!")
