import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.user import UserBase, UserCreate, UserResponse, UserUpdate


class TestUserBase:
    def test_valid(self):
        data = UserBase(email="user@example.com", full_name="John Doe")
        assert data.email == "user@example.com"
        assert data.full_name == "John Doe"

    def test_without_full_name(self):
        data = UserBase(email="user@example.com")
        assert data.email == "user@example.com"
        assert data.full_name is None

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserBase(email="not-an-email")

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            UserBase(email="")


class TestUserCreate:
    def test_valid(self):
        data = UserCreate(
            email="new@example.com", password="secret123", full_name="New User"
        )
        assert data.email == "new@example.com"
        assert data.password == "secret123"

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="new@example.com")

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            UserCreate(password="secret123")


class TestUserUpdate:
    def test_full_update(self):
        data = UserUpdate(
            email="updated@example.com",
            full_name="Updated",
            password="newpass",
            is_active=False,
        )
        assert data.email == "updated@example.com"
        assert data.is_active is False

    def test_partial_update(self):
        data = UserUpdate(full_name="Only Name")
        assert data.full_name == "Only Name"
        assert data.email is None
        assert data.password is None

    def test_empty_update(self):
        data = UserUpdate()
        assert all(v is None for v in [data.email, data.full_name, data.password, data.is_active])


class TestUserResponse:
    def test_from_dict(self):
        user_data = {
            "id": uuid.uuid4(),
            "email": "resp@example.com",
            "full_name": "Response User",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        resp = UserResponse(**user_data)
        assert resp.id == user_data["id"]
        assert resp.email == user_data["email"]

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UserResponse(email="x@x.com")