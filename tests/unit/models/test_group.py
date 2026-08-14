import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email="group-owner@example.com",
        hashed_password="hashed",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


class TestGroupCreate:
    @pytest.mark.asyncio
    async def test_create_group(self, db_session: AsyncSession, user: User):
        group = Group(name="Goa Trip", created_by=user.id)
        db_session.add(group)
        await db_session.flush()
        await db_session.refresh(group)

        assert group.id is not None
        assert isinstance(group.id, uuid.UUID)
        assert group.name == "Goa Trip"
        assert group.created_by == user.id
        assert group.simplify_debts is True
        assert group.is_active is True
        assert group.created_at is not None

    @pytest.mark.asyncio
    async def test_create_group_with_explicit_values(
        self, db_session: AsyncSession, user: User
    ):
        group = Group(
            name="Roommates",
            created_by=user.id,
            simplify_debts=False,
        )
        db_session.add(group)
        await db_session.flush()
        await db_session.refresh(group)

        assert group.simplify_debts is False


class TestGroupUpdate:
    @pytest_asyncio.fixture
    async def group(self, db_session: AsyncSession, user: User) -> Group:
        g = Group(id=uuid.uuid4(), name="Original", created_by=user.id)
        db_session.add(g)
        await db_session.flush()
        await db_session.refresh(g)
        return g

    @pytest.mark.asyncio
    async def test_update_name(self, db_session: AsyncSession, group: Group):
        group.name = "Updated Group"
        await db_session.flush()
        await db_session.refresh(group)

        assert group.name == "Updated Group"

    @pytest.mark.asyncio
    async def test_deactivate(self, db_session: AsyncSession, group: Group):
        group.is_active = False
        await db_session.flush()
        await db_session.refresh(group)

        assert group.is_active is False


class TestGroupDelete:
    @pytest_asyncio.fixture
    async def group(self, db_session: AsyncSession, user: User) -> Group:
        g = Group(id=uuid.uuid4(), name="ToDelete", created_by=user.id)
        db_session.add(g)
        await db_session.flush()
        await db_session.refresh(g)
        return g

    @pytest.mark.asyncio
    async def test_delete_group(self, db_session: AsyncSession, group: Group):
        await db_session.delete(group)
        await db_session.flush()

        result = await db_session.execute(select(Group).where(Group.id == group.id))
        assert result.scalar_one_or_none() is None