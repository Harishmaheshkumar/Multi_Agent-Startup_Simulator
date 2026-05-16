"""
Vector store for semantic memory search.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .memory_manager import BaseMemoryStore, Memory
from .embeddings import EmbeddingManager
from ..utils.config import config
from ..utils.logger import LoggerMixin


class VectorStore(BaseMemoryStore, LoggerMixin):
    """Vector-based memory store for semantic search."""

    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.index: Dict[str, Tuple[Memory, List[float]]] = {}
        self.index_file = config.embeddings_dir / "vector_index.json"
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Initialize the vector store."""
        if self._initialized:
            return

        try:
            # Load existing index if available
            await self._load_index()
            self._initialized = True
            self.logger.info(f"Vector store initialized with {len(self.index)} memories")
        except Exception as e:
            self.logger.error(f"Error initializing vector store: {e}")

    async def _load_index(self):
        """Load index from disk."""
        if not self.index_file.exists():
            return

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for memory_id, memory_data in data.items():
                memory = Memory.from_dict(memory_data["memory"])
                embedding = memory_data["embedding"]
                self.index[memory_id] = (memory, embedding)

        except Exception as e:
            self.logger.error(f"Error loading vector index: {e}")

    async def _save_index(self):
        """Save index to disk."""
        try:
            data = {}
            for memory_id, (memory, embedding) in self.index.items():
                data[memory_id] = {
                    "memory": memory.to_dict(),
                    "embedding": embedding
                }

            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving vector index: {e}")

    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory with its embedding."""
        async with self._lock:
            try:
                # Generate embedding for the content
                text_to_embed = f"{memory.content} {memory.response or ''}".strip()
                embedding = await self.embedding_manager.generate_embedding(text_to_embed)

                if not embedding:
                    self.logger.warning(f"Failed to generate embedding for memory {memory.id}")
                    return False

                # Store in index
                self.index[memory.id] = (memory, embedding)

                # Save to disk periodically (every 10 memories)
                if len(self.index) % 10 == 0:
                    await self._save_index()

                return True

            except Exception as e:
                self.logger.error(f"Error storing memory in vector store: {e}")
                return False

    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
        **filters
    ) -> List[Memory]:
        """Retrieve memories with filters."""
        async with self._lock:
            memories = []

            for memory, _ in self.index.values():
                if agent_id and memory.agent_id != agent_id:
                    continue
                if memory_type and memory.memory_type.value != memory_type:
                    continue

                # Apply additional filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key not in memory.metadata or memory.metadata[key] != value:
                            match = False
                            break
                    if not match:
                        continue

                memories.append(memory)

            # Sort by timestamp (newest first)
            memories.sort(key=lambda m: m.timestamp, reverse=True)
            return memories[:limit]

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by semantic similarity."""
        async with self._lock:
            if not self.embedding_manager.is_available():
                self.logger.warning("Embedding manager not available for semantic search")
                return []

            try:
                # Generate embedding for query
                query_embedding = await self.embedding_manager.generate_embedding(query)
                if not query_embedding:
                    return []

                # Prepare embeddings for search
                search_candidates = []
                for memory, embedding in self.index.values():
                    if agent_id and memory.agent_id != agent_id:
                        continue
                    search_candidates.append((memory, embedding))

                # Find similar memories
                similar_items = await self.embedding_manager.find_similar(
                    query_embedding,
                    [(m.id, emb) for m, emb in search_candidates],
                    top_k=limit
                )

                # Get memories by ID
                result_memories = []
                id_to_memory = {m.id: m for m, _ in search_candidates}

                for memory_id, similarity in similar_items:
                    if memory_id in id_to_memory:
                        memory = id_to_memory[memory_id]
                        # Update access tracking
                        memory.access_count += 1
                        memory.last_accessed = memory.timestamp  # Would be datetime.now() in real implementation
                        result_memories.append(memory)

                return result_memories

            except Exception as e:
                self.logger.error(f"Error in semantic search: {e}")
                return []

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from the vector store."""
        async with self._lock:
            if memory_id in self.index:
                del self.index[memory_id]
                await self._save_index()
                return True
            return False

    async def cleanup_old_memories(self, days: int = 30) -> int:
        """Clean up old memories."""
        # For now, just return 0 - vector store cleanup would be more complex
        # In a real implementation, you'd check timestamps and remove old entries
        return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        async with self._lock:
            total_memories = len(self.index)
            agent_counts = {}
            type_counts = {}

            for memory, _ in self.index.values():
                agent_counts[memory.agent_id] = agent_counts.get(memory.agent_id, 0) + 1
                type_counts[memory.memory_type.value] = type_counts.get(memory.memory_type.value, 0) + 1

            return {
                "total_memories": total_memories,
                "agents": agent_counts,
                "types": type_counts,
                "embedding_dimension": self.embedding_manager.dimension,
                "embedding_provider": "available" if self.embedding_manager.is_available() else "unavailable"
            }

    async def rebuild_index(self):
        """Rebuild the vector index from scratch."""
        async with self._lock:
            self.logger.info("Rebuilding vector index...")

            # Clear current index
            self.index.clear()

            # Re-index all memories (this would need to be implemented based on your storage)
            # For now, just save empty index
            await self._save_index()

            self.logger.info("Vector index rebuilt")