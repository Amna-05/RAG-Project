"""
Integration tests for LLM graceful degradation and fallback.
File: tests/integration/test_graceful_degradation.py

Tests:
- Provider fallback when primary fails
- Retry logic for transient failures
- Fallback order: Grok → Gemini → Claude → OpenAI → Ollama
- All providers fail graceful error handling
"""
import pytest
from unittest.mock import patch, MagicMock, call
from rag.services.llm_service import LLMService, LLMProvider


class TestLLMServiceInitialization:
    """Test LLM service initialization with different provider configurations."""

    def test_provider_priority_order_grok_first(self):
        """Test that Grok is prioritized as first fallback."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            # Configure with Grok and Gemini
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = "gemini-key"
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            # Verify priority: Grok first, then Gemini
            assert service.providers[0] == LLMProvider.GROK
            assert service.providers[1] == LLMProvider.GEMINI

    def test_provider_priority_gemini_when_grok_unavailable(self):
        """Test that Gemini is fallback when Grok unavailable."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            # Configure without Grok, with Gemini
            mock_settings.xai_api_key = None
            mock_settings.google_api_key = "gemini-key"
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            # Verify Gemini is first
            assert service.providers[0] == LLMProvider.GEMINI

    def test_default_provider_priority_order(self):
        """Test the default provider priority order matches specification."""
        expected_order = [
            LLMProvider.GROK,
            LLMProvider.GEMINI,
            LLMProvider.CLAUDE,
            LLMProvider.OPENAI,
            LLMProvider.OLLAMA,
        ]
        assert LLMService.DEFAULT_PROVIDER_PRIORITY == expected_order


class TestLLMServiceFallback:
    """Test automatic fallback when providers fail."""

    @pytest.mark.asyncio
    async def test_fallback_from_grok_to_gemini(self):
        """Test fallback from Grok to Gemini when Grok fails."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            # Configure both providers
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = "gemini-key"
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            with patch.object(service, '_call_grok') as mock_grok, \
                 patch.object(service, '_call_gemini') as mock_gemini:

                # Grok fails, Gemini succeeds
                mock_grok.side_effect = Exception("Grok API error")
                mock_gemini.return_value = {
                    "answer": "Here's the answer from Gemini",
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "success": True,
                    "error": None
                }

                result = service.generate_answer("What is AI?")

                # Verify Grok was tried first
                assert mock_grok.called
                # Verify Gemini was tried as fallback
                assert mock_gemini.called
                # Verify success
                assert result["success"]
                assert result["provider"] == "gemini"
                assert "Gemini" in result["answer"]

    @pytest.mark.asyncio
    async def test_all_providers_fail_graceful_error(self):
        """Test graceful error when all providers fail."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            # Configure with only two providers
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = "gemini-key"
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            with patch.object(service, '_call_grok') as mock_grok, \
                 patch.object(service, '_call_gemini') as mock_gemini:

                # Both fail
                mock_grok.side_effect = Exception("Grok API error")
                mock_gemini.side_effect = Exception("Gemini API error")

                result = service.generate_answer("What is AI?")

                # Verify failure
                assert not result["success"]
                assert result["provider"] == "none"
                assert "I apologize" in result["answer"]
                assert "unavailable" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_retry_logic_with_transient_failure(self):
        """Test that retry logic handles transient failures."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            with patch.object(service, '_call_grok') as mock_grok, \
                 patch('time.sleep'):  # Mock sleep to speed up test

                # First call fails, second succeeds
                mock_grok.side_effect = [
                    {
                        "answer": "",
                        "provider": "grok",
                        "model": "",
                        "success": False,
                        "error": "Transient API error"
                    },
                    {
                        "answer": "Success on retry",
                        "provider": "grok",
                        "model": "grok-3",
                        "success": True,
                        "error": None
                    }
                ]

                result = service.generate_answer("What is AI?")

                # Verify retry was attempted (called twice)
                assert mock_grok.call_count == 2
                # Verify eventual success
                assert result["success"]
                assert "Success on retry" in result["answer"]

    @pytest.mark.asyncio
    async def test_last_successful_provider_preference(self):
        """Test that last successful provider is tried first on next call."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = "gemini-key"
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            with patch.object(service, '_call_grok') as mock_grok, \
                 patch.object(service, '_call_gemini') as mock_gemini:

                # First call: Grok fails, Gemini succeeds
                mock_grok.side_effect = Exception("Grok error")
                mock_gemini.return_value = {
                    "answer": "Answer from Gemini",
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "success": True,
                    "error": None
                }

                result1 = service.generate_answer("First question?")
                assert result1["provider"] == "gemini"
                assert service.last_successful_provider == LLMProvider.GEMINI

                # Reset mocks
                mock_grok.reset_mock()
                mock_gemini.reset_mock()

                # Second call: Gemini should be tried first
                mock_gemini.return_value = {
                    "answer": "Answer from Gemini again",
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "success": True,
                    "error": None
                }

                result2 = service.generate_answer("Second question?")

                # Verify Gemini was called (as last successful)
                assert mock_gemini.called
                # Verify Grok was NOT called (since Gemini succeeded)
                assert not mock_grok.called


class TestLLMServiceErrorHandling:
    """Test error handling and error messages."""

    @pytest.mark.asyncio
    async def test_error_message_includes_attempt_count(self):
        """Test that error messages include attempt information."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            mock_settings.xai_api_key = "grok-key"
            mock_settings.google_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            with patch.object(service, '_call_grok') as mock_grok:
                # All retries fail
                mock_grok.side_effect = Exception("API Rate Limited")

                result = service.generate_answer("Test?")

                # Verify error includes attempt info
                assert not result["success"]
                assert "retry" in result["error"].lower() or "attempt" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_no_providers_configured_error(self):
        """Test error when no providers are configured."""
        with patch('rag.services.llm_service.settings') as mock_settings:
            # No providers configured
            mock_settings.xai_api_key = None
            mock_settings.google_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.use_ollama = False

            service = LLMService()

            # Should have no providers
            assert len(service.providers) == 0

            result = service.generate_answer("Test?")

            # Should gracefully return error
            assert not result["success"]
            assert result["provider"] == "none"
