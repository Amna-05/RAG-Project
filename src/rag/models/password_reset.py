"""
Password reset token model.
File: src/rag/models/password_reset.py
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from rag.models.base import Base


class PasswordResetToken(Base):
    """
    Secure token for password reset workflow.

    Security features:
    - Token hash stored, not plaintext
    - 1-hour expiry (per clarification)
    - Single-use (used_at marks as consumed)
    - Previous tokens invalidated on new request
    """
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # SHA-256 hash of the token (32 bytes random -> 64 char hex hash)
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    # Expiration: created_at + 1 hour
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    # When token was consumed (NULL if unused)
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship to user
    user = relationship("User", backref="password_reset_tokens")

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        now = datetime.utcnow()
        return self.used_at is None and self.expires_at > now

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} valid={self.is_valid}>"
