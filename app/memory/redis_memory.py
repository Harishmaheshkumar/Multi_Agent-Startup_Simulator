"""
Redis-based memory store for persistence.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from .memory_manager import BaseMemoryStore, Memory
from ..utils.config import config
from ..utils.logger import LoggerMixin


class RedisMemoryStore(BaseMemoryStore, LoggerMixin):
    """Redis-based persistent memory store."""

    def __init__(self):
        self.redis_client = None
        self._initialized = False
        self._last_error_log_time = 0
        self._error_log_cooldown = 30  # seconds
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Redis client."""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(config.redis_url)
            self._initialized = True
            self.logger.info("Redis memory store initialized")
        except ImportError:
            self.logger.warning("redis package not installed")
        except Exception as e:
            self.logger.error(f"Error initializing Redis client: {e}")

    async def _reconnect(self) -> bool:
        """Attempt to reconnect to Redis."""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(config.redis_url)
            self._initialized = True
            self._last_error_log_time = 0  # reset cooldown on success
            self.logger.info("Reconnected to Redis")
            return True
        except Exception as e:
            import time
            current_time = time.time()
            if current_time - self._last_error_log_time >= self._error_log_cooldown:
                self.logger.error(f"Error reconnecting to Redis: {e}")
                self._last_error_log_time = current_time
            self._initialized = False
            return False

    async def _ensure_connection(self):
        """Ensure Redis connection is available."""
        if not self._initialized or not self.redis_client:
            return await self._reconnect()

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            import time
            current_time = time.time()
            if current_time - self._last_error_log_time >= self._error_log_cooldown:
                self.logger.warning(f"Redis ping failed, attempting reconnect: {e}")
                self._last_error_log_time = current_time
            return await self._reconnect()

    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in Redis."""
        if not await self._ensure_connection():
            return False

        try:
            key = f"memory:{memory.id}"
            data = memory.to_dict()

            # Store as JSON
            await self.redis_client.set(key, json.dumps(data))

            # Add to agent index
            agent_key = f"agent_memories:{memory.agent_id}"
            await self.redis_client.sadd(agent_key, memory.id)

            # Add to type index
            type_key = f"type_memories:{memory.memory_type.value}"
            await self.redis_client.sadd(type_key, memory.id)

            # Add timestamp for cleanup
            timestamp_key = f"memory_timestamps:{memory.id}"
            await self.redis_client.set(timestamp_key, memory.timestamp.isoformat())

            return True

        except Exception as e:
            self.logger.error(f"Error storing memory in Redis: {e}")
            return False

    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
        **filters
    ) -> List[Memory]:
        """Retrieve memories from Redis with filters."""
        if not await self._ensure_connection():
            return []

        try:
            memory_ids = []

            if agent_id and memory_type:
                # Intersection of agent and type sets
                agent_key = f"agent_memories:{agent_id}"
                type_key = f"type_memories:{memory_type.value}"
                memory_ids = await self.redis_client.sinter(agent_key, type_key)
            elif agent_id:
                agent_key = f"agent_memories:{agent_id}"
                memory_ids = await self.redis_client.smembers(agent_key)
            elif memory_type:
                type_key = f"type_memories:{memory_type.value if hasattr(memory_type, 'value') else memory_type}"
                memory_ids = await self.redis_client.smembers(type_key)
            else:
                # Get all memories (this is inefficient for large datasets)
                all_keys = await self.redis_client.keys("memory:*")
                memory_ids = [key.decode().split(":", 1)[1] for key in all_keys]

            # Convert to list and limit
            memory_ids = list(memory_ids)[:limit * 2]  # Get more than needed for sorting

            memories = []
            for memory_id in memory_ids:
                memory_id = memory_id.decode() if isinstance(memory_id, bytes) else memory_id
                key = f"memory:{memory_id}"
                data = await self.redis_client.get(key)

                if data:
                    try:
                        memory_data = json.loads(data)
                        memory = Memory.from_dict(memory_data)
                        memories.append(memory)
                    except json.JSONDecodeError:
                        continue

            # Sort by timestamp (newest first)
            memories.sort(key=lambda m: m.timestamp, reverse=True)
            return memories[:limit]

        except Exception as e:
            self.logger.error(f"Error retrieving memories from Redis: {e}")
            return []

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by content (simple text search)."""
        if not await self._ensure_connection():
            return []

        try:
            # Get candidate memory IDs
            if agent_id:
                agent_key = f"agent_memories:{agent_id}"
                candidate_ids = await self.redis_client.smembers(agent_key)
            else:
                all_keys = await self.redis_client.keys("memory:*")
                candidate_ids = [key.decode().split(":", 1)[1] for key in all_keys]

            matching_memories = []
            query_lower = query.lower()

            for memory_id in candidate_ids:
                memory_id = memory_id.decode() if isinstance(memory_id, bytes) else memory_id
                key = f"memory:{memory_id}"
                data = await self.redis_client.get(key)

                if data:
                    try:
                        memory_data = json.loads(data)
                        content = memory_data.get("content", "").lower()
                        response = memory_data.get("response", "").lower() if memory_data.get("response") else ""

                        if query_lower in content or query_lower in response:
                            memory = Memory.from_dict(memory_data)
                            matching_memories.append(memory)
                    except (json.JSONDecodeError, KeyError):
                        continue

            # Sort by recency and access count
            matching_memories.sort(
                key=lambda m: (m.access_count, m.timestamp),
                reverse=True
            )

            return matching_memories[:limit]

        except Exception as e:
            self.logger.error(f"Error searching memories in Redis: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Redis."""
        if not await self._ensure_connection():
            return False

        try:
            key = f"memory:{memory_id}"

            # Get memory data to remove from indexes
            data = await self.redis_client.get(key)
            if data:
                memory_data = json.loads(data)
                agent_id = memory_data.get("agent_id")
                memory_type = memory_data.get("memory_type")

                # Remove from indexes
                if agent_id:
                    agent_key = f"agent_memories:{agent_id}"
                    await self.redis_client.srem(agent_key, memory_id)

                if memory_type:
                    type_key = f"type_memories:{memory_type}"
                    await self.redis_client.srem(type_key, memory_id)

                # Remove timestamp
                timestamp_key = f"memory_timestamps:{memory_id}"
                await self.redis_client.delete(timestamp_key)

            # Delete the memory
            await self.redis_client.delete(key)
            return True

        except Exception as e:
            self.logger.error(f"Error deleting memory from Redis: {e}")
            return False

    async def cleanup_old_memories(self, days: int = 30) -> int:
        """Clean up old memories from Redis."""
        if not await self._ensure_connection():
            return 0

        try:
            import datetime
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

            # Get all timestamp keys
            timestamp_keys = await self.redis_client.keys("memory_timestamps:*")
            cleaned_count = 0

            for timestamp_key in timestamp_keys:
                timestamp_str = await self.redis_client.get(timestamp_key)
                if timestamp_str:
                    try:
                        timestamp = datetime.datetime.fromisoformat(timestamp_str.decode())
                        if timestamp < cutoff_date:
                            # Extract memory ID and delete
                            memory_id = timestamp_key.decode().split(":", 1)[1]
                            await self.delete_memory(memory_id)
                            cleaned_count += 1
                    except (ValueError, AttributeError):
                        continue

            self.logger.info(f"Cleaned up {cleaned_count} old memories from Redis")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old memories from Redis: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis memory store statistics."""
        if not await self._ensure_connection():
            return {"status": "disconnected"}

        try:
            # Get basic stats
            memory_count = await self.redis_client.dbsize()
            agent_count = len(await self.redis_client.keys("agent_memories:*"))
            type_count = len(await self.redis_client.keys("type_memories:*"))

            return {
                "status": "connected",
                "total_keys": memory_count,
                "agent_indexes": agent_count,
                "type_indexes": type_count,
                "redis_url": config.redis_url
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}