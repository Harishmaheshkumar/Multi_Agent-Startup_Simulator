"""
Tests for workflow functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from ..crew.startup_crew import StartupCrew
from ..crew.tasks import TaskManager, StartupTask
from ..crew.workflows import WorkflowManager
from ..orchestration.planner import StartupPlanner
from ..orchestration.debate_engine import DebateEngine
from ..orchestration.discussion_manager import DiscussionManager
from ..agents.base_agent import BaseAgent
from ..utils.constants import AgentRole, TaskType, StartupStage


class TestTaskManager:
    """Test cases for TaskManager class."""

    @pytest.fixture
    def task_manager(self):
        """Create a task manager instance."""
        return TaskManager()

    def test_task_manager_initialization(self, task_manager):
        """Test task manager initialization."""
        assert task_manager.tasks == []
        assert task_manager.task_counter == 0

    def test_create_task(self, task_manager):
        """Test task creation."""
        task_data = {
            "type": TaskType.PLANNING,
            "content": "Plan company strategy",
            "priority": "high",
            "assigned_to": "ceo_1"
        }

        task = task_manager.create_task(**task_data)

        assert task.task_id.startswith("task_")
        assert task.type == TaskType.PLANNING
        assert task.content == "Plan company strategy"
        assert task.priority == "high"
        assert task.assigned_to == "ceo_1"
        assert task.status == "pending"

    def test_add_task(self, task_manager):
        """Test adding a task."""
        task = StartupTask(
            task_id="test_task_1",
            type=TaskType.DEVELOPMENT,
            content="Develop feature",
            priority="medium"
        )

        task_manager.add_task(task)

        assert len(task_manager.tasks) == 1
        assert task_manager.tasks[0] == task

    def test_get_pending_tasks(self, task_manager):
        """Test getting pending tasks."""
        # Add tasks with different statuses
        task1 = StartupTask("task_1", TaskType.PLANNING, "Task 1", "high")
        task2 = StartupTask("task_2", TaskType.DEVELOPMENT, "Task 2", "medium")
        task2.status = "completed"
        task3 = StartupTask("task_3", TaskType.FUNDING, "Task 3", "low")

        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)

        pending_tasks = task_manager.get_pending_tasks()

        assert len(pending_tasks) == 2
        assert task1 in pending_tasks
        assert task3 in pending_tasks
        assert task2 not in pending_tasks

    def test_get_tasks_by_type(self, task_manager):
        """Test getting tasks by type."""
        task1 = StartupTask("task_1", TaskType.PLANNING, "Planning task", "high")
        task2 = StartupTask("task_2", TaskType.DEVELOPMENT, "Development task", "medium")
        task3 = StartupTask("task_3", TaskType.PLANNING, "Another planning task", "low")

        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)

        planning_tasks = task_manager.get_tasks_by_type(TaskType.PLANNING)

        assert len(planning_tasks) == 2
        assert task1 in planning_tasks
        assert task3 in planning_tasks
        assert task2 not in planning_tasks

    def test_update_task_status(self, task_manager):
        """Test updating task status."""
        task = StartupTask("task_1", TaskType.PLANNING, "Test task", "medium")
        task_manager.add_task(task)

        task_manager.update_task_status("task_1", "completed")

        assert task.status == "completed"
        assert task.completed_at is not None

    def test_get_task_stats(self, task_manager):
        """Test getting task statistics."""
        # Add various tasks
        tasks_data = [
            ("planning", "high", "pending"),
            ("development", "medium", "completed"),
            ("funding", "high", "in_progress"),
            ("marketing", "low", "completed"),
            ("planning", "medium", "pending")
        ]

        for i, (task_type, priority, status) in enumerate(tasks_data):
            task = StartupTask(f"task_{i}", TaskType(task_type), f"Task {i}", priority)
            task.status = status
            task_manager.add_task(task)

        stats = task_manager.get_task_stats()

        assert stats["total_tasks"] == 5
        assert stats["pending"] == 2
        assert stats["completed"] == 2
        assert stats["in_progress"] == 1
        assert stats["by_type"]["planning"] == 2
        assert stats["by_priority"]["high"] == 2


class TestWorkflowManager:
    """Test cases for WorkflowManager class."""

    @pytest.fixture
    def workflow_manager(self):
        """Create a workflow manager instance."""
        return WorkflowManager()

    def test_workflow_manager_initialization(self, workflow_manager):
        """Test workflow manager initialization."""
        assert workflow_manager.workflows == {}
        assert workflow_manager.workflow_counter == 0

    def test_create_workflow(self, workflow_manager):
        """Test workflow creation."""
        workflow_data = {
            "name": "Startup Foundation",
            "description": "Initial startup setup workflow",
            "stages": [StartupStage.IDEA, StartupStage.MVP]
        }

        workflow = workflow_manager.create_workflow(**workflow_data)

        assert workflow.workflow_id.startswith("workflow_")
        assert workflow.name == "Startup Foundation"
        assert workflow.description == "Initial startup setup workflow"
        assert workflow.stages == [StartupStage.IDEA, StartupStage.MVP]
        assert workflow.status == "created"

    def test_add_workflow(self, workflow_manager):
        """Test adding a workflow."""
        from ..crew.workflows import StartupWorkflow

        workflow = StartupWorkflow(
            workflow_id="test_workflow_1",
            name="Test Workflow",
            description="Test description",
            stages=[StartupStage.IDEA]
        )

        workflow_manager.add_workflow(workflow)

        assert "test_workflow_1" in workflow_manager.workflows
        assert workflow_manager.workflows["test_workflow_1"] == workflow

    def test_get_workflow(self, workflow_manager):
        """Test getting a workflow."""
        workflow = workflow_manager.create_workflow(
            name="Test Workflow",
            description="Test",
            stages=[StartupStage.IDEA]
        )

        retrieved = workflow_manager.get_workflow(workflow.workflow_id)

        assert retrieved == workflow

    def test_update_workflow_status(self, workflow_manager):
        """Test updating workflow status."""
        workflow = workflow_manager.create_workflow(
            name="Test Workflow",
            description="Test",
            stages=[StartupStage.IDEA]
        )

        workflow_manager.update_workflow_status(workflow.workflow_id, "in_progress")

        assert workflow.status == "in_progress"

    def test_get_active_workflows(self, workflow_manager):
        """Test getting active workflows."""
        workflow1 = workflow_manager.create_workflow(
            name="Workflow 1", description="Test 1", stages=[StartupStage.IDEA]
        )
        workflow2 = workflow_manager.create_workflow(
            name="Workflow 2", description="Test 2", stages=[StartupStage.MVP]
        )
        workflow3 = workflow_manager.create_workflow(
            name="Workflow 3", description="Test 3", stages=[StartupStage.SCALE]
        )

        workflow1.status = "completed"
        workflow2.status = "in_progress"
        workflow3.status = "in_progress"

        active_workflows = workflow_manager.get_active_workflows()

        assert len(active_workflows) == 2
        assert workflow2 in active_workflows
        assert workflow3 in active_workflows
        assert workflow1 not in active_workflows


class TestStartupPlanner:
    """Test cases for StartupPlanner class."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents."""
        agents = []
        for role in [AgentRole.CEO, AgentRole.ENGINEER, AgentRole.MARKETER]:
            agent = Mock(spec=BaseAgent)
            agent.name = f"{role.value.title()} Agent"
            agent.role = role
            agent.is_active = True
            agent.process_task = AsyncMock(return_value={"success": True, "response": "Task completed"})
            agents.append(agent)
        return agents

    @pytest.fixture
    def planner(self, mock_agents):
        """Create a startup planner instance."""
        return StartupPlanner(agents=mock_agents)

    @pytest.mark.asyncio
    async def test_planner_initialization(self, planner, mock_agents):
        """Test planner initialization."""
        assert planner.agents == mock_agents
        assert planner.current_stage == StartupStage.IDEA

    @pytest.mark.asyncio
    async def test_generate_tasks_for_stage(self, planner):
        """Test generating tasks for a stage."""
        tasks = await planner.generate_tasks(StartupStage.IDEA)

        assert isinstance(tasks, list)
        assert len(tasks) > 0

        # Check that tasks have required fields
        for task in tasks:
            assert "type" in task
            assert "content" in task
            assert "priority" in task

    @pytest.mark.asyncio
    async def test_advance_stage(self, planner):
        """Test advancing to next stage."""
        initial_stage = planner.current_stage

        await planner.advance_stage()

        # Should advance from IDEA to MVP
        assert planner.current_stage == StartupStage.MVP

    @pytest.mark.asyncio
    async def test_get_stage_requirements(self, planner):
        """Test getting stage requirements."""
        requirements = planner.get_stage_requirements(StartupStage.IDEA)

        assert isinstance(requirements, dict)
        assert "tasks" in requirements
        assert "success_criteria" in requirements


