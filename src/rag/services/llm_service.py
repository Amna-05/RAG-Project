"""
Multi-LLM service with automatic fallback.
Supports: OpenAI, Google Gemini, Anthropic Claude, xAI Grok, Local Ollama.

Features:
- Configurable provider priority order (default: Grok → Gemini → Claude → OpenAI)
- Automatic retry logic for transient failures
- Graceful degradation across multiple providers
- Request tracing and detailed error logging
"""
import logging
import time
from typing import Optional, List, Dict, Any
from enum import Enum

from rag.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    GROK = "grok"
    OLLAMA = "ollama"


class LLMService:
    """
    Unified LLM service with automatic fallback and retry logic.

    Provider priority (default): Grok → Gemini → Claude → OpenAI → Ollama
    This prioritizes free-trial providers (Grok and Gemini).
    """

    # Default provider priority order (free trial providers first)
    DEFAULT_PROVIDER_PRIORITY = [
        LLMProvider.GROK,      # xAI - free trial available
        LLMProvider.GEMINI,    # Google - free tier available
        LLMProvider.CLAUDE,    # Anthropic
        LLMProvider.OPENAI,    # OpenAI
        LLMProvider.OLLAMA,    # Local fallback
    ]

    # Retry configuration
    MAX_RETRIES = 2  # Total attempts = 1 + MAX_RETRIES
    RETRY_DELAY_SECONDS = 1  # Delay between retries

    def __init__(self):
        """Initialize LLM service."""
        self.providers = self._initialize_providers()
        self.last_successful_provider: Optional[LLMProvider] = None
        logger.info(f"📊 LLM Service initialized with providers: {[p.value for p in self.providers]}")
        logger.info(f"🎯 Provider priority order: {' → '.join([p.value for p in self.DEFAULT_PROVIDER_PRIORITY if p in self.providers])}")
    
    def _initialize_providers(self) -> List[LLMProvider]:
        """
        Determine which providers are available based on API keys.
        Returns list in priority order (Grok → Gemini → Claude → OpenAI → Ollama).
        """
        available = {}

        # Check each provider for API key/configuration
        if settings.xai_api_key:
            available[LLMProvider.GROK] = True
            logger.info("✅ Grok available (xAI Grok API)")

        if settings.google_api_key:
            available[LLMProvider.GEMINI] = True
            logger.info("✅ Gemini available (Google Gemini API)")

        if settings.anthropic_api_key:
            available[LLMProvider.CLAUDE] = True
            logger.info("✅ Claude available (Anthropic API)")

        if settings.openai_api_key:
            available[LLMProvider.OPENAI] = True
            logger.info("✅ OpenAI available (OpenAI API)")

        if settings.use_ollama:
            available[LLMProvider.OLLAMA] = True
            logger.info("✅ Ollama available (Local deployment)")

        if not available:
            logger.warning("⚠️ No LLM providers configured! Add API keys to .env")

        # Return providers in priority order
        sorted_providers = [p for p in self.DEFAULT_PROVIDER_PRIORITY if p in available]
        return sorted_providers
    
    def generate_answer(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate answer using available LLM with automatic fallback and retry logic.

        Strategy:
        1. Try last successful provider first (with retries)
        2. Fall back to next providers in priority order (each with retries)
        3. If all fail, return graceful error message

        Returns:
            {
                "answer": str,
                "provider": str,
                "model": str,
                "success": bool,
                "error": Optional[str],
                "attempt": int  # Which attempt this was (1, 2, 3, etc)
            }
        """
        logger.info(f"🚀 Generating answer (attempt {retry_count + 1}/{self.MAX_RETRIES + 1})")

        # Try last successful provider first (with retries)
        if self.last_successful_provider and self.last_successful_provider in self.providers:
            logger.info(f"🎯 Trying last successful provider: {self.last_successful_provider.value}")
            for attempt in range(self.MAX_RETRIES + 1):
                result = self._try_provider(
                    self.last_successful_provider,
                    prompt,
                    max_tokens,
                    temperature,
                    attempt
                )
                if result["success"]:
                    return result

                if attempt < self.MAX_RETRIES:
                    logger.info(f"⏳ Retrying {self.last_successful_provider.value} in {self.RETRY_DELAY_SECONDS}s...")
                    time.sleep(self.RETRY_DELAY_SECONDS)

        # Try all other providers in priority order (with retries)
        for provider in self.providers:
            if provider == self.last_successful_provider:
                continue  # Already tried

            logger.info(f"🔄 Trying {provider.value}... (fallback)")
            for attempt in range(self.MAX_RETRIES + 1):
                result = self._try_provider(provider, prompt, max_tokens, temperature, attempt)

                if result["success"]:
                    self.last_successful_provider = provider
                    logger.info(f"✅ Success with {provider.value}")
                    return result

                if attempt < self.MAX_RETRIES:
                    logger.info(f"⏳ Retrying {provider.value} in {self.RETRY_DELAY_SECONDS}s...")
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    logger.warning(f"❌ {provider.value} exhausted all retries: {result['error']}")

        # All providers and retries failed - graceful degradation
        logger.error("💥 All LLM providers failed after retries")
        return {
            "answer": (
                "I apologize, but I'm currently unable to generate a response. "
                "All AI providers are unavailable. Please try again later."
            ),
            "provider": "none",
            "model": "none",
            "success": False,
            "error": "All LLM providers failed after retries",
            "attempt": retry_count + 1
        }
    
    def _try_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        max_tokens: int,
        temperature: float,
        attempt: int = 0
    ) -> Dict[str, Any]:
        """
        Try a specific provider.

        Args:
            provider: Which LLM provider to try
            prompt: The prompt to send
            max_tokens: Max tokens in response
            temperature: Response temperature (0-1)
            attempt: Which attempt this is (0, 1, 2, etc)

        Returns:
            Result dict with answer, provider, model, success, and error
        """
        try:
            if provider == LLMProvider.OPENAI:
                return self._call_openai(prompt, max_tokens, temperature)
            elif provider == LLMProvider.GEMINI:
                return self._call_gemini(prompt, max_tokens, temperature)
            elif provider == LLMProvider.CLAUDE:
                return self._call_claude(prompt, max_tokens, temperature)
            elif provider == LLMProvider.GROK:
                return self._call_grok(prompt, max_tokens, temperature)
            elif provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt, max_tokens, temperature)
        except Exception as e:
            error_msg = f"{provider.value} error (attempt {attempt + 1}): {str(e)}"
            logger.error(error_msg)
            return {
                "answer": "",
                "provider": provider.value,
                "model": "",
                "success": False,
                "error": error_msg
            }
    
    def _call_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call OpenAI GPT API."""
        import openai
        
        openai.api_key = settings.openai_api_key
        
        response = openai.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "provider": "openai",
            "model": settings.openai_model,
            "success": True,
            "error": None
        }
    
    def _call_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call Google Gemini API."""
        import google.generativeai as genai
        
        genai.configure(api_key=settings.google_api_key)
        
        model = genai.GenerativeModel(
            settings.gemini_model,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        response = model.generate_content(prompt)
        
        return {
            "answer": response.text,
            "provider": "gemini",
            "model": settings.gemini_model,
            "success": True,
            "error": None
        }
    
    def _call_claude(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        answer = response.content[0].text
        
        return {
            "answer": answer,
            "provider": "claude",
            "model": settings.claude_model,
            "success": True,
            "error": None
        }
    
    def _call_grok(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call xAI Grok API (OpenAI-compatible endpoint)."""
        import openai

        client = openai.OpenAI(
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1"
        )

        response = client.chat.completions.create(
            model=settings.grok_model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "provider": "grok",
            "model": settings.grok_model,
            "success": True,
            "error": None
        }

    def _call_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call local Ollama API."""
        import requests

        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        return {
            "answer": result["response"],
            "provider": "ollama",
            "model": settings.ollama_model,
            "success": True,
            "error": None
        }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def generate_answer(prompt: str, **kwargs) -> str:
    """
    Convenience function to generate answer.
    
    Args:
        prompt: The prompt to send
        **kwargs: Additional arguments (max_tokens, temperature)
        
    Returns:
        Generated answer as string
    """
    service = get_llm_service()
    result = service.generate_answer(prompt, **kwargs)
    return result["answer"]