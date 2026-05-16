"""
Startup planner for generating tasks and managing project planning.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from random import choice, randint

from ..agents.base_agent import BaseAgent
from ..utils.constants import TaskType, StartupStage
from ..utils.logger import LoggerMixin


class StartupPlanner(LoggerMixin):
    """Planner for generating tasks and managing startup planning."""

    def __init__(self):
        self.current_stage = StartupStage.IDEA
        self.planned_tasks: List[Dict[str, Any]] = []
        self.completed_milestones: List[Dict[str, Any]] = []
        self.upcoming_milestones: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize the startup planner."""
        self.logger.info("Startup planner initialized")
        await self._initialize_milestones()

    async def _initialize_milestones(self):
        """Initialize default milestones for startup stages."""
        self.upcoming_milestones = [
            {
                "name": "Market Validation",
                "stage": StartupStage.IDEA,
                "description": "Validate market need and customer interest",
                "estimated_completion": datetime.now() + timedelta(days=30),
                "tasks_required": ["market_research", "customer_interviews"]
            },
            {
                "name": "MVP Development",
                "stage": StartupStage.IDEA,
                "description": "Build and test minimum viable product",
                "estimated_completion": datetime.now() + timedelta(days=90),
                "tasks_required": ["product_design", "technical_development"]
            },
            {
                "name": "Beta Launch",
                "stage": StartupStage.MVP,
                "description": "Launch beta version to initial users",
                "estimated_completion": datetime.now() + timedelta(days=150),
                "tasks_required": ["user_testing", "marketing_prep"]
            },
            {
                "name": "Full Launch",
                "stage": StartupStage.BETA,
                "description": "Official product launch",
                "estimated_completion": datetime.now() + timedelta(days=210),
                "tasks_required": ["marketing_campaign", "sales_setup"]
            }
        ]

    async def generate_tasks(
        self,
        agents: List[BaseAgent],
        cycle_number: int
    ) -> List[Dict[str, Any]]:
        """Generate tasks for the current simulation cycle."""
        tasks = []

        # Generate routine tasks based on cycle
        routine_tasks = await self._generate_routine_tasks(cycle_number)
        tasks.extend(routine_tasks)

        # Generate milestone-based tasks
        milestone_tasks = await self._generate_milestone_tasks()
        tasks.extend(milestone_tasks)

        # Generate opportunistic tasks based on agent availability and needs
        opportunistic_tasks = await self._generate_opportunistic_tasks(agents)
        tasks.extend(opportunistic_tasks)

        # Prioritize tasks
        prioritized_tasks = await self._prioritize_tasks(tasks)

        self.logger.info(f"Generated {len(prioritized_tasks)} tasks for cycle {cycle_number}")
        return prioritized_tasks

    async def _generate_routine_tasks(self, cycle_number: int) -> List[Dict[str, Any]]:
        """Generate routine tasks that occur regularly."""
        tasks = []

        # Weekly planning (every 7 cycles)
        if cycle_number % 7 == 0:
            tasks.append({
                "id": f"planning_{cycle_number}",
                "type": TaskType.PLANNING,
                "content": "Conduct weekly planning session and review progress",
                "priority": "high",
                "agent_preference": "ceo"
            })

        # Daily standup simulation (every cycle)
        tasks.append({
            "id": f"standup_{cycle_number}",
            "type": TaskType.PLANNING,
            "content": "Daily standup: Share progress, blockers, and plans",
            "priority": "medium",
            "agent_preference": "all"
        })

        # Engineering tasks (frequent)
        if cycle_number % 3 == 0:
            tasks.append({
                "id": f"engineering_{cycle_number}",
                "type": TaskType.DEVELOPMENT,
                "content": "Continue product development and feature implementation",
                "priority": "high",
                "agent_preference": "engineer"
            })

        # Marketing tasks (periodic)
        if cycle_number % 5 == 0:
            tasks.append({
                "id": f"marketing_{cycle_number}",
                "type": TaskType.MARKETING,
                "content": "Execute marketing activities and customer outreach",
                "priority": "medium",
                "agent_preference": "marketer"
            })

        return tasks

    async def _generate_milestone_tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks based on upcoming milestones."""
        tasks = []

        for milestone in self.upcoming_milestones[:2]:  # Focus on next 2 milestones
            if datetime.now() >= milestone["estimated_completion"] - timedelta(days=7):
                # Milestone is approaching, generate preparation tasks
                for task_type in milestone["tasks_required"]:
                    task = {
                        "id": f"milestone_{milestone['name'].lower().replace(' ', '_')}_{task_type}",
                        "type": self._map_task_type(task_type),
                        "content": f"Prepare for milestone '{milestone['name']}': {task_type.replace('_', ' ')}",
                        "priority": "high",
                        "milestone": milestone["name"]
                    }
                    tasks.append(task)

        return tasks

    async def _generate_opportunistic_tasks(self, agents: List[BaseAgent]) -> List[Dict[str, Any]]:
        """Generate tasks based on current context and agent states."""
        tasks = []

        # Check agent performance and generate improvement tasks
        for agent in agents:
            status = await agent.get_status()
            metrics = status.get("performance_metrics", {})

            # If agent has low success rate, generate coaching task
            if metrics.get("success_rate", 1.0) < 0.7:
                tasks.append({
                    "id": f"coaching_{agent.name.lower()}",
                    "type": TaskType.PLANNING,
                    "content": f"Provide coaching and support to {agent.name}",
                    "priority": "medium",
                    "target_agent": agent.name
                })

        # Generate collaborative tasks when multiple agents are available
        if len(agents) >= 3:
            tasks.append({
                "id": f"collaboration_{randint(1000, 9999)}",
                "type": TaskType.DEBATE,
                "content": "Conduct cross-functional collaboration session",
                "priority": "medium",
                "participants": [agent.name for agent in agents[:3]]
            })

        return tasks

    async def _prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize tasks based on various factors."""
        # Simple prioritization logic
        priority_weights = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }

        for task in tasks:
            priority = task.get("priority", "medium")
            weight = priority_weights.get(priority, 2)

            # Boost priority for milestone-related tasks
            if "milestone" in task:
                weight += 1

            # Boost priority for time-sensitive tasks
            if task.get("type") == TaskType.DECISION_MAKING:
                weight += 1

            task["_priority_weight"] = weight

        # Sort by priority weight (descending)
        tasks.sort(key=lambda t: t["_priority_weight"], reverse=True)

        # Remove temporary priority field
        for task in tasks:
            del task["_priority_weight"]

        return tasks

    def _map_task_type(self, task_type_str: str) -> TaskType:
        """Map string task type to TaskType enum."""
        mapping = {
            "planning": TaskType.PLANNING,
            "development": TaskType.DEVELOPMENT,
            "funding": TaskType.FUNDING,
            "legal_review": TaskType.LEGAL_REVIEW,
            "marketing": TaskType.MARKETING,
            "product_strategy": TaskType.PRODUCT_STRATEGY,
            "market_research": TaskType.MARKETING,
            "customer_interviews": TaskType.MARKETING,
            "product_design": TaskType.PRODUCT_STRATEGY,
            "technical_development": TaskType.DEVELOPMENT,
            "user_testing": TaskType.PRODUCT_STRATEGY,
            "marketing_prep": TaskType.MARKETING,
            "marketing_campaign": TaskType.MARKETING,
            "sales_setup": TaskType.MARKETING
        }

        return mapping.get(task_type_str, TaskType.PLANNING)

    async def generate_debate_topic(self, cycle_number: int) -> Optional[str]:
        """Generate a debate topic for the current cycle."""
        debate_topics = [
            "Should we focus on product-market fit or rapid scaling?",
            "What's the best pricing strategy for our product?",
            "Should we bootstrap or seek external funding?",
            "How should we allocate our limited resources?",
            "What's our competitive advantage and how to leverage it?",
            "Should we expand to new markets or deepen current market penetration?",
            "How important is brand building vs. direct sales?",
            "Should we open source parts of our technology?",
            "What's the right balance between innovation and stability?",
            "How should we handle customer feedback and feature requests?"
        ]

        # Generate debate every few cycles
        if cycle_number % 5 == 0:
            return choice(debate_topics)

        return None

    async def update_stage(self, new_stage: StartupStage):
        """Update the current startup stage."""
        old_stage = self.current_stage
        self.current_stage = new_stage

        self.logger.info(f"Startup stage changed from {old_stage.value} to {new_stage.value}")

        # Update milestones based on new stage
        await self._update_milestones_for_stage(new_stage)

    async def _update_milestones_for_stage(self, stage: StartupStage):
        """Update milestones when stage changes."""
        # Mark current stage milestones as completed
        completed = []
        for milestone in self.upcoming_milestones[:]:
            if milestone["stage"] == stage:
                completed.append(milestone)
                self.upcoming_milestones.remove(milestone)

        for milestone in completed:
            milestone["actual_completion"] = datetime.now()
            self.completed_milestones.append(milestone)

        # Add new stage milestones
        if stage == StartupStage.MVP:
            self.upcoming_milestones.append({
                "name": "User Growth",
                "stage": StartupStage.MVP,
                "description": "Achieve sustainable user growth",
                "estimated_completion": datetime.now() + timedelta(days=60),
                "tasks_required": ["user_acquisition", "retention_strategy"]
            })

    def get_current_stage(self) -> StartupStage:
        """Get the current startup stage."""
        return self.current_stage

    def get_milestones(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current milestones."""
        return {
            "completed": self.completed_milestones,
            "upcoming": self.upcoming_milestones
        }

    def get_planner_stats(self) -> Dict[str, Any]:
        """Get planner statistics."""
        return {
            "current_stage": self.current_stage.value,
            "completed_milestones": len(self.completed_milestones),
            "upcoming_milestones": len(self.upcoming_milestones),
            "planned_tasks": len(self.planned_tasks)
        }