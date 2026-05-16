"""
Debate engine for facilitating discussions among agents.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..utils.logger import LoggerMixin


class DebateEngine(LoggerMixin):
    """Engine for managing debates and discussions among agents."""

    def __init__(self):
        self.active_debates: Dict[str, Dict[str, Any]] = {}
        self.debate_history: List[Dict[str, Any]] = []
        self.debate_counter = 0

    async def initialize(self):
        """Initialize the debate engine."""
        self.logger.info("Debate engine initialized")

    def create_debate_id(self) -> str:
        """Generate a unique debate ID."""
        self.debate_counter += 1
        return f"debate_{self.debate_counter}"

    async def run_debate(
        self,
        agents: List[BaseAgent],
        topic: str,
        max_rounds: int = 3,
        time_limit: int = 300
    ) -> Dict[str, Any]:
        """Run a debate among agents on a given topic."""
        debate_id = self.create_debate_id()

        self.logger.info(f"Starting debate {debate_id} on topic: {topic}")

        debate_data = {
            "id": debate_id,
            "topic": topic,
            "participants": [agent.name for agent in agents],
            "start_time": datetime.now(),
            "rounds": [],
            "conclusion": None,
            "status": "active"
        }

        self.active_debates[debate_id] = debate_data

        try:
            # Opening statements
            opening_round = await self._run_opening_round(agents, topic)
            debate_data["rounds"].append(opening_round)

            # Debate rounds
            for round_num in range(max_rounds):
                round_data = await self._run_debate_round(agents, topic, round_num + 1)
                debate_data["rounds"].append(round_data)

                # Check for consensus
                if await self._check_consensus(round_data):
                    break

            # Closing statements and conclusion
            conclusion = await self._generate_conclusion(agents, topic, debate_data["rounds"])
            debate_data["conclusion"] = conclusion

            debate_data["end_time"] = datetime.now()
            debate_data["status"] = "completed"

            # Store in history
            self.debate_history.append(debate_data)
            del self.active_debates[debate_id]

            self.logger.info(f"Debate {debate_id} completed")
            return debate_data

        except Exception as e:
            self.logger.error(f"Error in debate {debate_id}: {e}")
            debate_data["status"] = "error"
            debate_data["error"] = str(e)
            return debate_data

    async def _run_opening_round(self, agents: List[BaseAgent], topic: str) -> Dict[str, Any]:
        """Run opening statements round."""
        opening_statements = []

        for agent in agents:
            prompt = f"""
            As {agent.name}, provide your opening statement on the topic: {topic}

            Consider your role as {agent.role.value} and provide insights from your perspective.
            Be concise but comprehensive in your initial position.
            """

            try:
                response = await agent.think(prompt, {"debate_round": "opening"})
                opening_statements.append({
                    "agent": agent.name,
                    "role": agent.role.value,
                    "statement": response,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Error getting opening statement from {agent.name}: {e}")
                opening_statements.append({
                    "agent": agent.name,
                    "role": agent.role.value,
                    "statement": f"Unable to provide opening statement: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })

        return {
            "round_type": "opening",
            "statements": opening_statements,
            "timestamp": datetime.now().isoformat()
        }

    async def _run_debate_round(
        self,
        agents: List[BaseAgent],
        topic: str,
        round_num: int
    ) -> Dict[str, Any]:
        """Run a single debate round."""
        round_statements = []

        for i, agent in enumerate(agents):
            # Get previous statements for context
            previous_statements = []
            for prev_agent in agents:
                if prev_agent != agent:
                    # Find previous statement from this agent
                    for stmt in round_statements:
                        if stmt["agent"] == prev_agent.name:
                            previous_statements.append(stmt)
                            break

            prompt = f"""
            As {agent.name}, respond to the previous statements in the debate on: {topic}

            Previous statements in this round:
            {self._format_previous_statements(previous_statements)}

            Provide your counter-arguments, agreements, or clarifications from your {agent.role.value} perspective.
            Build upon the discussion and advance the debate.
            """

            try:
                response = await agent.think(prompt, {
                    "debate_round": f"round_{round_num}",
                    "previous_statements": len(previous_statements)
                })
                round_statements.append({
                    "agent": agent.name,
                    "role": agent.role.value,
                    "statement": response,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Error in debate round {round_num} from {agent.name}: {e}")
                round_statements.append({
                    "agent": agent.name,
                    "role": agent.role.value,
                    "statement": f"Unable to respond: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })

        return {
            "round_type": f"debate_round_{round_num}",
            "statements": round_statements,
            "timestamp": datetime.now().isoformat()
        }

    async def _check_consensus(self, round_data: Dict[str, Any]) -> bool:
        """Check if consensus has been reached in the debate."""
        statements = round_data.get("statements", [])

        if len(statements) < 2:
            return False

        # Simple consensus check - if all statements express agreement
        agreement_keywords = ["agree", "consensus", "settled", "conclusion", "unanimous"]
        disagreement_keywords = ["disagree", "conflict", "opposed", "different"]

        agreements = 0
        disagreements = 0

        for statement in statements:
            text = statement.get("statement", "").lower()
            if any(word in text for word in agreement_keywords):
                agreements += 1
            if any(word in text for word in disagreement_keywords):
                disagreements += 1

        # Consensus if majority agrees and no strong disagreements
        total_agents = len(statements)
        return agreements >= total_agents * 0.6 and disagreements == 0

    async def _generate_conclusion(
        self,
        agents: List[BaseAgent],
        topic: str,
        rounds: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a conclusion for the debate."""
        # Use the CEO agent to summarize if available
        ceo_agent = None
        for agent in agents:
            if agent.role.value == "ceo":
                ceo_agent = agent
                break

        if ceo_agent:
            prompt = f"""
            As CEO, provide a conclusion and summary of the debate on: {topic}

            Debate rounds summary:
            {self._summarize_rounds(rounds)}

            Synthesize the key points, agreements, disagreements, and provide a clear conclusion or decision.
            """

            try:
                conclusion = await ceo_agent.think(prompt, {"debate_conclusion": True})
                return {
                    "conclusion": conclusion,
                    "summarizer": ceo_agent.name,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Error generating conclusion: {e}")

        # Fallback conclusion
        return {
            "conclusion": f"Debate on '{topic}' completed. Key insights exchanged among {len(agents)} agents.",
            "summarizer": "system",
            "timestamp": datetime.now().isoformat()
        }

    def _format_previous_statements(self, statements: List[Dict[str, Any]]) -> str:
        """Format previous statements for context."""
        if not statements:
            return "No previous statements in this round."

        formatted = []
        for stmt in statements:
            formatted.append(f"{stmt['agent']} ({stmt['role']}): {stmt['statement'][:200]}...")

        return "\n".join(formatted)

    def _summarize_rounds(self, rounds: List[Dict[str, Any]]) -> str:
        """Summarize all debate rounds."""
        summaries = []

        for i, round_data in enumerate(rounds):
            round_type = round_data.get("round_type", f"round_{i+1}")
            statements = round_data.get("statements", [])

            summary = f"Round {i+1} ({round_type}): {len(statements)} statements"
            summaries.append(summary)

        return "\n".join(summaries)

    def get_active_debates(self) -> List[Dict[str, Any]]:
        """Get list of active debates."""
        return list(self.active_debates.values())

    def get_debate_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get debate history."""
        return self.debate_history[-limit:] if self.debate_history else []

    def get_debate_stats(self) -> Dict[str, Any]:
        """Get debate statistics."""
        total_debates = len(self.debate_history)
        active_debates = len(self.active_debates)

        if total_debates > 0:
            avg_rounds = sum(len(d.get("rounds", [])) for d in self.debate_history) / total_debates
            completed_debates = sum(1 for d in self.debate_history if d.get("status") == "completed")
            completion_rate = completed_debates / total_debates
        else:
            avg_rounds = 0
            completion_rate = 0

        return {
            "total_debates": total_debates,
            "active_debates": active_debates,
            "average_rounds_per_debate": avg_rounds,
            "completion_rate": completion_rate
        }