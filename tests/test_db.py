# test_db.py
from rag.core.config import get_settings

settings = get_settings()
print(f"Database URL: {settings.database_url}")