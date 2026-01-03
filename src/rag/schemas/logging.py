"""
Logging and metrics request/response schemas.
File: src/rag/schemas/logging.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class RequestLogCreate(BaseModel):
    """Schema for creating a request log entry."""
    request_id: str = Field(
        ...,
        description="Correlation ID for request tracing",
        max_length=36
    )
    endpoint: str = Field(
        ...,
        description="API endpoint path",
        max_length=255
    )
    method: str = Field(
        ...,
        description="HTTP method",
        max_length=10
    )
    user_id: Optional[UUID] = Field(
        None,
        description="Authenticated user ID"
    )
    ip_address: Optional[str] = Field(
        None,
        description="Client IP address",
        max_length=45
    )
    status_code: int = Field(
        ...,
        description="HTTP response status code"
    )
    duration_ms: float = Field(
        ...,
        description="Request duration in milliseconds"
    )
    error_type: Optional[str] = Field(
        None,
        description="Error category if request failed",
        max_length=50
    )


class RequestLogResponse(RequestLogCreate):
    """Schema for request log response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class SystemMetricCreate(BaseModel):
    """Schema for creating a system metric entry."""
    metric_name: str = Field(
        ...,
        description="Metric identifier",
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    metric_type: MetricType = Field(
        ...,
        description="Type of metric"
    )
    value: float = Field(
        ...,
        description="Metric value"
    )
    labels: Optional[Dict[str, Any]] = Field(
        None,
        description="Dimensional labels"
    )


class SystemMetricResponse(SystemMetricCreate):
    """Schema for system metric response."""
    id: UUID
    recorded_at: datetime

    class Config:
        from_attributes = True


class LogEntry(BaseModel):
    """Structured log entry format."""
    timestamp: datetime = Field(
        ...,
        description="Log entry timestamp"
    )
    level: str = Field(
        ...,
        description="Log level (INFO, WARNING, ERROR)"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request correlation ID"
    )
    endpoint: Optional[str] = Field(
        None,
        description="API endpoint"
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID if authenticated"
    )
    status_code: Optional[int] = Field(
        None,
        description="HTTP status code"
    )
    duration_ms: Optional[float] = Field(
        None,
        description="Request duration"
    )
    message: str = Field(
        ...,
        description="Log message"
    )
    extra: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context"
    )
