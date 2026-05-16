"""
Ollama client wrapper for the Multi-Agent Startup Simulator.
"""

import asyncio
from typing import Any, Dict, List, Optional

from .model_loader import OllamaProvider
from ..utils.config import config
from ..utils.logger import LoggerMixin


class OllamaClient(LoggerMixin):
    """Enhanced Ollama client with additional features."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.ollama_base_url
        self.provider = OllamaProvider(self.base_url)
        self.available_models: List[str] = []
        self._initialized = False

    async def initialize(self):
        """Initialize the Ollama client and discover models."""
        if self._initialized:
            return

        if not self.provider.client:
            self.logger.warning("Ollama provider not available")
            return

        available = await self.provider.check_availability()
        if not available:
            self.logger.warning("Ollama server not available")
            return

        self.available_models = await self._get_available_models()
        self._initialized = True
        self.logger.info(f"Ollama client initialized with models: {self.available_models}")

    async def _get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        if not self.provider.client:
            return []

        try:
            models = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.provider.client.list()
            )

            if isinstance(models, dict):
                model_list = models.get("models", models.get("data", []))
            else:
                model_list = models

            available = []
            for model in model_list or []:
                if isinstance(model, str):
                    available.append(model)
                elif isinstance(model, dict):
                    name = model.get("name") or model.get("id")
                    if name:
                        available.append(name)

            return available
        except Exception as e:
            self.logger.error(f"Error getting Ollama models: {e}")
            return []

    async def generate_with_model(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate response with a specific Ollama model."""
        if not self.provider.client:
            return "Ollama client not available"

        # Determine model: explicit -> discovered available -> provider default -> fallback
        if not model:
            if self.available_models:
                model = self.available_models[0]
            else:
                model = self.provider.default_model or "llama2"
        else:
            if self.available_models and model not in self.available_models:
                self.logger.warning(f"Model {model} not available, using default")
                model = self.available_models[0] if self.available_models else (self.provider.default_model or "llama2")

        return await self.provider.generate_response(
            prompt=prompt,
            context=context,
            model=model,
            **kwargs
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Convert chat messages to a prompt and generate a response."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        full_prompt = "\n\n".join(prompt_parts)
        return await self.generate_with_model(full_prompt, model, **kwargs)

    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Stream response from Ollama (placeholder for future implementation)."""
        response = await self.generate_with_model(prompt, model, context, **kwargs)
        yield response

    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return {
            "name": model,
            "available": model in self.available_models,
            "provider": "ollama"
        }

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        if not self.provider.client:
            return False

        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.provider.client.pull(model)
            )
            self.available_models = await self._get_available_models()
            return True
        except Exception as e:
            self.logger.error(f"Error pulling model {model}: {e}")
            return False

    async def list_running_models(self) -> List[Dict[str, Any]]:
        """List currently running models."""
        if not self.provider.client:
            return []

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.provider.client.ps()
            )
            if isinstance(response, dict):
                return response.get("models", [])
            return []
        except Exception as e:
            self.logger.error(f"Error listing running models: {e}")
            return []

    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    def get_available_models_list(self) -> List[str]:
        """Get list of available models."""
        return self.available_models.copy()