class TestDebateEngine:
    """Test cases for DebateEngine class."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for debate."""
        agents = []
        for i in range(3):
            agent = Mock(spec=BaseAgent)
            agent.name = f"Agent {i+1}"
            agent.role = AgentRole.CEO if i == 0 else AgentRole.ENGINEER
            agent.collaborate = AsyncMock(return_value=f"Debate response from {agent.name}")
            agents.append(agent)
        return agents

    @pytest.fixture
    def debate_engine(self, mock_agents):
        """Create a debate engine instance."""
        return DebateEngine(agents=mock_agents)

    @pytest.mark.asyncio
    async def test_debate_initialization(self, debate_engine, mock_agents):
        """Test debate engine initialization."""
        assert debate_engine.agents == mock_agents
        assert debate_engine.max_rounds == 5

    @pytest.mark.asyncio
    async def test_run_debate(self, debate_engine):
        """Test running a debate."""
        topic = "Should we focus on B2B or B2C market?"

        result = await debate_engine.run_debate(topic)

        assert "topic" in result
        assert "rounds" in result
        assert "conclusion" in result
        assert "participants" in result
        assert result["topic"] == topic
        assert len(result["rounds"]) > 0

    @pytest.mark.asyncio
    async def test_debate_round(self, debate_engine):
        """Test a single debate round."""
        topic = "Test debate topic"

        round_result = await debate_engine._run_debate_round(topic, round_num=1)

        assert "round" in round_result
        assert "responses" in round_result
        assert round_result["round"] == 1
        assert len(round_result["responses"]) == len(debate_engine.agents)


