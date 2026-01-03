"""
Request log model for API audit logging.
File: src/rag/models/request_log.py
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from rag.models.base import Base


class RequestLog(Base):
    """
    Audit log for API requests.

    Features:
    - Request correlation via request_id
    - User tracking for authenticated requests
    - Duration and status for performance monitoring
    - 30-day retention (cleanup via scheduled task)
    """
    __tablename__ = "request_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Correlation ID for request tracing
    request_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True
    )

    # Request details
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    # User (NULL for unauthenticated requests)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Client info
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True
    )

    # Response info
    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    duration_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Error tracking
    error_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<RequestLog {self.method} {self.endpoint} -> {self.status_code}>"
