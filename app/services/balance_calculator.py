import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit


class BalanceCalculator:
    """Calculates net balances for group members based on all expenses."""

    @staticmethod
    async def get_group_balances(
        group_id: uuid.UUID, db: AsyncSession
    ) -> dict[str, Decimal]:
        """
        Returns a dict of user_id (str) -> net balance.
        Positive = user is owed money (creditor).
        Negative = user owes money (debtor).
        """
        balances: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        # Get all active expenses for the group
        result = await db.execute(
            select(Expense).where(
                Expense.group_id == group_id,
                Expense.is_active == True,
            )
        )
        expenses = result.scalars().all()

        for expense in expenses:
            payer_id = str(expense.paid_by)

            # Payer paid the full amount, so they are owed the full amount
            balances[payer_id] += expense.amount

            # Get splits for this expense
            splits_result = await db.execute(
                select(ExpenseSplit).where(
                    ExpenseSplit.expense_id == expense.id,
                )
            )
            splits = splits_result.scalars().all()

            # Each participant owes their share
            for split in splits:
                participant_id = str(split.user_id)
                balances[participant_id] -= split.amount

        return dict(balances)

    @staticmethod
    def simplify_debts(
        balances: dict[str, Decimal],
    ) -> list[dict]:
        """
        Simplify debts to minimize the number of transactions.
        Uses a greedy algorithm: repeatedly settle the largest debtor
        with the largest creditor.

        Returns list of {from_user_id, to_user_id, amount}.
        """
        # Separate creditors (positive) and debtors (negative)
        creditors = []
        debtors = []
        for user_id, balance in balances.items():
            if balance > 0:
                creditors.append([user_id, balance])
            elif balance < 0:
                debtors.append([user_id, -balance])  # store as positive amount owed

        # Sort: largest creditors/debtors first
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        transactions = []
        i, j = 0, 0

        while i < len(debtors) and j < len(creditors):
            debtor_id, debt_amount = debtors[i]
            creditor_id, credit_amount = creditors[j]

            settle_amount = min(debt_amount, credit_amount)
            settle_amount = settle_amount.quantize(Decimal("0.01"))

            if settle_amount > 0:
                transactions.append({
                    "from_user_id": debtor_id,
                    "to_user_id": creditor_id,
                    "amount": settle_amount,
                })

            debtors[i][1] -= settle_amount
            creditors[j][1] -= settle_amount

            if debtors[i][1] < Decimal("0.01"):
                i += 1
            if creditors[j][1] < Decimal("0.01"):
                j += 1

        return transactions