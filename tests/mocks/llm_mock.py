"""
Mock LLM provider implementation for testing.
File: tests/mocks/llm_mock.py
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class MockLLMResponse:
    """Mock LLM response."""
    text: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class MockLLMProvider:
    """
    Mock LLM provider for testing.

    Simulates LLM responses without making actual API calls.
    Can be configured to fail for testing error handling.
    """

    def __init__(
        self,
        default_response: str = "This is a mock response based on the provided context.",
        should_fail: bool = False,
        fail_count: int = 0,
        model_name: str = "mock-model"
    ):
        self.default_response = default_response
        self.should_fail = should_fail
        self.fail_count = fail_count
        self.model_name = model_name
        self.call_count = 0
        self.calls: List[Dict[str, Any]] = []

    async def generate(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> MockLLMResponse:
        """Generate a mock response."""
        self.call_count += 1
        self.calls.append({
            "prompt": prompt,
            "context": context,
            "max_tokens": max_tokens,
            "temperature": temperature
        })

        # Simulate failures if configured
        if self.should_fail:
            if self.fail_count == 0 or self.call_count <= self.fail_count:
                raise Exception("Mock LLM failure for testing")

        # Generate response based on context
        if context:
            response_text = f"Based on the provided context: {context[0][:100]}..."
        else:
            response_text = self.default_response

        return MockLLMResponse(
            text=response_text,
            model=self.model_name,
            tokens_used=len(prompt.split()) + len(response_text.split())
        )

    def reset(self):
        """Reset call tracking."""
        self.call_count = 0
        self.calls = []

    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last call made to the provider."""
        return self.calls[-1] if self.calls else None


class MockGeminiProvider(MockLLMProvider):
    """Mock Google Gemini provider."""

    def __init__(self, **kwargs):
        super().__init__(model_name="gemini-pro", **kwargs)


class MockOpenAIProvider(MockLLMProvider):
    """Mock OpenAI provider (fallback)."""

    def __init__(self, **kwargs):
        super().__init__(model_name="gpt-4", **kwargs)


class MockLLMWithFallback:
    """
    Mock LLM service with fallback support.

    Used to test graceful degradation scenarios.
    """

    def __init__(
        self,
        primary: MockLLMProvider,
        fallback: Optional[MockLLMProvider] = None
    ):
        self.primary = primary
        self.fallback = fallback
        self.primary_attempts = 0
        self.fallback_used = False

    async def generate(self, prompt: str, **kwargs) -> MockLLMResponse:
        """Generate with fallback support."""
        try:
            self.primary_attempts += 1
            return await self.primary.generate(prompt, **kwargs)
        except Exception as e:
            if self.fallback:
                self.fallback_used = True
                return await self.fallback.generate(prompt, **kwargs)
            raise e

    def reset(self):
        """Reset state."""
        self.primary.reset()
        if self.fallback:
            self.fallback.reset()
        self.primary_attempts = 0
        self.fallback_used = False
