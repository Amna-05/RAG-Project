import google.generativeai as genai
from rag.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)

# Test available models
for model in genai.list_models():
    print(f"✅ Available: {model.name}")

    