"""
Task definitions for the startup crew.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from crewai import Task
from ..utils.constants import TaskType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StartupTask(Task):
    """Custom task class for startup simulation."""

    def __init__(
        self,
        description: str,
        agent_role: str,
        task_type: TaskType,
        priority: str = "medium",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            description=description,
            agent=agent_role,
            **kwargs
        )

        self.task_type = task_type
        self.priority = priority
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "description": self.description,
            "agent_role": self.agent,
            "task_type": self.task_type.value,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StartupTask':
        """Create task from dictionary."""
        return cls(
            description=data["description"],
            agent_role=data["agent_role"],
            task_type=TaskType(data["task_type"]),
            priority=data.get("priority", "medium"),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {})
        )


def create_planning_task(content: str, priority: str = "high") -> StartupTask:
    """Create a strategic planning task."""
    return StartupTask(
        description=f"Develop strategic plan for: {content}",
        agent_role="ceo",
        task_type=TaskType.PLANNING,
        priority=priority,
        metadata={"domain": "strategy", "content": content}
    )


def create_development_task(content: str, priority: str = "medium") -> StartupTask:
    """Create a development task."""
    return StartupTask(
        description=f"Implement technical solution for: {content}",
        agent_role="engineer",
        task_type=TaskType.DEVELOPMENT,
        priority=priority,
        metadata={"domain": "technical", "content": content}
    )


def create_funding_task(content: str, priority: str = "high") -> StartupTask:
    """Create a funding/investment task."""
    return StartupTask(
        description=f"Evaluate funding opportunities for: {content}",
        agent_role="investor",
        task_type=TaskType.FUNDING,
        priority=priority,
        metadata={"domain": "financial", "content": content}
    )


def create_legal_task(content: str, priority: str = "medium") -> StartupTask:
    """Create a legal review task."""
    return StartupTask(
        description=f"Review legal aspects of: {content}",
        agent_role="legal",
        task_type=TaskType.LEGAL_REVIEW,
        priority=priority,
        metadata={"domain": "legal", "content": content}
    )


def create_marketing_task(content: str, priority: str = "medium") -> StartupTask:
    """Create a marketing task."""
    return StartupTask(
        description=f"Develop marketing strategy for: {content}",
        agent_role="marketer",
        task_type=TaskType.MARKETING,
        priority=priority,
        metadata={"domain": "marketing", "content": content}
    )


def create_product_task(content: str, priority: str = "medium") -> StartupTask:
    """Create a product management task."""
    return StartupTask(
        description=f"Define product requirements for: {content}",
        agent_role="product_manager",
        task_type=TaskType.PRODUCT_STRATEGY,
        priority=priority,
        metadata={"domain": "product", "content": content}
    )


def create_debate_task(topic: str, participants: List[str]) -> StartupTask:
    """Create a debate task."""
    return StartupTask(
        description=f"Participate in debate on: {topic}",
        agent_role="ceo",  # Debate coordinator
        task_type=TaskType.DEBATE,
        priority="medium",
        metadata={
            "domain": "debate",
            "topic": topic,
            "participants": participants
        }
    )


def create_decision_task(content: str, options: List[str], priority: str = "high") -> StartupTask:
    """Create a decision-making task."""
    return StartupTask(
        description=f"Make decision regarding: {content}",
        agent_role="ceo",
        task_type=TaskType.DECISION_MAKING,
        priority=priority,
        metadata={
            "domain": "decision",
            "content": content,
            "options": options
        }
    )


class TaskManager:
    """Manager for handling tasks in the startup simulation."""

    def __init__(self):
        self.tasks: Dict[str, StartupTask] = {}
        self.task_counter = 0

    def create_task_id(self) -> str:
        """Generate a unique task ID."""
        self.task_counter += 1
        return f"task_{self.task_counter}"

    def add_task(self, task: StartupTask) -> str:
        """Add a task to the manager."""
        task_id = self.create_task_id()
        self.tasks[task_id] = task
        logger.info(f"Added task: {task_id} - {task.description}")
        return task_id

    def get_task(self, task_id: str) -> Optional[StartupTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[StartupTask]:
        """Get all pending tasks."""
        return [task for task in self.tasks.values() if task.status == "pending"]

    def get_completed_tasks(self) -> List[StartupTask]:
        """Get all completed tasks."""
        return [task for task in self.tasks.values() if task.status == "completed"]

    def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """Update task status."""
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            if status == "completed":
                task.completed_at = datetime.now()
            task.result = result
            logger.info(f"Updated task {task_id} status to {status}")

    def get_tasks_by_agent(self, agent_role: str) -> List[StartupTask]:
        """Get tasks assigned to a specific agent role."""
        return [task for task in self.tasks.values() if task.agent == agent_role]

    def get_tasks_by_type(self, task_type: TaskType) -> List[StartupTask]:
        """Get tasks of a specific type."""
        return [task for task in self.tasks.values() if task.task_type == task_type]

    def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        total = len(self.tasks)
        pending = len(self.get_pending_tasks())
        completed = len(self.get_completed_tasks())

        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "completed_tasks": completed,
            "completion_rate": completed / total if total > 0 else 0
        }