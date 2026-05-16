"""
Tests for agent functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..agents.ceo_agent import CEOAgent
from ..utils.constants import AgentRole
from ..memory.memory_manager import MemoryManager


class TestBaseAgent:
    """Test cases for BaseAgent class."""

    @pytest.fixture
    def mock_memory_manager(self):
        """Create a mock memory manager."""
        manager = Mock(spec=MemoryManager)
        manager.store_memory = AsyncMock()
        manager.search_memories = AsyncMock(return_value=[])
        return manager

    @pytest.fixture
    def mock_model_loader(self):
        """Create a mock model loader."""
        loader = Mock()
        loader.generate_response = AsyncMock(return_value="Mock response")
        return loader

    @pytest.fixture
    def base_agent(self, mock_memory_manager, mock_model_loader):
        """Create a base agent instance."""
        agent = BaseAgent(
            agent_id="test_agent_1",
            name="Test Agent",
            role=AgentRole.CEO,
            memory_manager=mock_memory_manager,
            model_loader=mock_model_loader
        )
        return agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self, base_agent):
        """Test agent initialization."""
        assert base_agent.agent_id == "test_agent_1"
        assert base_agent.name == "Test Agent"
        assert base_agent.role == AgentRole.CEO
        assert base_agent.is_active is False
        assert base_agent.performance_metrics == {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "collaboration_score": 0.0
        }

    @pytest.mark.asyncio
    async def test_agent_activation(self, base_agent):
        """Test agent activation."""
        await base_agent.activate()
        assert base_agent.is_active is True
        assert base_agent.last_active is not None

    @pytest.mark.asyncio
    async def test_agent_deactivation(self, base_agent):
        """Test agent deactivation."""
        await base_agent.activate()
        await base_agent.deactivate()
        assert base_agent.is_active is False

    @pytest.mark.asyncio
    async def test_task_processing(self, base_agent, mock_model_loader):
        """Test task processing."""
        mock_model_loader.generate_response.return_value = "Task completed successfully"

        task_data = {
            "type": "planning",
            "content": "Plan the company strategy",
            "priority": "high"
        }

        result = await base_agent.process_task(task_data)

        assert result["success"] is True
        assert "response" in result
        assert result["response"] == "Task completed successfully"
        assert base_agent.performance_metrics["tasks_completed"] == 1

    @pytest.mark.asyncio
    async def test_memory_integration(self, base_agent, mock_memory_manager):
        """Test memory integration."""
        task_data = {
            "type": "planning",
            "content": "Test memory storage",
            "priority": "medium"
        }

        await base_agent.process_task(task_data)

        # Verify memory was stored
        mock_memory_manager.store_memory.assert_called_once()
        call_args = mock_memory_manager.store_memory.call_args

        memory_data = call_args[0][0]  # First positional argument
        assert memory_data["content"] == "Test memory storage"
        assert memory_data["response"] == "Mock response"
        assert memory_data["memory_type"] == "task"

    @pytest.mark.asyncio
    async def test_collaboration(self, base_agent):
        """Test agent collaboration."""
        other_agent = Mock()
        other_agent.name = "Collaborator Agent"
        other_agent.get_status = AsyncMock(return_value={"is_active": True})

        message = "Let's collaborate on this task"
        response = await base_agent.collaborate(other_agent, message)

        assert response is not None
        assert base_agent.performance_metrics["collaboration_score"] > 0

    @pytest.mark.asyncio
    async def test_status_reporting(self, base_agent):
        """Test status reporting."""
        status = await base_agent.get_status()

        assert status["agent_id"] == "test_agent_1"
        assert status["name"] == "Test Agent"
        assert status["role"] == "ceo"
        assert status["is_active"] is False
        assert "performance_metrics" in status
        assert "last_active" in status

    @pytest.mark.asyncio
    async def test_performance_tracking(self, base_agent, mock_model_loader):
        """Test performance metrics tracking."""
        # Process multiple tasks
        tasks = [
            {"type": "planning", "content": "Task 1", "priority": "high"},
            {"type": "development", "content": "Task 2", "priority": "medium"},
            {"type": "funding", "content": "Task 3", "priority": "high"}
        ]

        for task in tasks:
            await base_agent.process_task(task)

        metrics = base_agent.performance_metrics
        assert metrics["tasks_completed"] == 3
        assert metrics["success_rate"] == 1.0  # All tasks successful
        assert metrics["average_response_time"] > 0


class TestCEOAgent:
    """Test cases for CEOAgent class."""

    @pytest.fixture
    def ceo_agent(self, mock_memory_manager, mock_model_loader):
        """Create a CEO agent instance."""
        agent = CEOAgent(
            agent_id="ceo_1",
            memory_manager=mock_memory_manager,
            model_loader=mock_model_loader
        )
        return agent

    @pytest.mark.asyncio
    async def test_ceo_initialization(self, ceo_agent):
        """Test CEO agent initialization."""
        assert ceo_agent.role == AgentRole.CEO
        assert ceo_agent.name == "CEO Agent"
        assert "leadership" in ceo_agent.capabilities
        assert "strategy" in ceo_agent.capabilities

    @pytest.mark.asyncio
    async def test_ceo_task_processing(self, ceo_agent, mock_model_loader):
        """Test CEO-specific task processing."""
        mock_model_loader.generate_response.return_value = "Strategic plan developed"

        task_data = {
            "type": "planning",
            "content": "Develop company strategy",
            "priority": "high"
        }

        result = await ceo_agent.process_task(task_data)

        assert result["success"] is True
        assert "Strategic plan developed" in result["response"]

    @pytest.mark.asyncio
    async def test_ceo_capabilities(self, ceo_agent):
        """Test CEO agent capabilities."""
        capabilities = ceo_agent.get_capabilities()
        expected_caps = ["leadership", "strategy", "vision", "decision_making", "team_management"]

        for cap in expected_caps:
            assert cap in capabilities


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    @pytest.fixture
    def agent_group(self, mock_memory_manager, mock_model_loader):
        """Create a group of agents for integration testing."""
        agents = []

        # Create different agent types
        for role in [AgentRole.CEO, AgentRole.ENGINEER, AgentRole.MARKETER]:
            if role == AgentRole.CEO:
                agent = CEOAgent(
                    agent_id=f"{role.value}_1",
                    memory_manager=mock_memory_manager,
                    model_loader=mock_model_loader
                )
            else:
                agent = BaseAgent(
                    agent_id=f"{role.value}_1",
                    name=f"{role.value.title()} Agent",
                    role=role,
                    memory_manager=mock_memory_manager,
                    model_loader=mock_model_loader
                )
            agents.append(agent)

        return agents

    @pytest.mark.asyncio
    async def test_agent_collaboration_flow(self, agent_group):
        """Test collaboration flow between agents."""
        ceo_agent = agent_group[0]
        engineer_agent = agent_group[1]

        # Activate agents
        await ceo_agent.activate()
        await engineer_agent.activate()

        # CEO initiates collaboration
        message = "We need to develop a new product feature"
        response = await ceo_agent.collaborate(engineer_agent, message)

        assert response is not None
        assert ceo_agent.performance_metrics["collaboration_score"] > 0
        assert engineer_agent.performance_metrics["collaboration_score"] > 0

    @pytest.mark.asyncio
    async def test_task_distribution(self, agent_group):
        """Test task distribution among agents."""
        tasks = [
            {"type": "planning", "content": "Strategic planning", "priority": "high"},
            {"type": "development", "content": "Feature development", "priority": "high"},
            {"type": "marketing", "content": "Market analysis", "priority": "medium"}
        ]

        # Assign tasks to appropriate agents
        for i, task in enumerate(tasks):
            agent = agent_group[i % len(agent_group)]
            result = await agent.process_task(task)
            assert result["success"] is True

        # Verify all agents have worked
        for agent in agent_group:
            assert agent.performance_metrics["tasks_completed"] > 0

    @pytest.mark.asyncio
    async def test_performance_aggregation(self, agent_group):
        """Test performance metrics aggregation."""
        # Process tasks for all agents
        for agent in agent_group:
            for _ in range(3):
                task = {"type": "general", "content": "Test task", "priority": "medium"}
                await agent.process_task(task)

        # Check aggregated performance
        total_tasks = sum(agent.performance_metrics["tasks_completed"] for agent in agent_group)
        assert total_tasks == 9  # 3 agents * 3 tasks each

        # Check average success rate
        avg_success = sum(agent.performance_metrics["success_rate"] for agent in agent_group) / len(agent_group)
        assert avg_success == 1.0  # All tasks successful


# Performance benchmarks
@pytest.mark.benchmark
class TestAgentPerformance:
    """Performance tests for agents."""

    @pytest.fixture
    def performance_agent(self, mock_memory_manager, mock_model_loader):
        """Create agent for performance testing."""
        agent = BaseAgent(
            agent_id="perf_agent_1",
            name="Performance Agent",
            role=AgentRole.ENGINEER,
            memory_manager=mock_memory_manager,
            model_loader=mock_model_loader
        )
        return agent

    @pytest.mark.asyncio
    async def test_task_processing_speed(self, performance_agent, benchmark):
        """Benchmark task processing speed."""
        task_data = {
            "type": "development",
            "content": "Implement feature X",
            "priority": "high"
        }

        # Benchmark the task processing
        result = await benchmark(performance_agent.process_task, task_data)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, performance_agent):
        """Test concurrent task processing."""
        tasks = [
            {"type": "development", "content": f"Task {i}", "priority": "medium"}
            for i in range(10)
        ]

        # Process tasks concurrently
        results = await asyncio.gather(*[
            performance_agent.process_task(task) for task in tasks
        ])

        assert len(results) == 10
        assert all(result["success"] for result in results)
        assert performance_agent.performance_metrics["tasks_completed"] == 10


if __name__ == "__main__":
    pytest.main([__file__])