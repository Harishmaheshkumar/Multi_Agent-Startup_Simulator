"""
Startup Crew implementation using CrewAI for multi-agent orchestration.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from crewai import Crew, Agent, Task, Process
from langchain_core.tools import Tool

from ..agents.base_agent import BaseAgent
from ..agents.ceo_agent import CEOAgent
from ..agents.engineer_agent import EngineerAgent
from ..agents.investor_agent import InvestorAgent
from ..agents.legal_agent import LegalAgent
from ..agents.marketer_agent import MarketerAgent
from ..agents.product_manager_agent import ProductManagerAgent
from ..llm.model_loader import ModelLoader
from ..memory.memory_manager import MemoryManager
from ..orchestration.debate_engine import DebateEngine
from ..orchestration.discussion_manager import DiscussionManager
from ..orchestration.planner import StartupPlanner
from ..orchestration.startup_scorer import StartupScorer
from ..tools.competitor_analysis import CompetitorAnalysisTool
from ..tools.finance_tool import FinanceTool
from ..tools.market_research import MarketResearchTool
from ..tools.validation_tool import ValidationTool
from ..utils.config import config
from ..utils.constants import AgentRole, TaskType
from ..utils.logger import LoggerMixin


class StartupCrew(LoggerMixin):
    """Main crew class that orchestrates all agents in the startup simulation."""

    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.crew: Optional[Crew] = None
        self.model_loader = ModelLoader()
        self.memory_manager = MemoryManager()
        self.debate_engine = DebateEngine()
        self.discussion_manager = DiscussionManager()
        self.planner = StartupPlanner()
        self.scorer = StartupScorer()

        # Tools
        self.tools = self._initialize_tools()

        # State
        self.is_active = False
        self.current_cycle = 0
        self.start_time: Optional[datetime] = None
        self.tasks_completed = 0

    async def initialize(self):
        """Initialize the startup crew and all agents."""
        self.logger.info("Initializing Startup Crew...")

        try:
            # Ensure an LLM provider is available
            if not self.model_loader.default_provider:
                raise RuntimeError(
                    "No available LLM provider configured. Check OLLAMA_BASE_URL."
                )
            await self.model_loader.generate_response("Test system initialization")

            # Initialize memory manager
            await self.memory_manager.get_memory_stats()

            # Create agents
            await self._create_agents()

            # Initialize CrewAI crew
            self._create_crew()

            # Initialize orchestration components
            await self.debate_engine.initialize()
            await self.discussion_manager.initialize()
            await self.planner.initialize()
            await self.scorer.initialize()

            self.logger.info("Startup Crew initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing Startup Crew: {e}")
            raise

    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize all available tools."""
        tools = {}

        try:
            tools["competitor_analysis"] = CompetitorAnalysisTool()
            tools["finance"] = FinanceTool()
            tools["market_research"] = MarketResearchTool()
            tools["validation"] = ValidationTool()
        except Exception as e:
            self.logger.warning(f"Error initializing tools: {e}")

        return tools

    async def _create_agents(self):
        """Create and initialize all agents."""
        agent_configs = [
            (CEOAgent, AgentRole.CEO),
            (EngineerAgent, AgentRole.ENGINEER),
            (InvestorAgent, AgentRole.INVESTOR),
            (LegalAgent, AgentRole.LEGAL),
            (MarketerAgent, AgentRole.MARKETER),
            (ProductManagerAgent, AgentRole.PRODUCT_MANAGER)
        ]

        for agent_class, role in agent_configs:
            try:
                agent = agent_class(
                    model_loader=self.model_loader,
                    memory_manager=self.memory_manager,
                    config={"role": role.value}
                )
                self.agents.append(agent)
                self.logger.info(f"Created agent: {agent.name} ({role.value})")
            except Exception as e:
                self.logger.error(f"Error creating {role.value} agent: {e}")

    def _create_crew(self):
        """Create the CrewAI crew with agents and tasks."""
        try:
            # Convert our agents to CrewAI agents
            crewai_agents = []
            for agent in self.agents:
                crewai_agent = Agent(
                    role=agent.role.value,
                    goal=f"Act as a {agent.role.value} in a startup simulation",
                    backstory=f"You are {agent.name}, a {agent.role.value} agent in a multi-agent startup simulation.",
                    allow_delegation=True,
                    verbose=config.verbose
                )
                crewai_agents.append(crewai_agent)

            # Create crew
            self.crew = Crew(
                agents=crewai_agents,
                tasks=[],  # Tasks will be added dynamically
                verbose=config.verbose,
                process=Process.sequential
            )

        except Exception as e:
            self.logger.error(f"Error creating CrewAI crew: {e}")

    async def start(self):
        """Start the simulation."""
        if self.is_active:
            self.logger.warning("Simulation is already running")
            return

        self.is_active = True
        self.start_time = datetime.now()
        self.current_cycle = 0

        self.logger.info("Starting startup simulation...")

        # Start background task loop
        asyncio.create_task(self._simulation_loop())

    async def stop(self):
        """Stop the simulation."""
        self.is_active = False
        self.logger.info("Stopping startup simulation...")

    async def reset(self):
        """Reset the simulation."""
        await self.stop()
        self.current_cycle = 0
        self.tasks_completed = 0
        self.start_time = None

        # Reset agents
        for agent in self.agents:
            agent.current_task = None
            agent.performance_metrics = {
                "tasks_completed": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "collaboration_score": 0.0
            }

        self.logger.info("Simulation reset")

    async def _simulation_loop(self):
        """Main simulation loop."""
        while self.is_active:
            try:
                await self.run_cycle()
                self.current_cycle += 1

                # Wait before next cycle
                await asyncio.sleep(config.simulation_interval)

            except Exception as e:
                self.logger.error(f"Error in simulation cycle: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def run_cycle(self):
        """Run one simulation cycle."""
        self.logger.info(f"Running simulation cycle {self.current_cycle + 1}")

        try:
            # Generate tasks for this cycle
            tasks = await self.planner.generate_tasks(self.agents, self.current_cycle)

            # Execute tasks
            for task in tasks:
                await self._execute_task(task)

            # Run debate/discussion if needed
            if self.current_cycle % 5 == 0:  # Every 5 cycles
                await self._run_debate_session()

            # Score and evaluate progress
            await self.scorer.evaluate_progress(self.agents, self.current_cycle)

        except Exception as e:
            self.logger.error(f"Error running simulation cycle: {e}")

    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a single task."""
        try:
            # Find appropriate agent
            agent = self._find_agent_for_task(task)
            if not agent:
                self.logger.warning(f"No suitable agent found for task: {task.get('type')}")
                return

            # Execute task
            start_time = datetime.now()
            result = await agent.process_task(task)
            end_time = datetime.now()

            # Update metrics
            agent.performance_metrics["tasks_completed"] += 1
            response_time = (end_time - start_time).total_seconds()
            agent.performance_metrics["average_response_time"] = (
                (agent.performance_metrics["average_response_time"] +
                 response_time) / 2
            )

            self.tasks_completed += 1

            self.logger.info(f"Task completed: {task.get('type')} by {agent.name}")

        except Exception as e:
            self.logger.error(f"Error executing task: {e}")

    def _find_agent_for_task(self, task: Dict[str, Any]) -> Optional[BaseAgent]:
        """Find the most appropriate agent for a task."""
        task_type = task.get("type", "")

        # Map task types to agent roles
        task_agent_mapping = {
            TaskType.PLANNING: AgentRole.CEO,
            TaskType.DECISION_MAKING: AgentRole.CEO,
            TaskType.DEVELOPMENT: AgentRole.ENGINEER,
            TaskType.FUNDING: AgentRole.INVESTOR,
            TaskType.LEGAL_REVIEW: AgentRole.LEGAL,
            TaskType.MARKETING: AgentRole.MARKETER,
            TaskType.PRODUCT_STRATEGY: AgentRole.PRODUCT_MANAGER,
        }

        preferred_role = task_agent_mapping.get(task_type)

        if preferred_role:
            for agent in self.agents:
                if agent.role == preferred_role:
                    return agent

        # Fallback: return first available agent
        return self.agents[0] if self.agents else None

    async def _run_debate_session(self):
        """Run a debate session among agents."""
        try:
            debate_topic = await self.planner.generate_debate_topic(self.current_cycle)

            if debate_topic:
                self.logger.info(f"Running debate session: {debate_topic}")

                # Run debate
                debate_result = await self.debate_engine.run_debate(
                    self.agents, debate_topic
                )

                # Store debate results
                await self.discussion_manager.store_discussion(debate_result)

        except Exception as e:
            self.logger.error(f"Error running debate session: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the crew."""
        agent_statuses = []
        for agent in self.agents:
            status = await agent.get_status()
            agent_statuses.append(status)

        return {
            "is_active": self.is_active,
            "current_cycle": self.current_cycle,
            "tasks_completed": self.tasks_completed,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "agents": agent_statuses,
            "memory_stats": await self.memory_manager.get_memory_stats()
        }

    async def add_custom_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Add a custom task to the simulation."""
        task_id = f"custom_task_{datetime.now().timestamp()}"

        custom_task = {
            "id": task_id,
            "type": task.get("type", "custom"),
            "content": task.get("content", ""),
            "priority": task.get("priority", "medium"),
            "metadata": task.get("metadata", {}),
            "created_at": datetime.now().isoformat()
        }

        # Execute immediately
        result = await self._execute_task(custom_task)

        return {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }