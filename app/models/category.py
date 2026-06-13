import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, String, Uuid, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String, nullable=False)  # Enum ["expense", "income"]
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"),  nullable=False
    )  # FK user
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    # Ensure categories are unique per user (same name + type)
    __table_args__ = (
        UniqueConstraint("user_id", "name", "type", name="uq_user_category"),
    )
