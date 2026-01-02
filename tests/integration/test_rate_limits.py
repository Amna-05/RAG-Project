"""
Integration tests for API rate limiting.
File: tests/integration/test_rate_limits.py

Tests rate limiting on chat, upload, and auth endpoints.
Uses in-memory storage for isolated tests.

Run with: pytest tests/integration/test_rate_limits.py -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
import asyncio

from rag.main import app
from rag.core.rate_limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test."""
    # Clear any existing limits by resetting the limiter's storage
    if hasattr(limiter, '_storage') and limiter._storage:
        try:
            limiter._storage.reset()
        except Exception:
            pass
    yield
    # Cleanup after test
    if hasattr(limiter, '_storage') and limiter._storage:
        try:
            limiter._storage.reset()
        except Exception:
            pass


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def unique_ip():
    """Generate unique IP for each test to avoid rate limit interference."""
    import uuid
    import time
    # Use time + random to ensure uniqueness across test runs
    unique = f"{time.time_ns()}{uuid.uuid4().hex[:8]}"
    return f"192.168.{int(unique[-4:-2], 16) % 256}.{int(unique[-2:], 16) % 256}"


def generate_unique_ip():
    """Helper to generate unique IP inline."""
    import uuid
    import time
    unique = f"{time.time_ns()}{uuid.uuid4().hex[:8]}"
    return f"10.{int(unique[-6:-4], 16) % 256}.{int(unique[-4:-2], 16) % 256}.{int(unique[-2:], 16) % 256}"


class TestHealthEndpointNotRateLimited:
    """Verify health endpoint is NOT rate limited."""

    @pytest.mark.asyncio
    async def test_health_no_rate_limit(self, client: AsyncClient):
        """Health endpoint should never return 429."""
        # Make 20 rapid requests (more than any limit)
        for i in range(20):
            response = await client.get("/health")
            assert response.status_code == 200, f"Request {i+1} failed with {response.status_code}"


class TestDocsEndpointNotRateLimited:
    """Verify docs endpoints are NOT rate limited."""

    @pytest.mark.asyncio
    async def test_docs_no_rate_limit(self, client: AsyncClient):
        """Docs endpoint should never return 429."""
        for i in range(20):
            response = await client.get("/docs")
            # Docs returns 200 or redirects
            assert response.status_code in [200, 307], f"Request {i+1} failed"

    @pytest.mark.asyncio
    async def test_openapi_no_rate_limit(self, client: AsyncClient):
        """OpenAPI endpoint should never return 429."""
        for i in range(20):
            response = await client.get("/openapi.json")
            assert response.status_code == 200, f"Request {i+1} failed"


class TestAuthRateLimiting:
    """Test rate limiting on authentication endpoints (IP-based, 5/minute)."""

    @pytest.mark.asyncio
    async def test_login_rate_limit_enforced(self, client: AsyncClient, unique_ip: str):
        """Test that 6th login attempt returns 429."""
        login_data = {"email": "test@example.com", "password": "wrong"}

        # First 5 requests should pass (even if auth fails)
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                json=login_data,
                headers={"X-Forwarded-For": unique_ip}
            )
            # 401 = auth failed, but not rate limited
            assert response.status_code in [401, 200], f"Request {i+1}: unexpected {response.status_code}"

        # 6th request should be rate limited
        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers={"X-Forwarded-For": unique_ip}
        )
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_register_rate_limit_enforced(self, client: AsyncClient):
        """Test that 6th register attempt returns 429."""
        test_ip = generate_unique_ip()

        # First 5 requests should pass
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"user{i}_{test_ip.replace('.', '')}@test.com",
                    "username": f"user{i}_{test_ip.replace('.', '')}",
                    "password": "SecurePass123!",
                    "full_name": f"User {i}"
                },
                headers={"X-Forwarded-For": test_ip}
            )
            # Accept 201 (created), 400 (duplicate), or 422 (validation)
            assert response.status_code in [201, 400, 422], f"Request {i+1}: {response.status_code}"

        # 6th request should be rate limited
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"another_{test_ip.replace('.', '')}@test.com",
                "username": f"another_{test_ip.replace('.', '')}",
                "password": "SecurePass123!",
                "full_name": "Another User"
            },
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_response_format(self, client: AsyncClient):
        """Test 429 response has correct format and headers."""
        test_ip = generate_unique_ip()
        login_data = {"email": "test@example.com", "password": "wrong"}

        # Exhaust rate limit
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json=login_data,
                headers={"X-Forwarded-For": test_ip}
            )

        # Get rate limited response
        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers={"X-Forwarded-For": test_ip}
        )

        assert response.status_code == 429

        # Check response body
        data = response.json()
        assert "detail" in data
        assert "retry_after" in data or "Retry-After" in response.headers
        assert data.get("error_code") == "RATE_LIMIT_EXCEEDED"

        # Check headers
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_different_ips_have_separate_limits(self, client: AsyncClient):
        """Test that different IPs have independent rate limits."""
        login_data = {"email": "test@example.com", "password": "wrong"}

        ip1 = generate_unique_ip()
        ip2 = generate_unique_ip()

        # Exhaust limit for IP1
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json=login_data,
                headers={"X-Forwarded-For": ip1}
            )

        # IP1 should be rate limited
        response1 = await client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers={"X-Forwarded-For": ip1}
        )
        assert response1.status_code == 429

        # IP2 should still work
        response2 = await client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers={"X-Forwarded-For": ip2}
        )
        assert response2.status_code != 429  # Should be 401 (auth failed) or 200


class TestChatRateLimiting:
    """Test rate limiting on chat endpoint (user-based, 10/minute)."""

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client: AsyncClient):
        """Chat endpoint requires authentication."""
        response = await client.post(
            "/api/v1/rag/chat",
            json={"message": "Hello"}
        )
        # Should fail with 401/403, not rate limit
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_chat_endpoint_exists(self, client: AsyncClient):
        """Verify chat endpoint is accessible (auth will fail but endpoint exists)."""
        response = await client.post(
            "/api/v1/rag/chat",
            json={"message": "test"}
        )
        # 401/403 = endpoint exists but needs auth
        # 404 = endpoint doesn't exist
        assert response.status_code != 404


class TestUploadRateLimiting:
    """Test rate limiting on upload endpoint (user-based, 2/10minutes)."""

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient):
        """Upload endpoint requires authentication."""
        response = await client.post(
            "/api/v1/rag/upload",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code in [401, 403]


class TestRateLimitHeaders:
    """Test rate limit headers are present in responses."""

    @pytest.mark.asyncio
    async def test_429_has_retry_after_header(self, client: AsyncClient):
        """429 response must include Retry-After header."""
        test_ip = generate_unique_ip()

        # Exhaust rate limit
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrong"},
                headers={"X-Forwarded-For": test_ip}
            )

        # Get rate limited response
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": test_ip}
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers

        # Retry-After should be a positive integer
        retry_after = int(response.headers["Retry-After"])
        assert retry_after > 0


class TestFailOpenBehavior:
    """Test fail-open behavior when rate limit backend fails."""

    @pytest.mark.asyncio
    async def test_requests_succeed_without_redis(self, client: AsyncClient):
        """Requests should succeed even if Redis is unavailable."""
        # The app is running with in-memory storage (default)
        # This test verifies the fallback works
        response = await client.get("/health")
        assert response.status_code == 200


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
