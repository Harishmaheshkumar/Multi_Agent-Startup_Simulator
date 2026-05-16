"""
Base agent class for the Multi-Agent Startup Simulator.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..utils.constants import AgentRole, MemoryType
from ..utils.logger import LoggerMixin
from ..memory.memory_manager import MemoryManager
from ..llm.model_loader import ModelLoader


class BaseAgent(ABC, LoggerMixin):
    """Abstract base class for all agents in the startup simulator."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        model_loader: ModelLoader,
        memory_manager: MemoryManager,
        config: Optional[Dict[str, Any]] = None
    ):
        self.role = role
        self.name = name
        self.model_loader = model_loader
        self.memory_manager = memory_manager
        self.config = config or {}
        self.created_at = datetime.now()
        self.last_active = datetime.now()

        # Agent state
        self.is_active = True
        self.current_task = None
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "collaboration_score": 0.0
        }

    @property
    def agent_id(self) -> str:
        """Unique identifier for the agent."""
        return f"{self.role.value}_{self.name.lower().replace(' ', '_')}"

    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return the result."""
        pass

    async def collaborate(self, other_agents: List['BaseAgent'], context: Dict[str, Any]) -> Dict[str, Any]:
        """Collaborate with other agents on a task."""
        self.logger.info(f"{self.name} collaborating with {len(other_agents)} other agents")
        return {
            "agent": self.agent_id,
            "collaboration_result": "Default collaboration completed.",
            "context": context,
            "partner_agents": [agent.agent_id for agent in other_agents]
        }

    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using the agent's LLM."""
        self.last_active = datetime.now()

        # Prepare context
        full_context = {
            "agent_role": self.role.value,
            "agent_name": self.name,
            "current_time": datetime.now().isoformat(),
            "task_context": context or {}
        }

        # Add memory context
        memory_context = await self._get_memory_context(prompt)
        full_context.update(memory_context)

        # Generate response
        response = await self.model_loader.generate_response(
            prompt=prompt,
            context=full_context,
            agent_role=self.role.value
        )

        # Store in memory
        await self._store_memory(prompt, response, MemoryType.CONVERSATION)

        return response

    async def learn(self, experience: Dict[str, Any]) -> None:
        """Learn from an experience and update internal state."""
        self.logger.info(f"Agent {self.name} learning from experience: {experience.get('type', 'unknown')}")

        # Store learning in memory
        await self._store_memory(
            content=f"Learned: {experience}",
            metadata={"type": "learning", "experience": experience},
            memory_type=MemoryType.EPISODIC
        )

        # Update performance metrics
        if experience.get("success", False):
            self.performance_metrics["tasks_completed"] += 1
            # Recalculate success rate
            total_tasks = self.performance_metrics["tasks_completed"]
            self.performance_metrics["success_rate"] = total_tasks / (total_tasks + experience.get("failures", 0))

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "current_task": self.current_task,
            "last_active": self.last_active.isoformat(),
            "performance_metrics": self.performance_metrics,
            "created_at": self.created_at.isoformat()
        }

    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration."""
        self.config.update(new_config)
        self.logger.info(f"Updated config for agent {self.name}: {new_config}")

    async def _get_memory_context(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Retrieve relevant memory context for a query."""
        try:
            memories = await self.memory_manager.search_memories(
                query=query,
                agent_id=self.agent_id,
                limit=limit
            )

            return {
                "relevant_memories": [m.content for m in memories],
                "memory_count": len(memories)
            }
        except Exception as e:
            self.logger.error(f"Error retrieving memory context: {e}")
            return {"relevant_memories": [], "memory_count": 0}

    async def _store_memory(
        self,
        content: str,
        response: Optional[str] = None,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store information in memory."""
        try:
            memory_data = {
                "agent_id": self.agent_id,
                "content": content,
                "response": response,
                "memory_type": memory_type.value,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            await self.memory_manager.store_memory(memory_data)
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")

    def __str__(self) -> str:
        return f"{self.role.value.title()} Agent: {self.name}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(role={self.role.value}, name='{self.name}')>"