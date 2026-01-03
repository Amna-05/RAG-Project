"""
System metric model for monitoring.
File: src/rag/models/system_metric.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

from sqlalchemy import String, DateTime, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from rag.models.base import Base


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"      # Monotonically increasing (e.g., total requests)
    GAUGE = "gauge"          # Point-in-time value (e.g., active users)
    HISTOGRAM = "histogram"  # Distribution of values


class SystemMetric(Base):
    """
    Simple counter/gauge for monitoring.

    Metric names:
    - rate_limit_exceeded_total: 429 responses
    - upload_failed_total: Failed uploads
    - chat_queries_total: Chat requests
    - active_users: Currently active users
    """
    __tablename__ = "system_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    metric_type: Mapped[MetricType] = mapped_column(
        SQLEnum(MetricType),
        nullable=False
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Dimensional labels (e.g., {"endpoint": "/api/v1/chat", "status": "success"})
    labels: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SystemMetric {self.metric_name}={self.value}>"
