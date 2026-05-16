"""
API routes for the Multi-Agent Startup Simulator.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..crew.startup_crew import StartupCrew
from ..utils.constants import AgentRole, TaskType
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Global crew instance (would be managed better in production)
crew_instance: Optional[StartupCrew] = None

def set_crew_instance(crew: StartupCrew):
    """Set the global crew instance."""
    global crew_instance
    crew_instance = crew

# Pydantic models for API
class TaskRequest(BaseModel):
    agent_id: str
    task_type: str
    content: str
    priority: Optional[str] = "medium"
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class AgentStatus(BaseModel):
    agent_id: str
    name: str
    role: str
    is_active: bool
    current_task: Optional[str]
    performance_metrics: Dict[str, Any]
    last_active: str
    created_at: str

class SimulationStatus(BaseModel):
    is_running: bool
    active_agents: int
    completed_tasks: int
    current_cycle: int
    start_time: Optional[str]

# Create router
router = APIRouter()

@router.get("/agents", response_model=List[AgentStatus])
async def get_agents():
    """Get status of all agents."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        agents_status = []
        for agent in crew_instance.agents:
            status = await agent.get_status()
            agents_status.append(AgentStatus(**status))

        return agents_status

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/agents/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: str):
    """Get status of a specific agent."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        for agent in crew_instance.agents:
            if agent.agent_id == agent_id:
                status = await agent.get_status()
                return AgentStatus(**status)

        raise HTTPException(status_code=404, detail="Agent not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest):
    """Create and execute a task."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        # Find the agent
        target_agent = None
        for agent in crew_instance.agents:
            if agent.agent_id == task.agent_id:
                target_agent = agent
                break

        if not target_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create task data
        task_data = {
            "id": f"task_{datetime.now().timestamp()}",
            "type": task.task_type,
            "content": task.content,
            "priority": task.priority,
            "metadata": task.metadata or {},
            "created_at": datetime.now().isoformat()
        }

        # Execute task
        result = await target_agent.process_task(task_data)

        return TaskResponse(
            task_id=task_data["id"],
            status="completed",
            result=result,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100)
):
    """Get tasks with optional filtering."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        # This is a simplified implementation
        # In a real system, you'd have a task history store
        tasks = []

        # Mock some recent tasks for demonstration
        for agent in crew_instance.agents:
            if not agent_id or agent.agent_id == agent_id:
                # Get recent tasks from agent's memory
                memories = await crew_instance.memory_manager.get_agent_memories(
                    agent.agent_id,
                    limit=limit//len(crew_instance.agents) or 1
                )

                for memory in memories:
                    if memory.metadata.get("type") == "task":
                        tasks.append(TaskResponse(
                            task_id=memory.metadata.get("task_id", "unknown"),
                            status="completed",
                            result={
                                "response": memory.response,
                                "timestamp": memory.timestamp.isoformat()
                            },
                            timestamp=memory.timestamp.isoformat()
                        ))

        return tasks[:limit]

    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/simulation/status", response_model=SimulationStatus)
async def get_simulation_status():
    """Get the current simulation status."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        # Get basic stats
        active_agents = sum(1 for agent in crew_instance.agents if agent.is_active)
        completed_tasks = sum(
            agent.performance_metrics["tasks_completed"]
            for agent in crew_instance.agents
        )

        return SimulationStatus(
            is_running=crew_instance.is_active,
            active_agents=active_agents,
            completed_tasks=completed_tasks,
            current_cycle=getattr(crew_instance, 'current_cycle', 0),
            start_time=getattr(crew_instance, 'start_time', None)
        )

    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/simulation/start")
async def start_simulation():
    """Start the simulation."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        await crew_instance.start()
        return {"message": "Simulation started", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/simulation/stop")
async def stop_simulation():
    """Stop the simulation."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        await crew_instance.stop()
        return {"message": "Simulation stopped", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/simulation/reset")
async def reset_simulation():
    """Reset the simulation."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        await crew_instance.reset()
        return {"message": "Simulation reset", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        stats = await crew_instance.memory_manager.get_memory_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/memory/cleanup")
async def cleanup_memory(days: int = Query(30, ge=1, le=365)):
    """Clean up old memories."""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Crew not initialized")

    try:
        cleaned_count = await crew_instance.memory_manager.cleanup_memories(days)
        return {
            "message": f"Cleaned up {cleaned_count} old memories",
            "days": days,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning up memory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "crew_initialized": crew_instance is not None
    }