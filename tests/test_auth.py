"""
Authentication endpoint tests.
File: tests/test_auth.py

Run with: pytest tests/test_auth.py -v
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from rag.main import app
from rag.core.database import get_db


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123",
        "full_name": "Test User"
    }


class TestHealthCheck:
    """Test health check endpoint."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test /health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRegistration:
    """Test user registration."""
    
    async def test_register_new_user(self, client: AsyncClient, test_user_data):
        """Test successful registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email."""
        # Register first time
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register again
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_invalid_email(self, client: AsyncClient, test_user_data):
        """Test registration with invalid email."""
        test_user_data["email"] = "not-an-email"
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422  # Validation error
    
    async def test_register_weak_password(self, client: AsyncClient, test_user_data):
        """Test registration with weak password."""
        test_user_data["password"] = "123"  # Too short
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422


class TestLogin:
    """Test login functionality."""
    
    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        response = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        """Test login with wrong password."""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        })
        assert response.status_code == 401
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "SomePassword123"
        })
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test protected endpoints."""
    
    async def test_get_profile_without_token(self, client: AsyncClient):
        """Test accessing profile without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403  # Forbidden
    
    async def test_get_profile_with_invalid_token(self, client: AsyncClient):
        """Test accessing profile with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    async def test_get_profile_success(self, client: AsyncClient, test_user_data):
        """Test accessing profile with valid token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get profile
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]


class TestTokenRefresh:
    """Test token refresh functionality."""
    
    async def test_refresh_token_success(self, client: AsyncClient, test_user_data):
        """Test successful token refresh."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401