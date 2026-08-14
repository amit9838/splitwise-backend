import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.models.group import Group
from app.models.user import User


@pytest_asyncio.fixture
async def payer(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="payer@example.com", hashed_password="h")
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def group(db_session: AsyncSession, payer: User) -> Group:
    g = Group(id=uuid.uuid4(), name="Trip", created_by=payer.id)
    db_session.add(g)
    await db_session.flush()
    await db_session.refresh(g)
    return g


@pytest_asyncio.fixture
async def category(db_session: AsyncSession) -> Category:
    c = Category(id=uuid.uuid4(), name="Food")
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    return c


class TestExpenseCreate:
    @pytest.mark.asyncio
    async def test_create_expense(
        self,
        db_session: AsyncSession,
        group: Group,
        payer: User,
        category: Category,
    ):
        expense = Expense(
            group_id=group.id,
            paid_by=payer.id,
            category_id=category.id,
            amount=Decimal("1000.00"),
            description="Dinner",
        )
        db_session.add(expense)
        await db_session.flush()
        await db_session.refresh(expense)

        assert expense.id is not None
        assert isinstance(expense.id, uuid.UUID)
        assert expense.group_id == group.id
        assert expense.paid_by == payer.id
        assert expense.category_id == category.id
        assert expense.amount == Decimal("1000.00")
        assert expense.description == "Dinner"
        assert expense.currency == "INR"
        assert expense.split_type == "EQUAL"
        assert expense.is_active is True
        assert expense.expense_date is not None
        assert expense.created_at is not None

    @pytest.mark.asyncio
    async def test_create_expense_with_explicit_values(
        self,
        db_session: AsyncSession,
        group: Group,
        payer: User,
        category: Category,
    ):
        expense = Expense(
            group_id=group.id,
            paid_by=payer.id,
            category_id=category.id,
            amount=Decimal("500.00"),
            description="Taxi",
            currency="USD",
            split_type="EXACT",
        )
        db_session.add(expense)
        await db_session.flush()
        await db_session.refresh(expense)

        assert expense.currency == "USD"
        assert expense.split_type == "EXACT"


class TestExpenseDelete:
    @pytest_asyncio.fixture
    async def expense(
        self,
        db_session: AsyncSession,
        group: Group,
        payer: User,
        category: Category,
    ) -> Expense:
        e = Expense(
            id=uuid.uuid4(),
            group_id=group.id,
            paid_by=payer.id,
            category_id=category.id,
            amount=Decimal("100.00"),
            description="ToDelete",
        )
        db_session.add(e)
        await db_session.flush()
        await db_session.refresh(e)
        return e

    @pytest.mark.asyncio
    async def test_delete_expense(self, db_session: AsyncSession, expense: Expense):
        await db_session.delete(expense)
        await db_session.flush()

        result = await db_session.execute(
            select(Expense).where(Expense.id == expense.id)
        )
        assert result.scalar_one_or_none() is None