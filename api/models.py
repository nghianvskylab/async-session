from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model for performance testing."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hash: str
    salt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