class TestDiscussionManager:
    """Test cases for DiscussionManager class."""

    @pytest.fixture
    def discussion_manager(self):
        """Create a discussion manager instance."""
        return DiscussionManager()

    def test_discussion_manager_initialization(self, discussion_manager):
        """Test discussion manager initialization."""
        assert discussion_manager.discussions == []
        assert discussion_manager.active_discussions == {}

    def test_start_discussion(self, discussion_manager):
        """Test starting a discussion."""
        topic = "Product Strategy Discussion"
        participants = ["ceo_1", "engineer_1", "marketer_1"]

        discussion = discussion_manager.start_discussion(topic, participants)

        assert discussion.topic == topic
        assert discussion.participants == participants
        assert discussion.status == "active"
        assert discussion.discussion_id in discussion_manager.active_discussions

    def test_add_message_to_discussion(self, discussion_manager):
        """Test adding a message to discussion."""
        discussion = discussion_manager.start_discussion("Test", ["agent1"])

        message = {
            "sender": "agent1",
            "content": "Test message",
            "timestamp": datetime.now()
        }

        discussion_manager.add_message_to_discussion(discussion.discussion_id, message)

        assert len(discussion.messages) == 1
        assert discussion.messages[0] == message

    def test_end_discussion(self, discussion_manager):
        """Test ending a discussion."""
        discussion = discussion_manager.start_discussion("Test", ["agent1"])

        discussion_manager.end_discussion(discussion.discussion_id)

        assert discussion.status == "completed"
        assert discussion.discussion_id not in discussion_manager.active_discussions

    def test_get_discussion_summary(self, discussion_manager):
        """Test getting discussion summary."""
        discussion = discussion_manager.start_discussion("Test Topic", ["agent1", "agent2"])

        # Add some messages
        messages = [
            {"sender": "agent1", "content": "Point 1", "timestamp": datetime.now()},
            {"sender": "agent2", "content": "Counterpoint", "timestamp": datetime.now()},
            {"sender": "agent1", "content": "Rebuttal", "timestamp": datetime.now()}
        ]

        for msg in messages:
            discussion_manager.add_message_to_discussion(discussion.discussion_id, msg)

        summary = discussion_manager.get_discussion_summary(discussion.discussion_id)

        assert summary["topic"] == "Test Topic"
        assert summary["total_messages"] == 3
        assert summary["participants"] == ["agent1", "agent2"]
        assert summary["status"] == "active"


