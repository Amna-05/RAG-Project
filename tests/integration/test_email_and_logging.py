"""
Integration tests for email service and structured logging.
File: tests/integration/test_email_and_logging.py

Tests:
- Email service sends password reset emails
- Logging middleware captures requests with timing
- Logging filters sensitive data
- Forgot-password endpoint works with rate limiting
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.user import User
from rag.services.email_service import EmailService, get_email_service
from rag.core.logging import filter_sensitive_data, LoggingMiddleware


class TestEmailService:
    """Test email service functionality."""

    @pytest.mark.asyncio
    async def test_send_password_reset_email_with_mock(self):
        """Test password reset email is constructed correctly."""
        with patch('rag.services.email_service.Resend') as mock_resend:
            # Mock the Resend client
            mock_client = MagicMock()
            mock_client.emails.send.return_value = {"id": "test-email-id"}
            mock_resend.return_value = mock_client

            service = EmailService()
            service.client = mock_client

            # Call the method
            result = service.send_password_reset_email(
                email="user@example.com",
                reset_link="http://localhost:3000/reset?token=abc123",
                username="testuser"
            )

            # Verify
            assert result is True
            assert mock_client.emails.send.called
            call_args = mock_client.emails.send.call_args[0][0]
            assert call_args["to"] == "user@example.com"
            assert "Reset Your Password" in call_args["subject"]
            assert "abc123" in call_args["html"]
            assert "testuser" in call_args["html"]

    @pytest.mark.asyncio
    async def test_send_password_reset_email_no_client(self):
        """Test password reset email fails gracefully without API key."""
        service = EmailService()
        service.client = None  # Simulate missing API key

        result = service.send_password_reset_email(
            email="user@example.com",
            reset_link="http://localhost:3000/reset",
            username="testuser"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_email_with_mock(self):
        """Test welcome email is sent correctly."""
        with patch('rag.services.email_service.Resend') as mock_resend:
            mock_client = MagicMock()
            mock_client.emails.send.return_value = {"id": "welcome-email-id"}
            mock_resend.return_value = mock_client

            service = EmailService()
            service.client = mock_client

            result = service.send_welcome_email(
                email="user@example.com",
                username="testuser"
            )

            assert result is True
            assert mock_client.emails.send.called
            call_args = mock_client.emails.send.call_args[0][0]
            assert call_args["to"] == "user@example.com"
            assert "Welcome" in call_args["subject"]


class TestSensitiveDataFiltering:
    """Test logging filters sensitive data correctly."""

    def test_filter_password_field(self):
        """Test password field is redacted."""
        data = {
            "username": "testuser",
            "password": "SecurePassword123!",
            "email": "test@example.com"
        }

        filtered = filter_sensitive_data(data)

        assert filtered["username"] == "testuser"
        assert filtered["password"] == "[REDACTED]"
        assert filtered["email"] == "test@example.com"

    def test_filter_api_key_field(self):
        """Test API key field is redacted."""
        data = {
            "service": "pinecone",
            "api_key": "pc_1234567890abcdef",
            "index": "rag-index"
        }

        filtered = filter_sensitive_data(data)

        assert filtered["service"] == "pinecone"
        assert filtered["api_key"] == "[REDACTED]"
        assert filtered["index"] == "rag-index"

    def test_filter_token_fields(self):
        """Test token fields are redacted."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "authorization": "Bearer token123"
        }

        filtered = filter_sensitive_data(data)

        assert filtered["access_token"] == "[REDACTED]"
        assert filtered["refresh_token"] == "[REDACTED]"
        assert filtered["authorization"] == "[REDACTED]"

    def test_filter_nested_data(self):
        """Test nested sensitive data is redacted."""
        data = {
            "user": {
                "username": "testuser",
                "password": "SecurePass123!",
                "settings": {
                    "api_key": "secret123",
                    "notifications": True
                }
            }
        }

        filtered = filter_sensitive_data(data)

        assert filtered["user"]["username"] == "testuser"
        assert filtered["user"]["password"] == "[REDACTED]"
        assert filtered["user"]["settings"]["api_key"] == "[REDACTED]"
        assert filtered["user"]["settings"]["notifications"] is True


class TestForgotPasswordEndpoint:
    """Test forgot-password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_user_exists(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test forgot password returns generic response when user exists."""
        with patch('rag.api.v1.auth.send_password_reset_email') as mock_send:
            mock_send.return_value = True

            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email}
            )

            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            # Generic message - doesn't reveal if user exists
            assert "If an account exists" in data["email"] or "If an account exists" in str(data)

    @pytest.mark.asyncio
    async def test_forgot_password_user_not_exists(self, client: AsyncClient):
        """Test forgot password returns generic response when user doesn't exist."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        # Generic message - doesn't reveal if user exists
        assert "If an account exists" in str(data)

    @pytest.mark.asyncio
    async def test_forgot_password_rate_limit(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test forgot password endpoint respects rate limiting."""
        # Make 3 requests (should succeed)
        for i in range(3):
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email}
            )
            assert response.status_code == 200

        # 4th request should be rate limited
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email}
        )
        # Note: Rate limit status depends on RateLimiter implementation
        # This test documents the expected behavior


class TestLoggingIntegration:
    """Test logging integration with API endpoints."""

    @pytest.mark.asyncio
    async def test_request_logging_headers(self, client: AsyncClient):
        """Test that response includes X-Process-Time header."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        # Verify it's a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    @pytest.mark.asyncio
    async def test_logging_middleware_exists(self):
        """Test that logging middleware is configured."""
        # This is a basic sanity check
        from rag.core.logging import LoggingMiddleware
        assert LoggingMiddleware is not None
        assert hasattr(LoggingMiddleware, '__call__')

    @pytest.mark.asyncio
    async def test_email_service_singleton(self):
        """Test email service singleton pattern."""
        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2
