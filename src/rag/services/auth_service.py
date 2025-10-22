"""
Authentication service - business logic for auth operations.
File: src/rag/services/auth_service.py

PURPOSE:
Orchestrates auth workflows by combining CRUD + Core utilities.

WHY THIS LAYER:
- API layer should be thin (just HTTP handling)
- Business logic isolated for testing
- Multiple endpoints can reuse same logic

WHAT IT DOES:
- authenticate_user(): Login flow
- register_new_user(): Registration flow  
- refresh_tokens(): Token refresh flow
"""
from typing import Optional, Tuple
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.user import User
from rag.schemas.user import UserCreate
from rag.schemas.auth import Token
from rag.crud import user as user_crud
from rag.crud import token as token_crud
from rag.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)
from rag.core.config import get_settings

settings = get_settings()



async def authenticate_user(
    db: AsyncSession,
    email: str,  # ← Changed from username to email
    password: str
) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    FLOW:
    1. Find user by email
    2. Verify password
    3. Return user if valid, None if invalid
    
    Args:
        email: User's email address
        password: Plain text password to verify
        
    Returns:
        User object if credentials valid, None otherwise
    """
    # Find user by email
    user = await user_crud.get_user_by_email(db, email)
    
    if not user:
        # User doesn't exist
        return None
    
    # Verify password using bcrypt
    if not verify_password(password, user.hashed_password):
        # Wrong password
        return None
    
    # Check if user account is active
    if not user.is_active:
        return None
    
    return user

async def create_user_tokens(
    db: AsyncSession,
    user: User,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Token:
    """
    Create access + refresh tokens for user.
    
    FLOW:
    1. Generate JWT access token (30 mins)
    2. Generate JWT refresh token (7 days)
    3. Save refresh token to database
    4. Return both tokens
    
    WHY SEPARATE FUNCTION:
    - Used in login
    - Used in token refresh
    - Used in email verification (future)
    
    Args:
        user: User object to create tokens for
        device_info: Optional device/browser info
        ip_address: Optional IP address
        
    Returns:
        Token object with access_token and refresh_token
    """
    # Create access token (short-lived)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # Create refresh token (long-lived)
    refresh_token_str = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    # Save refresh token to database for tracking
    await token_crud.create_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token_str,
        device_info=device_info,
        ip_address=ip_address
    )
    
    # Update user's last login timestamp
    await user_crud.update_last_login(db, user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
    )


async def register_new_user(
    db: AsyncSession,
    user_data: UserCreate
) -> Tuple[User, Token]:
    """
    Register a new user and return tokens.
    
    FLOW:
    1. Check if email/username already exists
    2. Create user in database (password auto-hashed in CRUD)
    3. Generate tokens for immediate login
    4. Return user + tokens
    
    WHY SEPARATE FUNCTION:
    - Complex validation logic
    - Multiple database operations
    - Immediate login after registration
    
    Returns:
        Tuple of (User, Token)
        
    Raises:
        ValueError: If email/username already exists
    """
    # Check if email already registered
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError("Email already registered")
    
    # Check if username already taken
    existing_user = await user_crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise ValueError("Username already taken")
    
    # Create user (password hashing happens in CRUD layer)
    user = await user_crud.create_user(db, user_data)
    
    # Generate tokens for immediate login
    tokens = await create_user_tokens(db, user)
    
    return user, tokens


async def refresh_user_tokens(
    db: AsyncSession,
    refresh_token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Optional[Token]:
    """
    Refresh access token using refresh token.
    
    FLOW:
    1. Decode refresh token
    2. Verify token exists in database and not revoked
    3. Get user from token
    4. Generate new access token
    5. Optionally rotate refresh token (more secure)
    6. Return new tokens
    
    WHY THIS MATTERS:
    - User stays logged in without re-entering password
    - Frontend auto-refreshes before access token expires
    
    Args:
        refresh_token: JWT refresh token string
        device_info: Optional device info
        ip_address: Optional IP
        
    Returns:
        New Token object or None if invalid
    """
    # Decode and verify refresh token
    payload = decode_refresh_token(refresh_token)
    
    if not payload:
        return None
    
    # Check if token exists in database and is valid
    db_token = await token_crud.get_refresh_token(db, refresh_token)
    
    if not db_token or not db_token.is_valid:
        return None
    
    # Get user from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    
    user = await user_crud.get_user_by_id(db, UUID(user_id_str))
    
    if not user or not user.is_active:
        return None
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # SECURITY: Optional token rotation (issue new refresh token)
    # For now, we reuse the same refresh token
    # In high-security apps, you'd revoke old and issue new refresh token
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,  # Reuse existing
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


async def logout_user(
    db: AsyncSession,
    refresh_token: str
) -> bool:
    """
    Logout user by revoking refresh token.
    
    FLOW:
    1. Find token in database
    2. Mark as revoked
    3. Token cannot be used again
    
    Returns:
        True if successful, False otherwise
    """
    return await token_crud.revoke_token(db, refresh_token)


async def logout_all_sessions(
    db: AsyncSession,
    user_id: UUID
) -> int:
    """
    Logout user from all devices.
    
    FLOW:
    1. Find all user's refresh tokens
    2. Revoke all of them
    3. User must login again on all devices
    
    Returns:
        Number of tokens revoked
    """
    return await token_crud.revoke_all_user_tokens(db, user_id)