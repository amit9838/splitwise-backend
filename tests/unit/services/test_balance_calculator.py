from decimal import Decimal

from app.services.balance_calculator import BalanceCalculator


class TestSimplifyDebts:
    def test_simple_two_person_debt(self):
        balances = {
            "alice": Decimal("50.00"),
            "bob": Decimal("-50.00"),
        }
        result = BalanceCalculator.simplify_debts(balances)

        assert len(result) == 1
        assert result[0]["from_user_id"] == "bob"
        assert result[0]["to_user_id"] == "alice"
        assert result[0]["amount"] == Decimal("50.00")

    def test_multi_person_simplification(self):
        # Alice is owed 100, Bob owes 60, Carol owes 40
        balances = {
            "alice": Decimal("100.00"),
            "bob": Decimal("-60.00"),
            "carol": Decimal("-40.00"),
        }
        result = BalanceCalculator.simplify_debts(balances)

        assert len(result) == 2
        # Both debtors pay Alice
        for t in result:
            assert t["to_user_id"] == "alice"
        total = sum(t["amount"] for t in result)
        assert total == Decimal("100.00")

    def test_empty_balances(self):
        result = BalanceCalculator.simplify_debts({})
        assert result == []

    def test_settled_balances(self):
        balances = {
            "alice": Decimal("0.00"),
            "bob": Decimal("0.00"),
        }
        result = BalanceCalculator.simplify_debts(balances)
        assert result == []

    def test_chain_simplification(self):
        # A owes B 50, B owes C 30, C owes A 20
        # Net: A owes 30, B owes 20, C is owed 50
        balances = {
            "a": Decimal("-30.00"),
            "b": Decimal("-20.00"),
            "c": Decimal("50.00"),
        }
        result = BalanceCalculator.simplify_debts(balances)

        # A and B both pay C
        assert len(result) == 2
        for t in result:
            assert t["to_user_id"] == "c"
        total = sum(t["amount"] for t in result)
        assert total == Decimal("50.00")