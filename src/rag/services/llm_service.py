"""
Multi-LLM service with automatic fallback.
Supports: OpenAI, Google Gemini, Anthropic Claude, Local Ollama.
"""
import logging
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
    OLLAMA = "ollama"


class LLMService:
    """Unified LLM service with automatic fallback."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.providers = self._initialize_providers()
        self.last_successful_provider: Optional[LLMProvider] = None
    
    def _initialize_providers(self) -> List[LLMProvider]:
        """
        Determine which providers are available based on API keys.
        Returns list in priority order.
        """
        available = []
        
        # Check OpenAI
        if settings.openai_api_key:
            available.append(LLMProvider.OPENAI)
            logger.info("✅ OpenAI available")
        
        # Check Gemini
        if settings.google_api_key:
            available.append(LLMProvider.GEMINI)
            logger.info("✅ Gemini available")
        
        # Check Claude
        if settings.anthropic_api_key:
            available.append(LLMProvider.CLAUDE)
            logger.info("✅ Claude available")
        
        # Check Ollama (local, always available if running)
        if settings.use_ollama:
            available.append(LLMProvider.OLLAMA)
            logger.info("✅ Ollama available")
        
        if not available:
            logger.warning("⚠️ No LLM providers configured!")
        
        return available
    
    def generate_answer(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate answer using available LLM with automatic fallback.
        
        Returns:
            {
                "answer": str,
                "provider": str,
                "model": str,
                "success": bool,
                "error": Optional[str]
            }
        """
        # Try last successful provider first
        if self.last_successful_provider:
            result = self._try_provider(
                self.last_successful_provider,
                prompt,
                max_tokens,
                temperature
            )
            if result["success"]:
                return result
        
        # Try all providers in order
        for provider in self.providers:
            if provider == self.last_successful_provider:
                continue  # Already tried
            
            logger.info(f"🔄 Trying {provider.value}...")
            result = self._try_provider(provider, prompt, max_tokens, temperature)
            
            if result["success"]:
                self.last_successful_provider = provider
                return result
            else:
                logger.warning(f"❌ {provider.value} failed: {result['error']}")
        
        # All providers failed
        return {
            "answer": (
                "I apologize, but I'm currently unable to generate a response. "
                "All AI providers are unavailable. Please try again later."
            ),
            "provider": "none",
            "model": "none",
            "success": False,
            "error": "All LLM providers failed"
        }
    
    def _try_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Try a specific provider."""
        try:
            if provider == LLMProvider.OPENAI:
                return self._call_openai(prompt, max_tokens, temperature)
            elif provider == LLMProvider.GEMINI:
                return self._call_gemini(prompt, max_tokens, temperature)
            elif provider == LLMProvider.CLAUDE:
                return self._call_claude(prompt, max_tokens, temperature)
            elif provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"{provider.value} error: {e}")
            return {
                "answer": "",
                "provider": provider.value,
                "model": "",
                "success": False,
                "error": str(e)
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