import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email="txnuser@example.com",
        hashed_password="hashed",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def category(db_session: AsyncSession) -> Category:
    cat = Category(id=uuid.uuid4(), name="Shopping")
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)
    return cat


class TestTransactionCreate:
    @pytest.mark.asyncio
    async def test_create_transaction(
        self, db_session: AsyncSession, user: User, category: Category
    ):
        txn = Transaction(
            user_id=user.id,
            category_id=category.id,
            amount=150.75,
            description="Weekly grocery shopping",
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(txn)
        await db_session.flush()
        await db_session.refresh(txn)

        assert txn.id is not None
        assert isinstance(txn.id, uuid.UUID)
        assert txn.user_id == user.id
        assert txn.category_id == category.id
        assert txn.amount == 150.75
        assert txn.description == "Weekly grocery shopping"
        assert txn.is_active is True
        assert txn.created_at is not None
        assert txn.transaction_date is not None

    @pytest.mark.asyncio
    async def test_create_transaction_default_description(
        self, db_session: AsyncSession, user: User, category: Category
    ):
        txn = Transaction(
            user_id=user.id,
            category_id=category.id,
            amount=50.0,
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(txn)
        await db_session.flush()
        await db_session.refresh(txn)

        assert txn.description is None


class TestTransactionUpdate:
    @pytest_asyncio.fixture
    async def transaction(
        self, db_session: AsyncSession, user: User, category: Category
    ) -> Transaction:
        txn = Transaction(
            id=uuid.uuid4(),
            user_id=user.id,
            category_id=category.id,
            amount=99.99,
            description="Electricity bill",
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(txn)
        await db_session.flush()
        await db_session.refresh(txn)
        return txn

    @pytest.mark.asyncio
    async def test_update_amount_and_description(
        self, db_session: AsyncSession, transaction: Transaction
    ):
        transaction.amount = 200.50
        transaction.description = "Updated description"
        await db_session.flush()
        await db_session.refresh(transaction)

        assert transaction.amount == 200.50
        assert transaction.description == "Updated description"
        assert transaction.updated_at is not None

    @pytest.mark.asyncio
    async def test_deactivate(self, db_session: AsyncSession, transaction: Transaction):
        transaction.is_active = False
        await db_session.flush()
        await db_session.refresh(transaction)

        assert transaction.is_active is False


class TestTransactionDelete:
    @pytest_asyncio.fixture
    async def transaction(
        self, db_session: AsyncSession, user: User, category: Category
    ) -> Transaction:
        txn = Transaction(
            id=uuid.uuid4(),
            user_id=user.id,
            category_id=category.id,
            amount=10.0,
            transaction_date=datetime.now(timezone.utc),
        )
        db_session.add(txn)
        await db_session.flush()
        await db_session.refresh(txn)
        return txn

    @pytest.mark.asyncio
    async def test_delete_transaction(
        self, db_session: AsyncSession, transaction: Transaction
    ):
        await db_session.delete(transaction)
        await db_session.flush()

        result = await db_session.execute(
            select(Transaction).where(Transaction.id == transaction.id)
        )
        assert result.scalar_one_or_none() is None