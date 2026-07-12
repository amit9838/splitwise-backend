import uuid

import pytest
from httpx import AsyncClient


class TestListUsers:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/api/users/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_with_data(self, client: AsyncClient, seeded_user):
        response = await client.get("/api/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == seeded_user.email
        assert data[0]["id"] == str(seeded_user.id)


class TestGetUser:
    @pytest.mark.asyncio
    async def test_found(self, client: AsyncClient, seeded_user):
        response = await client.get(f"/api/users/{seeded_user.id}")
        assert response.status_code == 200
        assert response.json()["email"] == seeded_user.email
        assert response.json()["id"] == str(seeded_user.id)

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/users/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient):
        payload = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
        }
        response = await client.post("/api/users/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_duplicate_email(self, client: AsyncClient, seeded_user):
        payload = {
            "email": seeded_user.email,
            "password": "secret123",
        }
        response = await client.post("/api/users/", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/users/",
            json={"email": "not-an-email", "password": "secret123"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_password(self, client: AsyncClient):
        response = await client.post(
            "/api/users/",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 422


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_full_update(self, client: AsyncClient, seeded_user):
        payload = {
            "email": "newemail@example.com",
            "full_name": "Updated Name",
            "password": "newpassword",
            "is_active": False,
        }
        response = await client.put(f"/api/users/{seeded_user.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["full_name"] == "Updated Name"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_partial_update(self, client: AsyncClient, seeded_user):
        response = await client.put(
            f"/api/users/{seeded_user.id}",
            json={"full_name": "Partial Update"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Partial Update"
        assert data["email"] == seeded_user.email

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/users/{fake_id}", json={"full_name": "Nope"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @pytest.mark.asyncio
    async def test_duplicate_email(self, client: AsyncClient, seeded_user):
        # Create another user first
        await client.post(
            "/api/users/",
            json={"email": "other@example.com", "password": "secret123"},
        )
        # Try to change seeded_user's email to the one just taken
        response = await client.put(
            f"/api/users/{seeded_user.id}",
            json={"email": "other@example.com"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_invalid_email(self, client: AsyncClient, seeded_user):
        response = await client.put(
            f"/api/users/{seeded_user.id}",
            json={"email": "bad-email"},
        )
        assert response.status_code == 422


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, seeded_user):
        response = await client.delete(f"/api/users/{seeded_user.id}")
        assert response.status_code == 204
        assert response.content == b""

        get_resp = await client.get(f"/api/users/{seeded_user.id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/users/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"