"""
Discussion manager for handling agent conversations and collaborations.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from ..utils.logger import LoggerMixin


class DiscussionManager(LoggerMixin):
    """Manager for handling discussions and conversations among agents."""

    def __init__(self):
        self.discussions: Dict[str, Dict[str, Any]] = {}
        self.conversation_threads: Dict[str, List[Dict[str, Any]]] = {}
        self.discussion_counter = 0
        self.collaboration_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def initialize(self):
        """Initialize the discussion manager."""
        self.logger.info("Discussion manager initialized")

    def create_discussion_id(self) -> str:
        """Generate a unique discussion ID."""
        self.discussion_counter += 1
        return f"discussion_{self.discussion_counter}"

    async def start_discussion(
        self,
        topic: str,
        participants: List[str],
        discussion_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new discussion."""
        discussion_id = self.create_discussion_id()

        discussion_data = {
            "id": discussion_id,
            "topic": topic,
            "participants": participants,
            "discussion_type": discussion_type,
            "start_time": datetime.now(),
            "end_time": None,
            "status": "active",
            "messages": [],
            "metadata": metadata or {},
            "summary": None,
            "outcomes": []
        }

        self.discussions[discussion_id] = discussion_data
        self.conversation_threads[discussion_id] = []

        self.logger.info(f"Started discussion {discussion_id}: {topic}")
        return discussion_id

    async def add_message(
        self,
        discussion_id: str,
        agent_name: str,
        message: str,
        message_type: str = "statement",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a message to a discussion."""
        if discussion_id not in self.discussions:
            self.logger.error(f"Discussion {discussion_id} not found")
            return False

        message_data = {
            "agent": agent_name,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }

        self.discussions[discussion_id]["messages"].append(message_data)
        self.conversation_threads[discussion_id].append(message_data)

        # Update collaboration metrics
        await self._update_collaboration_metrics(discussion_id, agent_name, message_data)

        return True

    async def end_discussion(
        self,
        discussion_id: str,
        summary: Optional[str] = None,
        outcomes: Optional[List[str]] = None
    ) -> bool:
        """End a discussion."""
        if discussion_id not in self.discussions:
            return False

        discussion = self.discussions[discussion_id]
        discussion["end_time"] = datetime.now()
        discussion["status"] = "completed"
        discussion["summary"] = summary
        discussion["outcomes"] = outcomes or []

        self.logger.info(f"Ended discussion {discussion_id}")
        return True

    async def get_discussion(self, discussion_id: str) -> Optional[Dict[str, Any]]:
        """Get a discussion by ID."""
        return self.discussions.get(discussion_id)

    async def get_active_discussions(self) -> List[Dict[str, Any]]:
        """Get all active discussions."""
        return [d for d in self.discussions.values() if d["status"] == "active"]

    async def get_discussion_messages(
        self,
        discussion_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages from a discussion."""
        if discussion_id not in self.conversation_threads:
            return []

        messages = self.conversation_threads[discussion_id]
        return messages[-limit:] if messages else []

    async def store_discussion(self, discussion_data: Dict[str, Any]):
        """Store a completed discussion."""
        discussion_id = discussion_data.get("id")
        if not discussion_id:
            discussion_id = self.create_discussion_id()

        # Store the discussion
        self.discussions[discussion_id] = discussion_data

        # Store conversation thread
        messages = discussion_data.get("rounds", [])
        if messages:
            # Flatten debate rounds into messages
            flattened_messages = []
            for round_data in messages:
                for statement in round_data.get("statements", []):
                    flattened_messages.append({
                        "agent": statement.get("agent", "unknown"),
                        "message": statement.get("statement", ""),
                        "message_type": round_data.get("round_type", "debate"),
                        "timestamp": statement.get("timestamp", datetime.now()),
                        "metadata": {"round": round_data.get("round_type")}
                    })

            self.conversation_threads[discussion_id] = flattened_messages

        self.logger.info(f"Stored discussion {discussion_id}")

    async def search_discussions(
        self,
        query: str,
        agent_name: Optional[str] = None,
        discussion_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search discussions by content."""
        matching_discussions = []

        for discussion in self.discussions.values():
            # Filter by agent
            if agent_name and agent_name not in discussion["participants"]:
                continue

            # Filter by type
            if discussion_type and discussion["discussion_type"] != discussion_type:
                continue

            # Search in topic and messages
            search_text = discussion["topic"].lower()
            for message in discussion.get("messages", []):
                search_text += " " + message["message"].lower()

            if query.lower() in search_text:
                matching_discussions.append(discussion)

        # Sort by recency
        matching_discussions.sort(
            key=lambda d: d["start_time"],
            reverse=True
        )

        return matching_discussions[:limit]

    async def get_collaboration_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get collaboration metrics for an agent."""
        return self.collaboration_metrics.get(agent_name, {})

    async def _update_collaboration_metrics(
        self,
        discussion_id: str,
        agent_name: str,
        message_data: Dict[str, Any]
    ):
        """Update collaboration metrics for an agent."""
        if agent_name not in self.collaboration_metrics:
            self.collaboration_metrics[agent_name] = {
                "total_messages": 0,
                "discussions_participated": set(),
                "message_types": defaultdict(int),
                "collaboration_score": 0.0,
                "last_activity": None
            }

        metrics = self.collaboration_metrics[agent_name]
        metrics["total_messages"] += 1
        metrics["discussions_participated"].add(discussion_id)
        metrics["message_types"][message_data["message_type"]] += 1
        metrics["last_activity"] = message_data["timestamp"]

        # Calculate collaboration score (simple heuristic)
        participation_count = len(metrics["discussions_participated"])
        message_count = metrics["total_messages"]
        metrics["collaboration_score"] = min(1.0, (participation_count * 0.3) + (message_count * 0.1))

    def get_discussion_stats(self) -> Dict[str, Any]:
        """Get discussion statistics."""
        total_discussions = len(self.discussions)
        active_discussions = len([d for d in self.discussions.values() if d["status"] == "active"])
        completed_discussions = total_discussions - active_discussions

        total_messages = sum(len(d.get("messages", [])) for d in self.discussions.values())

        discussion_types = defaultdict(int)
        for discussion in self.discussions.values():
            discussion_types[discussion["discussion_type"]] += 1

        return {
            "total_discussions": total_discussions,
            "active_discussions": active_discussions,
            "completed_discussions": completed_discussions,
            "total_messages": total_messages,
            "discussion_types": dict(discussion_types),
            "average_messages_per_discussion": total_messages / total_discussions if total_discussions > 0 else 0
        }

    def get_agent_participation_stats(self) -> Dict[str, Any]:
        """Get agent participation statistics."""
        agent_stats = {}

        for agent_name, metrics in self.collaboration_metrics.items():
            agent_stats[agent_name] = {
                "total_messages": metrics["total_messages"],
                "discussions_participated": len(metrics["discussions_participated"]),
                "collaboration_score": metrics["collaboration_score"],
                "message_types": dict(metrics["message_types"]),
                "last_activity": metrics["last_activity"]
            }

        return agent_stats

    async def generate_discussion_summary(self, discussion_id: str) -> Optional[str]:
        """Generate a summary of a discussion."""
        discussion = self.discussions.get(discussion_id)
        if not discussion:
            return None

        messages = discussion.get("messages", [])
        if not messages:
            return f"Discussion on '{discussion['topic']}' with no messages."

        # Simple summary generation
        participants = set(msg["agent"] for msg in messages)
        message_count = len(messages)

        summary = f"Discussion '{discussion['topic']}' among {len(participants)} participants "
        summary += f"({', '.join(participants)}) with {message_count} messages."

        if discussion.get("summary"):
            summary += f" Summary: {discussion['summary']}"

        return summary