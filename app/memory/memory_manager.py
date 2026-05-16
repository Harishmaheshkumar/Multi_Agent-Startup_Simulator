"""
Memory manager for the Multi-Agent Startup Simulator.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..utils.config import config
from ..utils.constants import MemoryType
from ..utils.logger import LoggerMixin


@dataclass
class Memory:
    """Memory data structure."""
    id: str
    agent_id: str
    content: str
    response: Optional[str]
    memory_type: MemoryType
    timestamp: datetime
    metadata: Dict[str, Any]
    importance: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "content": self.content,
            "response": self.response,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create memory from dictionary."""
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            content=data["content"],
            response=data.get("response"),
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )


class BaseMemoryStore(ABC):
    """Abstract base class for memory storage."""

    @abstractmethod
    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory."""
        pass

    @abstractmethod
    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        **filters
    ) -> List[Memory]:
        """Retrieve memories with filters."""
        pass

    @abstractmethod
    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by content."""
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        pass

    @abstractmethod
    async def cleanup_old_memories(self, days: int = 30) -> int:
        """Clean up old memories."""
        pass


class InMemoryStore(BaseMemoryStore, LoggerMixin):
    """Simple in-memory memory store."""

    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self._lock = asyncio.Lock()

    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in memory."""
        async with self._lock:
            self.memories[memory.id] = memory
            return True

    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        **filters
    ) -> List[Memory]:
        """Retrieve memories with filters."""
        async with self._lock:
            memories = list(self.memories.values())

            # Apply filters
            if agent_id:
                memories = [m for m in memories if m.agent_id == agent_id]
            if memory_type:
                memories = [m for m in memories if m.memory_type == memory_type]

            # Sort by timestamp (newest first)
            memories.sort(key=lambda m: m.timestamp, reverse=True)

            return memories[:limit]

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by content."""
        async with self._lock:
            memories = list(self.memories.values())

            if agent_id:
                memories = [m for m in memories if m.agent_id == agent_id]

            # Simple text search
            query_lower = query.lower()
            matching_memories = []
            for memory in memories:
                content_lower = memory.content.lower()
                if query_lower in content_lower:
                    matching_memories.append(memory)

            # Sort by relevance (simple: recency + access count)
            matching_memories.sort(
                key=lambda m: (m.access_count, m.timestamp),
                reverse=True
            )

            return matching_memories[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        async with self._lock:
            if memory_id in self.memories:
                del self.memories[memory_id]
                return True
            return False

    async def cleanup_old_memories(self, days: int = 30) -> int:
        """Clean up old memories."""
        async with self._lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            old_memories = [
                mid for mid, m in self.memories.items()
                if m.timestamp < cutoff_date
            ]

            for mid in old_memories:
                del self.memories[mid]

            return len(old_memories)


class MemoryManager(LoggerMixin):
    """Main memory manager that coordinates different storage backends."""

    def __init__(self):
        self.primary_store: BaseMemoryStore = InMemoryStore()
        self.vector_store = None
        self.redis_store = None

        # Initialize additional stores if configured
        self._initialize_stores()

    def _initialize_stores(self):
        """Initialize additional memory stores."""
        # Vector store for semantic search
        try:
            from .vector_store import VectorStore
            self.vector_store = VectorStore()
        except ImportError:
            self.logger.warning("Vector store not available")

        # Redis store for persistence
        if config.use_redis:
            try:
                from .redis_memory import RedisMemoryStore
                self.redis_store = RedisMemoryStore()
            except ImportError:
                self.logger.warning("Redis store not available")
        else:
            self.logger.info("Redis store disabled via config")

    async def store_memory(self, memory_data: Dict[str, Any]) -> bool:
        """Store a memory in all available stores."""
        try:
            # Create memory object
            memory = Memory(
                id=memory_data.get("id") or f"mem_{datetime.now().timestamp()}",
                agent_id=memory_data["agent_id"],
                content=memory_data["content"],
                response=memory_data.get("response"),
                memory_type=MemoryType(memory_data["memory_type"]),
                timestamp=datetime.fromisoformat(memory_data["timestamp"]) if isinstance(memory_data["timestamp"], str) else memory_data["timestamp"],
                metadata=memory_data.get("metadata", {})
            )

            # Store in primary store
            success = await self.primary_store.store_memory(memory)

            # Store in additional stores
            if self.redis_store:
                await self.redis_store.store_memory(memory)

            if self.vector_store:
                await self.vector_store.store_memory(memory)

            return success

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            return False

    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        **filters
    ) -> List[Memory]:
        """Retrieve memories from primary store."""
        return await self.primary_store.retrieve_memories(
            agent_id=agent_id,
            memory_type=memory_type,
            limit=limit,
            **filters
        )

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories using the best available method."""
        # Try vector search first if available
        if self.vector_store:
            try:
                return await self.vector_store.search_memories(query, agent_id, limit)
            except Exception as e:
                self.logger.warning(f"Vector search failed: {e}")

        # Fall back to primary store search
        return await self.primary_store.search_memories(query, agent_id, limit)

    async def get_conversation_history(
        self,
        agent_id: str,
        limit: int = 20
    ) -> List[Memory]:
        """Get conversation history for an agent."""
        return await self.retrieve_memories(
            agent_id=agent_id,
            memory_type=MemoryType.CONVERSATION,
            limit=limit
        )

    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50
    ) -> List[Memory]:
        """Get all memories for a specific agent."""
        return await self.retrieve_memories(
            agent_id=agent_id,
            memory_type=memory_type,
            limit=limit
        )

    async def cleanup_memories(self, days: int = 30) -> int:
        """Clean up old memories across all stores."""
        total_cleaned = 0

        # Clean primary store
        total_cleaned += await self.primary_store.cleanup_old_memories(days)

        # Clean additional stores
        if self.redis_store:
            total_cleaned += await self.redis_store.cleanup_old_memories(days)

        if self.vector_store:
            total_cleaned += await self.vector_store.cleanup_old_memories(days)

        self.logger.info(f"Cleaned up {total_cleaned} old memories")
        return total_cleaned

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        # This is a simplified version - in practice, you'd query each store
        return {
            "total_memories": len(self.primary_store.memories) if hasattr(self.primary_store, 'memories') else 0,
            "stores": {
                "primary": "in_memory",
                "vector": "available" if self.vector_store else "unavailable",
                "redis": "available" if self.redis_store else "unavailable"
            }
        }