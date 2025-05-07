"""This file contains the thread model for the application."""

from datetime import (
    UTC,
    datetime,
)
from typing import Optional
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
)
from models.base import BaseModel


class Thread(BaseModel, table=True):
    """Thread model for storing conversation threads.

    Attributes:
        id: The primary key
        user_id: ID of the user to which the thread belongs
        created_at: When the thread was created
        user: Relationship with the owner user
    """

    __tablename__ = "thread"  # Explicitly set table name

    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user: "User" = Relationship(back_populates="threads", sa_relationship_kwargs={"lazy": "selectin"})

# Evitar importaciones circulares
from models.user import User  # noqa: E402