class TestWorkflowIntegration:
    """Integration tests for workflow components."""

    @pytest.fixture
    async def integrated_system(self):
        """Create an integrated workflow system."""
        # Mock agents
        agents = []
        for role in [AgentRole.CEO, AgentRole.ENGINEER, AgentRole.MARKETER]:
            agent = Mock(spec=BaseAgent)
            agent.name = f"{role.value.title()} Agent"
            agent.role = role
            agent.agent_id = f"{role.value}_1"
            agent.is_active = True
            agent.process_task = AsyncMock(return_value={"success": True, "response": "Task done"})
            agents.append(agent)

        # Create components
        task_manager = TaskManager()
        workflow_manager = WorkflowManager()
        planner = StartupPlanner(agents=agents)
        debate_engine = DebateEngine(agents=agents)
        discussion_manager = DiscussionManager()

        return {
            "agents": agents,
            "task_manager": task_manager,
            "workflow_manager": workflow_manager,
            "planner": planner,
            "debate_engine": debate_engine,
            "discussion_manager": discussion_manager
        }

    @pytest.mark.asyncio
    async def test_full_workflow_cycle(self, integrated_system):
        """Test a full workflow cycle."""
        components = integrated_system

        # Start with planning stage
        tasks = await components["planner"].generate_tasks(StartupStage.IDEA)

        # Add tasks to manager
        for task_data in tasks:
            task = components["task_manager"].create_task(**task_data)
            components["task_manager"].add_task(task)

        # Verify tasks were created
        pending_tasks = components["task_manager"].get_pending_tasks()
        assert len(pending_tasks) > 0

        # Create a workflow
        workflow = components["workflow_manager"].create_workflow(
            name="Integration Test Workflow",
            description="Test workflow",
            stages=[StartupStage.IDEA, StartupStage.MVP]
        )

        assert workflow.name == "Integration Test Workflow"

    @pytest.mark.asyncio
    async def test_debate_and_discussion_integration(self, integrated_system):
        """Test debate and discussion integration."""
        components = integrated_system

        # Start a discussion
        discussion = components["discussion_manager"].start_discussion(
            "Strategy Discussion",
            [agent.agent_id for agent in components["agents"]]
        )

        # Run a debate
        debate_result = await components["debate_engine"].run_debate(
            "What should be our main product focus?"
        )

        # Add debate conclusion to discussion
        conclusion_message = {
            "sender": "debate_engine",
            "content": f"Debate concluded: {debate_result['conclusion']}",
            "timestamp": datetime.now()
        }

        components["discussion_manager"].add_message_to_discussion(
            discussion.discussion_id,
            conclusion_message
        )

        # Verify integration
        summary = components["discussion_manager"].get_discussion_summary(discussion.discussion_id)
        assert summary["total_messages"] == 1
        assert "Debate concluded" in summary["messages"][0]["content"]


if __name__ == "__main__":
    pytest.main([__file__])