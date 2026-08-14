import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
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
async def participant(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="participant@example.com", hashed_password="h")
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


@pytest_asyncio.fixture
async def expense(
    db_session: AsyncSession, group: Group, payer: User, category: Category
) -> Expense:
    e = Expense(
        id=uuid.uuid4(),
        group_id=group.id,
        paid_by=payer.id,
        category_id=category.id,
        amount=Decimal("1000.00"),
        description="Dinner",
    )
    db_session.add(e)
    await db_session.flush()
    await db_session.refresh(e)
    return e


class TestExpenseSplitCreate:
    @pytest.mark.asyncio
    async def test_create_split(
        self, db_session: AsyncSession, expense: Expense, participant: User
    ):
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=participant.id,
            amount=Decimal("250.00"),
        )
        db_session.add(split)
        await db_session.flush()
        await db_session.refresh(split)

        assert split.id is not None
        assert isinstance(split.id, uuid.UUID)
        assert split.expense_id == expense.id
        assert split.user_id == participant.id
        assert split.amount == Decimal("250.00")
        assert split.percentage is None
        assert split.shares is None

    @pytest.mark.asyncio
    async def test_create_split_with_percentage(
        self, db_session: AsyncSession, expense: Expense, participant: User
    ):
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=participant.id,
            amount=Decimal("500.00"),
            percentage=50.0,
        )
        db_session.add(split)
        await db_session.flush()
        await db_session.refresh(split)

        assert split.percentage == 50.0

    @pytest.mark.asyncio
    async def test_create_split_with_shares(
        self, db_session: AsyncSession, expense: Expense, participant: User
    ):
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=participant.id,
            amount=Decimal("500.00"),
            shares=2,
        )
        db_session.add(split)
        await db_session.flush()
        await db_session.refresh(split)

        assert split.shares == 2


class TestExpenseSplitDelete:
    @pytest_asyncio.fixture
    async def split(
        self, db_session: AsyncSession, expense: Expense, participant: User
    ) -> ExpenseSplit:
        s = ExpenseSplit(
            id=uuid.uuid4(),
            expense_id=expense.id,
            user_id=participant.id,
            amount=Decimal("250.00"),
        )
        db_session.add(s)
        await db_session.flush()
        await db_session.refresh(s)
        return s

    @pytest.mark.asyncio
    async def test_delete_split(
        self, db_session: AsyncSession, split: ExpenseSplit
    ):
        await db_session.delete(split)
        await db_session.flush()

        result = await db_session.execute(
            select(ExpenseSplit).where(ExpenseSplit.id == split.id)
        )
        assert result.scalar_one_or_none() is None