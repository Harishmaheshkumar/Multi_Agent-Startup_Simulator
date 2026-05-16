"""
Tests for memory system functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ..memory.memory_manager import MemoryManager
from ..memory.vector_store import VectorStore
from ..memory.redis_memory import RedisMemoryStore
from ..memory.embeddings import EmbeddingManager


class TestMemoryManager:
    """Test cases for MemoryManager class."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = Mock(spec=VectorStore)
        store.store_memory = AsyncMock()
        store.search_memories = AsyncMock(return_value=[])
        store.get_stats = AsyncMock(return_value={"total_memories": 0})
        return store

    @pytest.fixture
    def mock_redis_store(self):
        """Create a mock Redis store."""
        store = Mock(spec=RedisMemoryStore)
        store.store_memory = AsyncMock()
        store.search_memories = AsyncMock(return_value=[])
        store.get_stats = AsyncMock(return_value={"total_memories": 0})
        return store

    @pytest.fixture
    def memory_manager(self, mock_vector_store, mock_redis_store):
        """Create a memory manager instance."""
        manager = MemoryManager()
        manager.vector_store = mock_vector_store
        manager.redis_store = mock_redis_store
        return manager

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initialization."""
        assert memory_manager.vector_store is not None
        assert memory_manager.redis_store is not None
        assert memory_manager.memory_stats == {}

    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager, mock_vector_store, mock_redis_store):
        """Test storing memory."""
        memory_data = {
            "content": "Test memory content",
            "response": "Test response",
            "memory_type": "conversation",
            "metadata": {"agent": "test_agent"}
        }

        await memory_manager.store_memory(memory_data)

        # Verify both stores were called
        mock_vector_store.store_memory.assert_called_once_with(memory_data)
        mock_redis_store.store_memory.assert_called_once_with(memory_data)

    @pytest.mark.asyncio
    async def test_search_memories(self, memory_manager, mock_vector_store, mock_redis_store):
        """Test searching memories."""
        mock_memories = [
            {"content": "Test memory 1", "response": "Response 1", "memory_type": "task"},
            {"content": "Test memory 2", "response": "Response 2", "memory_type": "conversation"}
        ]

        mock_vector_store.search_memories.return_value = mock_memories

        results = await memory_manager.search_memories("test query", limit=5)

        assert results == mock_memories
        mock_vector_store.search_memories.assert_called_once_with("test query", limit=5)

    @pytest.mark.asyncio
    async def test_memory_stats(self, memory_manager, mock_vector_store, mock_redis_store):
        """Test getting memory statistics."""
        mock_vector_store.get_stats.return_value = {"total_memories": 10, "types": {"task": 7, "conversation": 3}}
        mock_redis_store.get_stats.return_value = {"total_memories": 8, "stores": {"redis": "available"}}

        stats = await memory_manager.get_memory_stats()

        expected_stats = {
            "total_memories": 10,  # From vector store
            "types": {"task": 7, "conversation": 3},
            "stores": {"redis": "available"}
        }

        assert stats == expected_stats

    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory_manager, mock_vector_store, mock_redis_store):
        """Test memory cleanup."""
        await memory_manager.cleanup()

        mock_vector_store.cleanup.assert_called_once()
        mock_redis_store.cleanup.assert_called_once()


class TestVectorStore:
    """Test cases for VectorStore class."""

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create a mock embedding manager."""
        manager = Mock(spec=EmbeddingManager)
        manager.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return manager

    @pytest.fixture
    def vector_store(self, mock_embedding_manager):
        """Create a vector store instance."""
        store = VectorStore(embedding_manager=mock_embedding_manager)
        return store

    @pytest.mark.asyncio
    async def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization."""
        assert vector_store.memories == []
        assert vector_store.embedding_manager is not None

    @pytest.mark.asyncio
    async def test_store_memory(self, vector_store, mock_embedding_manager):
        """Test storing memory in vector store."""
        memory_data = {
            "content": "Test content",
            "response": "Test response",
            "memory_type": "task",
            "timestamp": datetime.now().isoformat()
        }

        await vector_store.store_memory(memory_data)

        assert len(vector_store.memories) == 1
        stored_memory = vector_store.memories[0]

        assert stored_memory.content == "Test content"
        assert stored_memory.response == "Test response"
        assert stored_memory.memory_type == "task"
        assert stored_memory.embedding == [0.1, 0.2, 0.3]

        mock_embedding_manager.generate_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_memories(self, vector_store, mock_embedding_manager):
        """Test searching memories in vector store."""
        # Store some test memories
        memories_data = [
            {"content": "Machine learning project", "response": "ML response", "memory_type": "task"},
            {"content": "Web development task", "response": "Web response", "memory_type": "task"},
            {"content": "Marketing strategy", "response": "Marketing response", "memory_type": "conversation"}
        ]

        for memory in memories_data:
            memory["timestamp"] = datetime.now().isoformat()
            await vector_store.store_memory(memory)

        # Mock similarity search
        mock_embedding_manager.generate_embedding.return_value = [0.1, 0.2, 0.3]

        results = await vector_store.search_memories("machine learning", limit=2)

        # Should return memories (mock similarity would need more complex setup)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_stats(self, vector_store):
        """Test getting vector store statistics."""
        # Store some memories
        memories_data = [
            {"content": "Task 1", "response": "Response 1", "memory_type": "task", "timestamp": datetime.now().isoformat()},
            {"content": "Task 2", "response": "Response 2", "memory_type": "task", "timestamp": datetime.now().isoformat()},
            {"content": "Conversation 1", "response": "Response 3", "memory_type": "conversation", "timestamp": datetime.now().isoformat()}
        ]

        for memory in memories_data:
            await vector_store.store_memory(memory)

        stats = await vector_store.get_stats()

        assert stats["total_memories"] == 3
        assert stats["types"]["task"] == 2
        assert stats["types"]["conversation"] == 1


class TestRedisMemoryStore:
    """Test cases for RedisMemoryStore class."""

    @pytest.fixture
    def redis_store(self):
        """Create a Redis memory store instance."""
        store = RedisMemoryStore()
        return store

    @pytest.mark.asyncio
    async def test_redis_store_initialization(self, redis_store):
        """Test Redis store initialization."""
        assert redis_store.client is None  # Not connected yet
        assert redis_store.memories == []

    @pytest.mark.asyncio
    @patch('redis.Redis')
    async def test_store_memory(self, mock_redis, redis_store):
        """Test storing memory in Redis store."""
        # Mock Redis client
        mock_client = Mock()
        mock_redis.return_value = mock_client
        redis_store.client = mock_client

        memory_data = {
            "content": "Redis test content",
            "response": "Redis test response",
            "memory_type": "task",
            "timestamp": datetime.now().isoformat()
        }

        await redis_store.store_memory(memory_data)

        # Verify Redis operations were called
        mock_client.set.assert_called()
        assert len(redis_store.memories) == 1

    @pytest.mark.asyncio
    @patch('redis.Redis')
    async def test_search_memories(self, mock_redis, redis_store):
        """Test searching memories in Redis store."""
        # Mock Redis client
        mock_client = Mock()
        mock_client.keys.return_value = [b"memory:1", b"memory:2"]
        mock_client.get.side_effect = [
            '{"content": "Test 1", "response": "Response 1", "memory_type": "task"}',
            '{"content": "Test 2", "response": "Response 2", "memory_type": "conversation"}'
        ]
        mock_redis.return_value = mock_client
        redis_store.client = mock_client

        results = await redis_store.search_memories("test query")

        assert len(results) == 2
        assert results[0]["content"] == "Test 1"
        assert results[1]["content"] == "Test 2"

    @pytest.mark.asyncio
    @patch('redis.Redis')
    async def test_get_stats(self, mock_redis, redis_store):
        """Test getting Redis store statistics."""
        # Mock Redis client
        mock_client = Mock()
        mock_client.keys.return_value = [b"memory:1", b"memory:2", b"memory:3"]
        mock_redis.return_value = mock_client
        redis_store.client = mock_client

        stats = await redis_store.get_stats()

        assert stats["total_memories"] == 3
        assert stats["stores"]["redis"] == "available"


class TestEmbeddingManager:
    """Test cases for EmbeddingManager class."""

    @pytest.fixture
    def embedding_manager(self):
        """Create an embedding manager instance."""
        manager = EmbeddingManager()
        return manager

    @pytest.mark.asyncio
    async def test_embedding_manager_initialization(self, embedding_manager):
        """Test embedding manager initialization."""
        assert embedding_manager.providers == {}
        assert embedding_manager.default_provider is None

    @pytest.mark.asyncio
    async def test_generate_embedding_mock(self, embedding_manager):
        """Test embedding generation with mock."""
        # Mock the provider
        mock_provider = Mock()
        mock_provider.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
        embedding_manager.providers["mock"] = mock_provider
        embedding_manager.default_provider = "mock"

        embedding = await embedding_manager.generate_embedding("test text")

        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_provider.generate_embedding.assert_called_once_with("test text")


class TestMemoryIntegration:
    """Integration tests for memory system."""

    @pytest.fixture
    async def full_memory_system(self):
        """Create a full memory system for integration testing."""
        # Mock components
        vector_store = Mock(spec=VectorStore)
        vector_store.store_memory = AsyncMock()
        vector_store.search_memories = AsyncMock(return_value=[])
        vector_store.get_stats = AsyncMock(return_value={"total_memories": 0})

        redis_store = Mock(spec=RedisMemoryStore)
        redis_store.store_memory = AsyncMock()
        redis_store.search_memories = AsyncMock(return_value=[])
        redis_store.get_stats = AsyncMock(return_value={"total_memories": 0})

        manager = MemoryManager()
        manager.vector_store = vector_store
        manager.redis_store = redis_store

        return manager, vector_store, redis_store

    @pytest.mark.asyncio
    async def test_end_to_end_memory_flow(self, full_memory_system):
        """Test end-to-end memory storage and retrieval."""
        manager, vector_store, redis_store = full_memory_system

        # Store a memory
        memory_data = {
            "content": "Integration test memory",
            "response": "Integration test response",
            "memory_type": "task",
            "metadata": {"test": True}
        }

        await manager.store_memory(memory_data)

        # Verify both stores were called
        vector_store.store_memory.assert_called_once_with(memory_data)
        redis_store.store_memory.assert_called_once_with(memory_data)

        # Search for memories
        results = await manager.search_memories("integration test")

        vector_store.search_memories.assert_called_once_with("integration test", limit=10)

    @pytest.mark.asyncio
    async def test_memory_stats_aggregation(self, full_memory_system):
        """Test memory statistics aggregation."""
        manager, vector_store, redis_store = full_memory_system

        # Mock different stats
        vector_store.get_stats.return_value = {
            "total_memories": 15,
            "types": {"task": 10, "conversation": 5}
        }
        redis_store.get_stats.return_value = {
            "total_memories": 12,
            "stores": {"redis": "available"}
        }

        stats = await manager.get_memory_stats()

        assert stats["total_memories"] == 15  # Takes from vector store
        assert stats["types"]["task"] == 10
        assert stats["stores"]["redis"] == "available"


# Performance tests
@pytest.mark.benchmark
class TestMemoryPerformance:
    """Performance tests for memory system."""

    @pytest.fixture
    def perf_memory_manager(self):
        """Create memory manager for performance testing."""
        manager = MemoryManager()
        # Use real stores but with minimal setup
        return manager

    @pytest.mark.asyncio
    async def test_memory_storage_performance(self, perf_memory_manager, benchmark):
        """Benchmark memory storage performance."""
        memory_data = {
            "content": "Performance test memory",
            "response": "Performance test response",
            "memory_type": "task",
            "timestamp": datetime.now().isoformat()
        }

        # Benchmark storage
        await benchmark(perf_memory_manager.store_memory, memory_data)

    @pytest.mark.asyncio
    async def test_memory_search_performance(self, perf_memory_manager, benchmark):
        """Benchmark memory search performance."""
        # Benchmark search
        results = await benchmark(perf_memory_manager.search_memories, "test query", limit=5)
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__])