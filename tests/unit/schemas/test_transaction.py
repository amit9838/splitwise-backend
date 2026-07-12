import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.transactions import (
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


class TestTransactionBase:
    def test_valid(self):
        txn = TransactionBase(
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            amount=100.50,
            transaction_date=datetime.now(timezone.utc),
        )
        assert txn.amount == 100.50

    def test_amount_zero_raises(self):
        with pytest.raises(ValidationError) as exc:
            TransactionBase(
                user_id=uuid.uuid4(),
                category_id=uuid.uuid4(),
                amount=0,
                transaction_date=datetime.now(timezone.utc),
            )
        assert "amount" in str(exc.value)

    def test_amount_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            TransactionBase(
                user_id=uuid.uuid4(),
                category_id=uuid.uuid4(),
                amount=-10,
                transaction_date=datetime.now(timezone.utc),
            )
        assert "amount" in str(exc.value)

    def test_optional_description(self):
        txn = TransactionBase(
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            amount=50.0,
            transaction_date=datetime.now(timezone.utc),
        )
        assert txn.description is None

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            TransactionBase(amount=50.0)


class TestTransactionCreate:
    def test_valid(self):
        txn = TransactionCreate(
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            amount=75.25,
            transaction_date=datetime.now(timezone.utc),
            description="Test",
        )
        assert txn.amount == 75.25
        assert txn.description == "Test"


class TestTransactionUpdate:
    def test_full_update(self):
        txn = TransactionUpdate(
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            amount=200.0,
            description="Updated",
            transaction_date=datetime.now(timezone.utc),
            is_active=False,
        )
        assert txn.amount == 200.0
        assert txn.is_active is False

    def test_partial_update(self):
        txn = TransactionUpdate(amount=300.0)
        assert txn.amount == 300.0
        assert txn.user_id is None
        assert txn.category_id is None
        assert txn.description is None
        assert txn.transaction_date is None
        assert txn.is_active is None

    def test_empty(self):
        txn = TransactionUpdate()
        assert txn.user_id is None
        assert txn.category_id is None
        assert txn.amount is None

    def test_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            TransactionUpdate(amount=0)

    def test_amount_negative_raises(self):
        with pytest.raises(ValidationError):
            TransactionUpdate(amount=-5)


class TestTransactionResponse:
    def test_from_dict(self):
        txn_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "category_id": uuid.uuid4(),
            "amount": 250.0,
            "transaction_date": datetime.now(timezone.utc),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        resp = TransactionResponse(**txn_data)
        assert resp.id == txn_data["id"]
        assert resp.amount == 250.0
        assert resp.is_active is True

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            TransactionResponse(amount=100)