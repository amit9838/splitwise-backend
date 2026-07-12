import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class TestCategoryCreate:
    @pytest.mark.asyncio
    async def test_create_category(self, db_session: AsyncSession):
        category = Category(name="Groceries")
        db_session.add(category)
        await db_session.flush()
        await db_session.refresh(category)

        assert category.id is not None
        assert isinstance(category.id, uuid.UUID)
        assert category.name == "Groceries"
        assert category.is_active is True
        assert category.created_at is not None

    @pytest.mark.asyncio
    async def test_unique_name_constraint(self, db_session: AsyncSession):
        cat1 = Category(name="Unique")
        cat2 = Category(name="Unique")
        db_session.add(cat1)
        await db_session.flush()

        db_session.add(cat2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestCategoryUpdate:
    @pytest_asyncio.fixture
    async def category(self, db_session: AsyncSession) -> Category:
        cat = Category(id=uuid.uuid4(), name="Utilities")
        db_session.add(cat)
        await db_session.flush()
        await db_session.refresh(cat)
        return cat

    @pytest.mark.asyncio
    async def test_update_name(self, db_session: AsyncSession, category: Category):
        category.name = "Updated Category"
        await db_session.flush()
        await db_session.refresh(category)

        assert category.name == "Updated Category"

    @pytest.mark.asyncio
    async def test_deactivate(self, db_session: AsyncSession, category: Category):
        category.is_active = False
        await db_session.flush()
        await db_session.refresh(category)

        assert category.is_active is False


class TestCategoryDelete:
    @pytest_asyncio.fixture
    async def category(self, db_session: AsyncSession) -> Category:
        cat = Category(id=uuid.uuid4(), name="ToDelete")
        db_session.add(cat)
        await db_session.flush()
        await db_session.refresh(cat)
        return cat

    @pytest.mark.asyncio
    async def test_delete_category(self, db_session: AsyncSession, category: Category):
        await db_session.delete(category)
        await db_session.flush()

        result = await db_session.execute(
            select(Category).where(Category.id == category.id)
        )
        assert result.scalar_one_or_none() is None