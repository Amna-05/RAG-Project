# In Python console or create a test file
import asyncio
from sqlalchemy import select
from rag.core.database import get_db
from rag.models.user import User

async def check_user():
    async for db in get_db():
        result = await db.execute(select(User).order_by(User.created_at.desc()).limit(1))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Latest User Found:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Password Hash (first 20 chars): {user.hashed_password[:20]}...")
            print(f"   Is Active: {user.is_active}")
            print(f"   Last Login: {user.last_login}")
        else:
            print("❌ No users found")
        break

asyncio.run(check_user())