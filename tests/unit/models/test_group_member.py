import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="owner@example.com", hashed_password="h")
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def member_user(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="member@example.com", hashed_password="h")
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def group(db_session: AsyncSession, owner: User) -> Group:
    g = Group(id=uuid.uuid4(), name="Trip", created_by=owner.id)
    db_session.add(g)
    await db_session.flush()
    await db_session.refresh(g)
    return g


class TestGroupMemberCreate:
    @pytest.mark.asyncio
    async def test_create_member(
        self, db_session: AsyncSession, group: Group, member_user: User
    ):
        member = GroupMember(group_id=group.id, user_id=member_user.id)
        db_session.add(member)
        await db_session.flush()
        await db_session.refresh(member)

        assert member.id is not None
        assert isinstance(member.id, uuid.UUID)
        assert member.group_id == group.id
        assert member.user_id == member_user.id
        assert member.joined_at is not None
        assert member.is_active is True

    @pytest.mark.asyncio
    async def test_unique_group_member_constraint(
        self, db_session: AsyncSession, group: Group, member_user: User
    ):
        m1 = GroupMember(group_id=group.id, user_id=member_user.id)
        m2 = GroupMember(group_id=group.id, user_id=member_user.id)

        db_session.add(m1)
        await db_session.flush()

        db_session.add(m2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestGroupMemberDelete:
    @pytest_asyncio.fixture
    async def member(
        self, db_session: AsyncSession, group: Group, member_user: User
    ) -> GroupMember:
        m = GroupMember(
            id=uuid.uuid4(), group_id=group.id, user_id=member_user.id
        )
        db_session.add(m)
        await db_session.flush()
        await db_session.refresh(m)
        return m

    @pytest.mark.asyncio
    async def test_delete_member(
        self, db_session: AsyncSession, member: GroupMember
    ):
        await db_session.delete(member)
        await db_session.flush()

        result = await db_session.execute(
            select(GroupMember).where(GroupMember.id == member.id)
        )
        assert result.scalar_one_or_none() is None