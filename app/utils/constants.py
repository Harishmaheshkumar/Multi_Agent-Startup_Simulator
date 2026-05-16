"""
Constants used throughout the Multi-Agent Startup Simulator.
"""

from enum import Enum
from typing import Dict, List


class AgentRole(str, Enum):
    """Agent roles in the startup simulation."""
    CEO = "ceo"
    ENGINEER = "engineer"
    INVESTOR = "investor"
    LEGAL = "legal"
    MARKETER = "marketer"
    PRODUCT_MANAGER = "product_manager"


class TaskType(str, Enum):
    """Types of tasks in the simulation."""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    FUNDING = "funding"
    LEGAL_REVIEW = "legal_review"
    MARKETING = "marketing"
    PRODUCT_STRATEGY = "product_strategy"
    DEBATE = "debate"
    DECISION_MAKING = "decision_making"


class MemoryType(str, Enum):
    """Types of memory storage."""
    CONVERSATION = "conversation"
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    EPISODIC = "episodic"


class StartupStage(str, Enum):
    """Stages of startup development."""
    IDEA = "idea"
    MVP = "mvp"
    PROTOTYPE = "prototype"
    BETA = "beta"
    LAUNCH = "launch"
    GROWTH = "growth"
    SCALE = "scale"


class DecisionType(str, Enum):
    """Types of decisions made in the simulation."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    FINANCIAL = "financial"
    LEGAL = "legal"
    MARKETING = "marketing"


# Agent capabilities and responsibilities
AGENT_CAPABILITIES: Dict[AgentRole, List[str]] = {
    AgentRole.CEO: [
        "Strategic planning",
        "Team leadership",
        "Vision setting",
        "Stakeholder management",
        "Crisis management"
    ],
    AgentRole.ENGINEER: [
        "Technical architecture",
        "Code development",
        "System design",
        "Quality assurance",
        "Technical debt management"
    ],
    AgentRole.INVESTOR: [
        "Financial analysis",
        "Risk assessment",
        "Valuation modeling",
        "Due diligence",
        "Investment strategy"
    ],
    AgentRole.LEGAL: [
        "Contract review",
        "Compliance checking",
        "Intellectual property",
        "Regulatory compliance",
        "Legal risk assessment"
    ],
    AgentRole.MARKETER: [
        "Market research",
        "Brand strategy",
        "Customer acquisition",
        "Marketing campaigns",
        "Competitive analysis"
    ],
    AgentRole.PRODUCT_MANAGER: [
        "Product roadmap",
        "Feature prioritization",
        "User research",
        "Requirements gathering",
        "Product metrics"
    ]
}

# Task priorities
TASK_PRIORITIES = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4
}

# Simulation parameters
SIMULATION_CONSTANTS = {
    "max_agents_per_task": 3,
    "debate_rounds": 3,
    "consensus_threshold": 0.7,
    "memory_retention_days": 30,
    "max_conversation_length": 1000
}

# API endpoints
API_ENDPOINTS = {
    "agents": "/api/agents",
    "tasks": "/api/tasks",
    "simulation": "/api/simulation",
    "memory": "/api/memory",
    "metrics": "/api/metrics"
}

# File extensions
SUPPORTED_EXTENSIONS = {
    "code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"],
    "config": [".json", ".yaml", ".yml", ".toml", ".ini"],
    "docs": [".md", ".txt", ".rst", ".adoc"]
}