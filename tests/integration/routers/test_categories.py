import uuid

import pytest
from httpx import AsyncClient


class TestListCategories:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/api/categories/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_with_data(self, client: AsyncClient, seeded_category):
        response = await client.get("/api/categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == seeded_category.name
        assert data[0]["id"] == str(seeded_category.id)


class TestGetCategory:
    @pytest.mark.asyncio
    async def test_found(self, client: AsyncClient, seeded_category):
        response = await client.get(f"/api/categories/{seeded_category.id}")
        assert response.status_code == 200
        assert response.json()["name"] == seeded_category.name

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/categories/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"


class TestCreateCategory:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient):
        response = await client.post("/api/categories/", json={"name": "Groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Groceries"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_missing_name(self, client: AsyncClient):
        response = await client.post("/api/categories/", json={})
        assert response.status_code == 422


class TestUpdateCategory:
    @pytest.mark.asyncio
    async def test_full_update(self, client: AsyncClient, seeded_category):
        payload = {"name": "Updated Category", "is_active": False}
        response = await client.put(
            f"/api/categories/{seeded_category.id}", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_name_only(self, client: AsyncClient, seeded_category):
        payload = {"name": "New Name Only"}
        response = await client.put(
            f"/api/categories/{seeded_category.id}", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Only"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_is_active_only(self, client: AsyncClient, seeded_category):
        payload = {"is_active": False}
        response = await client.put(
            f"/api/categories/{seeded_category.id}", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == seeded_category.name
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/categories/{fake_id}", json={"name": "Nope"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"


class TestDeleteCategory:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, seeded_category):
        response = await client.delete(f"/api/categories/{seeded_category.id}")
        assert response.status_code == 204
        assert response.content == b""

        get_resp = await client.get(f"/api/categories/{seeded_category.id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/categories/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"