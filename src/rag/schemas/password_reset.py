"""
Password reset request/response schemas.
File: src/rag/schemas/password_reset.py
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset."""
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )


class ForgotPasswordResponse(BaseModel):
    """Response for password reset request."""
    message: str = Field(
        default="If an account with that email exists, a reset link has been sent.",
        description="Generic message to prevent email enumeration"
    )
    success: bool = True


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token."""
    token: str = Field(
        ...,
        description="Password reset token from email",
        min_length=32,
        examples=["abc123def456..."]
    )
    new_password: str = Field(
        ...,
        description="New password (minimum 8 characters)",
        min_length=8,
        examples=["NewSecurePassword123!"]
    )


class ResetPasswordResponse(BaseModel):
    """Response for password reset completion."""
    message: str = Field(
        default="Password has been reset successfully. Please log in.",
        description="Success message"
    )
    success: bool = True


class TokenValidResponse(BaseModel):
    """Response for token validity check."""
    valid: bool = Field(
        ...,
        description="Whether the token is valid"
    )
    expires_in_seconds: Optional[int] = Field(
        None,
        description="Seconds until token expires",
        examples=[3540]
    )


class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str = Field(
        ...,
        description="Error message",
        examples=["Invalid or expired reset token"]
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code for client handling",
        examples=["INVALID_TOKEN"]
    )


class RateLimitError(BaseModel):
    """Rate limit exceeded response."""
    detail: str = Field(
        default="Rate limit exceeded. Please try again later.",
        description="Error message"
    )
    retry_after: int = Field(
        ...,
        description="Seconds to wait before retry",
        examples=[60]
    )
    error_code: str = Field(
        default="RATE_LIMIT_EXCEEDED",
        description="Error code"
    )
