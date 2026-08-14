import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.settlement import Settlement
from app.models.user import User


@pytest_asyncio.fixture
async def payer(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="payer@example.com", hashed_password="h")
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def payee(db_session: AsyncSession) -> User:
    u = User(id=uuid.uuid4(), email="payee@example.com", hashed_password="h")
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


class TestSettlementCreate:
    @pytest.mark.asyncio
    async def test_create_settlement(
        self, db_session: AsyncSession, group: Group, payer: User, payee: User
    ):
        settlement = Settlement(
            group_id=group.id,
            paid_by=payer.id,
            paid_to=payee.id,
            amount=Decimal("250.00"),
        )
        db_session.add(settlement)
        await db_session.flush()
        await db_session.refresh(settlement)

        assert settlement.id is not None
        assert isinstance(settlement.id, uuid.UUID)
        assert settlement.group_id == group.id
        assert settlement.paid_by == payer.id
        assert settlement.paid_to == payee.id
        assert settlement.amount == Decimal("250.00")
        assert settlement.payment_method == "cash"
        assert settlement.note is None
        assert settlement.settled_at is not None
        assert settlement.created_at is not None

    @pytest.mark.asyncio
    async def test_create_settlement_with_explicit_values(
        self, db_session: AsyncSession, group: Group, payer: User, payee: User
    ):
        settlement = Settlement(
            group_id=group.id,
            paid_by=payer.id,
            paid_to=payee.id,
            amount=Decimal("100.00"),
            payment_method="upi",
            note="Dinner split",
        )
        db_session.add(settlement)
        await db_session.flush()
        await db_session.refresh(settlement)

        assert settlement.payment_method == "upi"
        assert settlement.note == "Dinner split"


class TestSettlementDelete:
    @pytest_asyncio.fixture
    async def settlement(
        self, db_session: AsyncSession, group: Group, payer: User, payee: User
    ) -> Settlement:
        s = Settlement(
            id=uuid.uuid4(),
            group_id=group.id,
            paid_by=payer.id,
            paid_to=payee.id,
            amount=Decimal("50.00"),
        )
        db_session.add(s)
        await db_session.flush()
        await db_session.refresh(s)
        return s

    @pytest.mark.asyncio
    async def test_delete_settlement(
        self, db_session: AsyncSession, settlement: Settlement
    ):
        await db_session.delete(settlement)
        await db_session.flush()

        result = await db_session.execute(
            select(Settlement).where(Settlement.id == settlement.id)
        )
        assert result.scalar_one_or_none() is None