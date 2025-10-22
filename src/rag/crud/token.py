"""
Refresh Token CRUD operations.
File: src/rag/crud/token.py

PURPOSE:
- Manage refresh tokens in database
- Track token usage and revocation

WHY STORE REFRESH TOKENS:
- Can revoke tokens (logout from all devices)
- Track login sessions
- Security: detect stolen tokens
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.token import RefreshToken
from rag.core.config import get_settings

settings = get_settings()


async def create_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
) -> RefreshToken:
    """
    Create and store refresh token in database.
    
    Args:
        user_id: User who owns this token
        token: JWT refresh token string
        device_info: Optional device/browser info
        ip_address: Optional IP address
        
    Returns:
        RefreshToken object
    """
    expires_at = datetime.utcnow() + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    db_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        #device_info=device_info,
        #ip_address=ip_address,
    )
    
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    
    return db_token


async def get_refresh_token(
    db: AsyncSession, 
    token: str
) -> Optional[RefreshToken]:
    """
    Get refresh token by token string.
    
    Used during token refresh to validate.
    """
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    return result.scalar_one_or_none()


async def get_user_tokens(
    db: AsyncSession,
    user_id: UUID,
    include_revoked: bool = False
) -> List[RefreshToken]:
    """
    Get all refresh tokens for a user.
    
    Used to show "active sessions" to user.
    """
    query = select(RefreshToken).where(RefreshToken.user_id == user_id)
    
    if not include_revoked:
        query = query.where(RefreshToken.is_revoked == False)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def revoke_token(db: AsyncSession, token: str) -> bool:
    """
    Revoke (invalidate) a refresh token.
    
    Used for logout - token cannot be used again.
    """
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token == token)
        .values(
            is_revoked=True,
            revoked_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    return result.rowcount > 0


async def revoke_all_user_tokens(db: AsyncSession, user_id: UUID) -> int:
    """
    Revoke all refresh tokens for a user.
    
    Used for "logout from all devices" feature.
    """
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.is_revoked == False)
        .values(
            is_revoked=True,
            revoked_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    return result.rowcount


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Delete expired refresh tokens from database.
    
    Run this periodically (e.g., daily cron job) to clean up.
    """
    from sqlalchemy import delete
    
    result = await db.execute(
        delete(RefreshToken)
        .where(RefreshToken.expires_at < datetime.utcnow())
    )
    await db.commit()
    
    return result.rowcount


async def is_token_valid(db: AsyncSession, token: str) -> bool:
    """
    Check if refresh token is valid.
    
    Valid means: exists, not revoked, not expired.
    """
    db_token = await get_refresh_token(db, token)
    
    if not db_token:
        return False
    
    return db_token.is_valid