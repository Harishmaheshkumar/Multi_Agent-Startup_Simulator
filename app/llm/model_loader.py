"""
Model loader for managing different LLM providers.
"""

import asyncio
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from ..utils.config import config
from ..utils.logger import LoggerMixin


class BaseModelProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate a response from the model."""
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """Check if the model provider is available."""
        pass


class OllamaProvider(BaseModelProvider, LoggerMixin):
    """Ollama model provider."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        super().__init__(base_url=base_url)
        self.client = None
        self.default_model = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Ollama client."""
        try:
            import ollama
            self.client = ollama.Client(host=self.base_url)
            self.default_model = self._select_default_model()
        except ImportError:
            self.logger.warning("Ollama package not installed")
            self.client = None
            self.default_model = None

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Ollama."""
        if not self.client:
            return "Ollama client not available"

        model = model or self.default_model or "llama2"

        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)

            # If no model specified, try to pick a sensible default from the client
            if not model:
                model = self.default_model
                if not model:
                    try:
                        models = self.client.list()
                        model_list = models.get("models") if hasattr(models, "get") else models
                        if model_list:
                            first = model_list[0]
                            if isinstance(first, str):
                                model = first
                            elif isinstance(first, dict):
                                model = first.get("name") or first.get("id")
                    except Exception:
                        model = None

            if not model:
                model = "llama2"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate(
                    model=model,
                    prompt=full_prompt,
                    options={
                        "temperature": kwargs.get("temperature", config.temperature),
                        "num_predict": kwargs.get("max_tokens", config.max_tokens),
                    }
                )
            )

            return response.get("response", "")
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            return f"Error generating response: {str(e)}"

    def _select_default_model(self) -> Optional[str]:
        """Select a default Ollama model when available."""
        if not self.client:
            return None

        try:
            models = self.client.list()
            model_list = models.get("models") if hasattr(models, "get") else models
            if model_list:
                if isinstance(model_list, (list, tuple)):
                    first_model = model_list[0]
                else:
                    first_model = None

                if isinstance(first_model, str):
                    return first_model
                if isinstance(first_model, dict):
                    return first_model.get("name") or first_model.get("id")
        except Exception as e:
            self.logger.warning(f"Unable to select default Ollama model: {e}")

        return None

    async def check_availability(self) -> bool:
        """Check if Ollama is available."""
        if not self.client:
            return False

        try:
            models = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.list()
            )
            model_list = models.get("models") if hasattr(models, "get") else models
            return bool(model_list)
        except Exception:
            return False

    def _prepare_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Prepare the full prompt with context."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items() if isinstance(v, str)])
        return f"Context:\n{context_str}\n\nPrompt:\n{prompt}"


class ModelLoader(LoggerMixin):
    """Main model loader that manages different providers."""

    def __init__(self):
        self.providers = {}
        self.default_provider = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available model providers."""
        # Ollama provider
        if config.ollama_base_url:
            ollama_provider = OllamaProvider(config.ollama_base_url)
            if ollama_provider.client:
                self.providers["ollama"] = ollama_provider
                self.default_provider = "ollama"
            else:
                self.logger.warning("Ollama provider not available; skipping Ollama registration")

        # Anthropic provider (placeholder for future implementation)
        if config.anthropic_api_key:
            self.logger.info("Anthropic provider not yet implemented")

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        agent_role: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using the specified or default provider."""
        provider_name = provider or self.default_provider

        if not provider_name or provider_name not in self.providers:
            return "No model provider available"

        provider_instance = self.providers[provider_name]

        # Add agent role to context
        if context is None:
            context = {}
        if agent_role:
            context["agent_role"] = agent_role

        return await provider_instance.generate_response(prompt, context, **kwargs)

    async def check_provider_availability(self, provider: str) -> bool:
        """Check if a specific provider is available."""
        if provider not in self.providers:
            return False

        return await self.providers[provider].check_availability()

    async def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        available = []
        for name, provider in self.providers.items():
            if await provider.check_availability():
                available.append(name)
        return available

    def get_provider(self, name: str) -> Optional[BaseModelProvider]:
        """Get a specific provider instance."""
        return self.providers.get(name)