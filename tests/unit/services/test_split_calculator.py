import uuid
from decimal import Decimal

import pytest

from app.schemas.expenses import ExpenseSplitCreate
from app.services.split_calculator import SplitCalculator


class TestEqualSplit:
    def test_equal_split_four_people(self):
        participant_ids = [str(uuid.uuid4()) for _ in range(4)]
        result = SplitCalculator.calculate(
            total_amount=Decimal("1000.00"),
            split_type="EQUAL",
            splits=[],
            participant_ids=participant_ids,
        )

        assert len(result) == 4
        for r in result:
            assert r["amount"] == Decimal("250.00")

    def test_equal_split_no_participants_raises(self):
        with pytest.raises(ValueError):
            SplitCalculator.calculate(
                total_amount=Decimal("100.00"),
                split_type="EQUAL",
                splits=[],
                participant_ids=[],
            )


class TestExactSplit:
    def test_exact_split_valid(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), amount=Decimal("300.00")),
            ExpenseSplitCreate(user_id=uuid.uuid4(), amount=Decimal("200.00")),
            ExpenseSplitCreate(user_id=uuid.uuid4(), amount=Decimal("500.00")),
        ]
        result = SplitCalculator.calculate(
            total_amount=Decimal("1000.00"),
            split_type="EXACT",
            splits=splits,
            participant_ids=[],
        )

        assert len(result) == 3
        assert sum(r["amount"] for r in result) == Decimal("1000.00")

    def test_exact_split_sum_mismatch_raises(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), amount=Decimal("300.00")),
            ExpenseSplitCreate(user_id=uuid.uuid4(), amount=Decimal("200.00")),
        ]
        with pytest.raises(ValueError):
            SplitCalculator.calculate(
                total_amount=Decimal("1000.00"),
                split_type="EXACT",
                splits=splits,
                participant_ids=[],
            )


class TestPercentageSplit:
    def test_percentage_split_valid(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), percentage=50.0),
            ExpenseSplitCreate(user_id=uuid.uuid4(), percentage=30.0),
            ExpenseSplitCreate(user_id=uuid.uuid4(), percentage=20.0),
        ]
        result = SplitCalculator.calculate(
            total_amount=Decimal("1000.00"),
            split_type="PERCENTAGE",
            splits=splits,
            participant_ids=[],
        )

        assert len(result) == 3
        amounts = [r["amount"] for r in result]
        assert amounts[0] == Decimal("500.00")
        assert amounts[1] == Decimal("300.00")
        assert amounts[2] == Decimal("200.00")

    def test_percentage_split_not_100_raises(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), percentage=50.0),
            ExpenseSplitCreate(user_id=uuid.uuid4(), percentage=30.0),
        ]
        with pytest.raises(ValueError):
            SplitCalculator.calculate(
                total_amount=Decimal("1000.00"),
                split_type="PERCENTAGE",
                splits=splits,
                participant_ids=[],
            )


class TestSharesSplit:
    def test_shares_split_valid(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), shares=2),
            ExpenseSplitCreate(user_id=uuid.uuid4(), shares=1),
            ExpenseSplitCreate(user_id=uuid.uuid4(), shares=1),
        ]
        result = SplitCalculator.calculate(
            total_amount=Decimal("1000.00"),
            split_type="SHARES",
            splits=splits,
            participant_ids=[],
        )

        assert len(result) == 3
        amounts = [r["amount"] for r in result]
        assert amounts[0] == Decimal("500.00")
        assert amounts[1] == Decimal("250.00")
        assert amounts[2] == Decimal("250.00")

    def test_shares_split_zero_shares_raises(self):
        splits = [
            ExpenseSplitCreate(user_id=uuid.uuid4(), shares=0),
            ExpenseSplitCreate(user_id=uuid.uuid4(), shares=0),
        ]
        with pytest.raises(ValueError):
            SplitCalculator.calculate(
                total_amount=Decimal("1000.00"),
                split_type="SHARES",
                splits=splits,
                participant_ids=[],
            )


class TestUnknownSplitType:
    def test_unknown_split_type_raises(self):
        with pytest.raises(ValueError):
            SplitCalculator.calculate(
                total_amount=Decimal("100.00"),
                split_type="INVALID",
                splits=[],
                participant_ids=[str(uuid.uuid4())],
            )