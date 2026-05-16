"""
Embeddings module for vector-based memory search.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from ..utils.config import config
from ..utils.logger import LoggerMixin


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between two embeddings."""
        pass


class SentenceTransformerProvider(BaseEmbeddingProvider, LoggerMixin):
    """SentenceTransformer-based embedding provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the SentenceTransformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Initialized SentenceTransformer model: {self.model_name}")
        except ImportError:
            self.logger.error("sentence-transformers package not installed")
        except Exception as e:
            self.logger.error(f"Error initializing SentenceTransformer: {e}")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not self.model:
            return []

        try:
            # Run in executor to avoid blocking
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.encode(text, convert_to_numpy=False)
            )
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return []

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            return [[] for _ in texts]

        try:
            # Run in executor to avoid blocking
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.encode(texts, convert_to_numpy=False)
            )
            return embeddings.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            return [[] for _ in texts]

    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0


class TransformersProvider(BaseEmbeddingProvider, LoggerMixin):
    """Transformers-based embedding provider."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Transformers model."""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()  # Set to evaluation mode

            # Move to GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)

            self.logger.info(f"Initialized Transformers model: {self.model_name} on {self.device}")
        except ImportError:
            self.logger.error("transformers or torch package not installed")
        except Exception as e:
            self.logger.error(f"Error initializing Transformers: {e}")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not self.model or not self.tokenizer:
            return []

        try:
            import torch

            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling over token embeddings
                embeddings = outputs.last_hidden_state.mean(dim=1)
                # Normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

            return embeddings[0].cpu().numpy().tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return []

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        # For simplicity, generate one by one
        # In production, you'd want to batch this
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0


class EmbeddingManager(LoggerMixin):
    """Manager for embedding operations."""

    def __init__(self):
        self.provider = None
        self.dimension = config.vector_dimension
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the embedding provider."""
        # Try SentenceTransformer first
        self.provider = SentenceTransformerProvider()
        if self.provider.model is not None:
            self.logger.info("Using SentenceTransformer for embeddings")
            return

        # Fall back to Transformers
        self.provider = TransformersProvider()
        if self.provider.model is not None and self.provider.tokenizer is not None:
            self.logger.info("Using Transformers for embeddings")
            return

        self.provider = None
        self.logger.error("No embedding provider available")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.provider:
            return []
        return await self.provider.generate_embedding(text)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.provider:
            return [[] for _ in texts]
        return await self.provider.generate_embeddings(texts)

    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between embeddings."""
        if not self.provider:
            return 0.0
        return await self.provider.similarity(embedding1, embedding2)

    async def find_similar(
        self,
        query_embedding: List[float],
        embeddings: List[Tuple[str, List[float]]],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find most similar embeddings."""
        similarities = []
        for text, embedding in embeddings:
            similarity = await self.similarity(query_embedding, embedding)
            similarities.append((text, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def is_available(self) -> bool:
        """Check if embedding provider is available."""
        return self.provider is not None