"""
Workflow definitions for the startup crew.
"""

from typing import Any, Dict, List, Optional
from enum import Enum

from .tasks import StartupTask, TaskManager
from ..utils.constants import TaskType, StartupStage
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowType(str, Enum):
    """Types of workflows."""
    STARTUP_FOUNDATION = "startup_foundation"
    PRODUCT_DEVELOPMENT = "product_development"
    FUNDING_ROUND = "funding_round"
    MARKET_EXPANSION = "market_expansion"
    CRISIS_MANAGEMENT = "crisis_management"
    EXIT_STRATEGY = "exit_strategy"


class StartupWorkflow:
    """Represents a workflow of related tasks."""

    def __init__(
        self,
        workflow_type: WorkflowType,
        name: str,
        description: str,
        tasks: List[StartupTask],
        dependencies: Optional[Dict[str, List[str]]] = None
    ):
        self.workflow_type = workflow_type
        self.name = name
        self.description = description
        self.tasks = tasks
        self.dependencies = dependencies or {}
        self.status = "pending"
        self.current_task_index = 0
        self.results: Dict[str, Any] = {}

    def get_next_task(self) -> Optional[StartupTask]:
        """Get the next task to execute."""
        if self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None

    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """Mark a task as completed and store result."""
        self.results[task_id] = result
        self.current_task_index += 1

    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.current_task_index >= len(self.tasks)

    def get_progress(self) -> float:
        """Get workflow progress as percentage."""
        if not self.tasks:
            return 100.0
        return (self.current_task_index / len(self.tasks)) * 100.0


