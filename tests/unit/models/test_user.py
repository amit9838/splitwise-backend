import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from passlib.hash import pbkdf2_sha256
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUserCreate:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        user = User(
            email="test@example.com",
            hashed_password=pbkdf2_sha256.hash("securepassword"),
            full_name="Test User",
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_user_with_defaults(self, db_session: AsyncSession):
        user = User(
            email="minimal@example.com",
            hashed_password=pbkdf2_sha256.hash("pw"),
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        assert user.full_name is None
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_unique_email_constraint(self, db_session: AsyncSession):
        user1 = User(email="dup@example.com", hashed_password=pbkdf2_sha256.hash("pw"))
        user2 = User(
            email="dup@example.com", hashed_password=pbkdf2_sha256.hash("pw2")
        )
        db_session.add(user1)
        await db_session.flush()

        db_session.add(user2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestUserUpdate:
    @pytest_asyncio.fixture
    async def user(self, db_session: AsyncSession) -> User:
        u = User(
            id=uuid.uuid4(),
            email="update@example.com",
            hashed_password="hashed",
            full_name="Original",
        )
        db_session.add(u)
        await db_session.flush()
        await db_session.refresh(u)
        return u

    @pytest.mark.asyncio
    async def test_update_full_name(self, db_session: AsyncSession, user: User):
        user.full_name = "Updated Name"
        await db_session.flush()
        await db_session.refresh(user)

        assert user.full_name == "Updated Name"
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_deactivate_user(self, db_session: AsyncSession, user: User):
        user.is_active = False
        await db_session.flush()
        await db_session.refresh(user)

        assert user.is_active is False


class TestUserDelete:
    @pytest_asyncio.fixture
    async def user(self, db_session: AsyncSession) -> User:
        u = User(
            id=uuid.uuid4(),
            email="delete@example.com",
            hashed_password="hashed",
        )
        db_session.add(u)
        await db_session.flush()
        await db_session.refresh(u)
        return u

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession, user: User):
        await db_session.delete(user)
        await db_session.flush()

        result = await db_session.execute(select(User).where(User.id == user.id))
        assert result.scalar_one_or_none() is None