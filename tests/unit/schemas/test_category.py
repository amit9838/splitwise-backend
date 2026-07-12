import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.categories import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


class TestCategoryBase:
    def test_valid(self):
        data = CategoryBase(name="Food")
        assert data.name == "Food"

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            CategoryBase()

    def test_empty_name(self):
        data = CategoryBase(name="")
        assert data.name == ""


class TestCategoryCreate:
    def test_valid(self):
        data = CategoryCreate(name="Entertainment")
        assert data.name == "Entertainment"


class TestCategoryUpdate:
    def test_full_update(self):
        data = CategoryUpdate(name="Updated", is_active=False)
        assert data.name == "Updated"
        assert data.is_active is False

    def test_name_only(self):
        data = CategoryUpdate(name="Only Name")
        assert data.name == "Only Name"
        assert data.is_active is None

    def test_is_active_only(self):
        data = CategoryUpdate(is_active=True)
        assert data.name is None
        assert data.is_active is True

    def test_empty(self):
        data = CategoryUpdate()
        assert data.name is None
        assert data.is_active is None


class TestCategoryResponse:
    def test_from_dict(self):
        cat_data = {
            "id": uuid.uuid4(),
            "name": "Test Cat",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        resp = CategoryResponse(**cat_data)
        assert resp.id == cat_data["id"]
        assert resp.name == cat_data["name"]

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            CategoryResponse(name="Missing ID")