class WorkflowManager:
    """Manager for handling workflows in the startup simulation."""

    def __init__(self):
        self.workflows: Dict[str, StartupWorkflow] = {}
        self.task_manager = TaskManager()
        self.workflow_counter = 0

    def create_workflow_id(self) -> str:
        """Generate a unique workflow ID."""
        self.workflow_counter += 1
        return f"workflow_{self.workflow_counter}"

    def create_startup_foundation_workflow(self) -> StartupWorkflow:
        """Create a startup foundation workflow."""
        from .tasks import (
            create_planning_task,
            create_product_task,
            create_legal_task,
            create_funding_task
        )

        tasks = [
            create_planning_task(
                "Define company vision, mission, and core values",
                priority="high"
            ),
            create_product_task(
                "Identify target market and customer needs",
                priority="high"
            ),
            create_product_task(
                "Define minimum viable product (MVP) features",
                priority="high"
            ),
            create_legal_task(
                "Set up basic legal structure and IP protection",
                priority="medium"
            ),
            create_funding_task(
                "Assess initial funding requirements and sources",
                priority="medium"
            )
        ]

        return StartupWorkflow(
            workflow_type=WorkflowType.STARTUP_FOUNDATION,
            name="Startup Foundation",
            description="Establish the core foundation of the startup",
            tasks=tasks
        )

    def create_product_development_workflow(self) -> StartupWorkflow:
        """Create a product development workflow."""
        from .tasks import (
            create_product_task,
            create_development_task,
            create_marketing_task
        )

        tasks = [
            create_product_task(
                "Create detailed product requirements and specifications",
                priority="high"
            ),
            create_development_task(
                "Design system architecture and technical specifications",
                priority="high"
            ),
            create_development_task(
                "Implement core product features",
                priority="high"
            ),
            create_development_task(
                "Develop user interface and user experience",
                priority="medium"
            ),
            create_development_task(
                "Implement testing and quality assurance",
                priority="medium"
            ),
            create_marketing_task(
                "Prepare product launch marketing materials",
                priority="medium"
            )
        ]

        return StartupWorkflow(
            workflow_type=WorkflowType.PRODUCT_DEVELOPMENT,
            name="Product Development",
            description="Develop and launch the product",
            tasks=tasks
        )

    def create_funding_round_workflow(self, round_type: str = "seed") -> StartupWorkflow:
        """Create a funding round workflow."""
        from .tasks import (
            create_funding_task,
            create_legal_task,
            create_planning_task
        )

        tasks = [
            create_funding_task(
                f"Prepare {round_type} round investment materials and pitch deck",
                priority="high"
            ),
            create_funding_task(
                f"Identify and qualify potential {round_type} investors",
                priority="high"
            ),
            create_funding_task(
                f"Conduct investor meetings and due diligence",
                priority="high"
            ),
            create_legal_task(
                f"Prepare {round_type} round term sheet and legal documents",
                priority="medium"
            ),
            create_funding_task(
                f"Negotiate and finalize {round_type} investment terms",
                priority="high"
            ),
            create_planning_task(
                f"Plan use of {round_type} funding and milestones",
                priority="medium"
            )
        ]

        return StartupWorkflow(
            workflow_type=WorkflowType.FUNDING_ROUND,
            name=f"{round_type.title()} Funding Round",
            description=f"Execute a {round_type} funding round",
            tasks=tasks
        )

    def create_market_expansion_workflow(self) -> StartupWorkflow:
        """Create a market expansion workflow."""
        from .tasks import (
            create_marketing_task,
            create_product_task,
            create_planning_task
        )

        tasks = [
            create_marketing_task(
                "Analyze new market opportunities and segments",
                priority="high"
            ),
            create_product_task(
                "Adapt product for new market requirements",
                priority="medium"
            ),
            create_marketing_task(
                "Develop market entry strategy and positioning",
                priority="high"
            ),
            create_marketing_task(
                "Execute go-to-market plan and customer acquisition",
                priority="high"
            ),
            create_planning_task(
                "Monitor expansion progress and adjust strategy",
                priority="medium"
            )
        ]

        return StartupWorkflow(
            workflow_type=WorkflowType.MARKET_EXPANSION,
            name="Market Expansion",
            description="Expand into new markets",
            tasks=tasks
        )

    def create_crisis_management_workflow(self, crisis_type: str) -> StartupWorkflow:
        """Create a crisis management workflow."""
        from .tasks import (
            create_planning_task,
            create_legal_task,
            create_marketing_task
        )

        tasks = [
            create_planning_task(
                f"Assess {crisis_type} situation and immediate impacts",
                priority="critical"
            ),
            create_planning_task(
                f"Develop crisis response plan and communication strategy",
                priority="critical"
            ),
            create_legal_task(
                f"Evaluate legal implications and compliance requirements",
                priority="high"
            ),
            create_marketing_task(
                f"Prepare stakeholder communication and reputation management",
                priority="high"
            ),
            create_planning_task(
                f"Implement recovery plan and monitor progress",
                priority="high"
            )
        ]

        return StartupWorkflow(
            workflow_type=WorkflowType.CRISIS_MANAGEMENT,
            name="Crisis Management",
            description=f"Manage {crisis_type} crisis situation",
            tasks=tasks
        )

    def add_workflow(self, workflow: StartupWorkflow) -> str:
        """Add a workflow to the manager."""
        workflow_id = self.create_workflow_id()
        self.workflows[workflow_id] = workflow
        logger.info(f"Added workflow: {workflow_id} - {workflow.name}")
        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[StartupWorkflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_active_workflows(self) -> List[StartupWorkflow]:
        """Get all active (not completed) workflows."""
        return [wf for wf in self.workflows.values() if not wf.is_completed()]

    def get_completed_workflows(self) -> List[StartupWorkflow]:
        """Get all completed workflows."""
        return [wf for wf in self.workflows.values() if wf.is_completed()]

    def execute_workflow_step(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Execute the next step in a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.is_completed():
            return None

        task = workflow.get_next_task()
        if not task:
            return None

        # Add task to task manager
        task_id = self.task_manager.add_task(task)

        # For now, return task info (in real implementation, this would trigger execution)
        return {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "task_description": task.description,
            "agent_role": task.agent,
            "progress": workflow.get_progress()
        }

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        total = len(self.workflows)
        active = len(self.get_active_workflows())
        completed = len(self.get_completed_workflows())

        return {
            "total_workflows": total,
            "active_workflows": active,
            "completed_workflows": completed,
            "completion_rate": completed / total if total > 0 else 0
        }

    def get_workflows_by_type(self, workflow_type: WorkflowType) -> List[StartupWorkflow]:
        """Get workflows of a specific type."""
        return [wf for wf in self.workflows.values() if wf.workflow_type == workflow_type]