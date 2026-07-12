import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


class TestListTransactions:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/api/transactions/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_with_data(self, client: AsyncClient, seeded_transaction):
        response = await client.get("/api/transactions/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["amount"] == seeded_transaction.amount
        assert data[0]["id"] == str(seeded_transaction.id)


class TestGetTransaction:
    @pytest.mark.asyncio
    async def test_found(self, client: AsyncClient, seeded_transaction):
        response = await client.get(f"/api/transactions/{seeded_transaction.id}")
        assert response.status_code == 200
        assert response.json()["amount"] == seeded_transaction.amount

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/transactions/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"


class TestCreateTransaction:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, seeded_user, seeded_category):
        payload = {
            "user_id": str(seeded_user.id),
            "category_id": str(seeded_category.id),
            "amount": 250.50,
            "description": "Dinner at restaurant",
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }
        response = await client.post("/api/transactions/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 250.50
        assert data["description"] == "Dinner at restaurant"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_amount_zero_raises(
        self, client: AsyncClient, seeded_user, seeded_category
    ):
        payload = {
            "user_id": str(seeded_user.id),
            "category_id": str(seeded_category.id),
            "amount": 0,
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }
        response = await client.post("/api/transactions/", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_amount_negative_raises(
        self, client: AsyncClient, seeded_user, seeded_category
    ):
        payload = {
            "user_id": str(seeded_user.id),
            "category_id": str(seeded_category.id),
            "amount": -50,
            "transaction_date": datetime.now(timezone.utc).isoformat(),
        }
        response = await client.post("/api/transactions/", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        response = await client.post("/api/transactions/", json={"amount": 100})
        assert response.status_code == 422


class TestUpdateTransaction:
    @pytest.mark.asyncio
    async def test_full_update(self, client: AsyncClient, seeded_transaction):
        new_date = datetime.now(timezone.utc).isoformat()
        payload = {
            "amount": 500.00,
            "description": "Updated description",
            "transaction_date": new_date,
            "is_active": False,
        }
        response = await client.put(
            f"/api/transactions/{seeded_transaction.id}", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 500.00
        assert data["description"] == "Updated description"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_partial_amount(self, client: AsyncClient, seeded_transaction):
        response = await client.put(
            f"/api/transactions/{seeded_transaction.id}",
            json={"amount": 999.99},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 999.99
        assert data["description"] == seeded_transaction.description

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/transactions/{fake_id}", json={"amount": 100}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"

    @pytest.mark.asyncio
    async def test_invalid_amount(self, client: AsyncClient, seeded_transaction):
        response = await client.put(
            f"/api/transactions/{seeded_transaction.id}",
            json={"amount": -10},
        )
        assert response.status_code == 422


class TestDeleteTransaction:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, seeded_transaction):
        response = await client.delete(f"/api/transactions/{seeded_transaction.id}")
        assert response.status_code == 204
        assert response.content == b""

        get_resp = await client.get(f"/api/transactions/{seeded_transaction.id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/transactions/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"