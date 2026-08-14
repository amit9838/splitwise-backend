from decimal import Decimal
from typing import Optional

from app.schemas.expenses import ExpenseSplitCreate


class SplitCalculator:
    """Calculates how an expense should be split among participants."""

    @staticmethod
    def calculate(
        total_amount: Decimal,
        split_type: str,
        splits: list[ExpenseSplitCreate],
        participant_ids: list[str],
    ) -> list[dict]:
        """
        Returns a list of dicts with user_id and amount for each split.
        """
        if split_type == "EQUAL":
            return SplitCalculator._equal_split(total_amount, participant_ids)
        elif split_type == "EXACT":
            return SplitCalculator._exact_split(total_amount, splits)
        elif split_type == "PERCENTAGE":
            return SplitCalculator._percentage_split(total_amount, splits)
        elif split_type == "SHARES":
            return SplitCalculator._shares_split(total_amount, splits)
        else:
            raise ValueError(f"Unknown split type: {split_type}")

    @staticmethod
    def _equal_split(total: Decimal, participant_ids: list[str]) -> list[dict]:
        if not participant_ids:
            raise ValueError("At least one participant required for equal split")
        share = total / len(participant_ids)
        # Round to 2 decimal places
        share = share.quantize(Decimal("0.01"))
        return [{"user_id": uid, "amount": share} for uid in participant_ids]

    @staticmethod
    def _exact_split(total: Decimal, splits: list[ExpenseSplitCreate]) -> list[dict]:
        if not splits:
            raise ValueError("Splits required for exact split")
        split_sum = sum(
            (s.amount or Decimal("0")) for s in splits
        )
        if split_sum != total:
            raise ValueError(
                f"Sum of exact splits ({split_sum}) must equal total ({total})"
            )
        return [
            {"user_id": str(s.user_id), "amount": s.amount or Decimal("0")}
            for s in splits
        ]

    @staticmethod
    def _percentage_split(
        total: Decimal, splits: list[ExpenseSplitCreate]
    ) -> list[dict]:
        if not splits:
            raise ValueError("Splits required for percentage split")
        total_pct = sum(s.percentage or 0 for s in splits)
        if abs(total_pct - 100) > 0.01:
            raise ValueError(
                f"Percentages must sum to 100, got {total_pct}"
            )
        result = []
        for s in splits:
            pct = Decimal(str(s.percentage or 0))
            amount = (total * pct / Decimal("100")).quantize(Decimal("0.01"))
            result.append({"user_id": str(s.user_id), "amount": amount})
        return result

    @staticmethod
    def _shares_split(total: Decimal, splits: list[ExpenseSplitCreate]) -> list[dict]:
        if not splits:
            raise ValueError("Splits required for shares split")
        total_shares = sum(s.shares or 0 for s in splits)
        if total_shares == 0:
            raise ValueError("Total shares must be greater than 0")
        result = []
        for s in splits:
            share_count = Decimal(str(s.shares or 0))
            amount = (total * share_count / Decimal(str(total_shares))).quantize(
                Decimal("0.01")
            )
            result.append({"user_id": str(s.user_id), "amount": amount})
        return result