"""
User CRUD (Create, Read, Update, Delete) operations.
File: src/rag/crud/user.py

PURPOSE:
- All database operations for User model
- Keeps DB queries separate from API logic

WHY CRUD PATTERN:
- Reusable: Multiple endpoints can use same query
- Testable: Easy to unit test DB operations
- Maintainable: Change query in one place
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.user import User
from rag.schemas.user import UserCreate, UserUpdate
from rag.core.security import get_password_hash


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.
    
    Returns: User object or None if not found
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Used during login to find user.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Used during login and to check if username exists.
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create new user.
    
    Steps:
    1. Hash the password (never store plain text!)
    2. Create User object
    3. Add to database
    4. Return created user
    """
    # Hash password using bcrypt
    hashed_password = get_password_hash(user_data.password[:72])
    
    # Create user instance
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,  # Email verification can be added later
    )
    
    # Add to database
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)  # Load the generated fields (id, created_at, etc.)
    
    return db_user


async def update_user(
    db: AsyncSession, 
    user_id: UUID, 
    user_data: UserUpdate
) -> Optional[User]:
    """
    Update user profile.
    
    Only updates fields that are provided (not None).
    """
    # Build update dictionary (only non-None values)
    update_data = user_data.model_dump(exclude_unset=True)
    
    if not update_data:
        # Nothing to update
        return await get_user_by_id(db, user_id)
    
    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Execute update
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(**update_data)
    )
    await db.commit()
    
    # Return updated user
    return await get_user_by_id(db, user_id)


async def update_last_login(db: AsyncSession, user_id: UUID) -> None:
    """
    Update user's last login timestamp.
    
    Called after successful login.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_login=datetime.utcnow())
    )
    await db.commit()


async def increment_document_count(db: AsyncSession, user_id: UUID) -> None:
    """
    Increment user's document counter.
    
    Called after successful document upload.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(document_count=User.document_count + 1)
    )
    await db.commit()


async def increment_query_count(db: AsyncSession, user_id: UUID) -> None:
    """
    Increment user's query counter.
    
    Called after each query.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(query_count=User.query_count + 1)
    )
    await db.commit()


async def deactivate_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Deactivate user account (soft delete).
    
    User can be reactivated later.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=False)
    )
    await db.commit()
    
    return await get_user_by_id(db, user_id)


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """
    Permanently delete user (hard delete).
    
    Use with caution! This deletes all user data.
    In production, you'd also need to:
    - Delete user's documents from Pinecone
    - Delete uploaded files
    - Clean up related records
    """
    user = await get_user_by_id(db, user_id)
    
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    
    return True