"""
CEO Agent for the Multi-Agent Startup Simulator.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..utils.constants import AgentRole, TaskType
from ..utils.helpers import read_file_content
from ..utils.helpers import read_file_content


class CEOAgent(BaseAgent):
    """CEO Agent responsible for strategic leadership and vision."""

    def __init__(self, model_loader, memory_manager, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            role=AgentRole.CEO,
            name="Chief Executive Officer",
            model_loader=model_loader,
            memory_manager=memory_manager,
            config=config
        )

        # Load CEO prompt
        self.prompt_template = read_file_content("app/prompts/ceo_prompt.txt")

        # CEO-specific attributes
        self.vision = ""
        self.strategy = {}
        self.key_decisions = []
        self.stakeholder_communications = []

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a CEO-level task."""
        task_type = task.get("type", "")
        content = task.get("content", "")

        self.logger.info(f"CEO processing task: {task_type}")

        if task_type == TaskType.PLANNING:
            return await self._handle_strategic_planning(content)
        elif task_type == TaskType.DECISION_MAKING:
            return await self._handle_decision_making(content)
        elif task_type == "crisis_management":
            return await self._handle_crisis_management(content)
        elif task_type == "stakeholder_communication":
            return await self._handle_stakeholder_communication(content)
        else:
            # General task processing
            prompt = self.prompt_template.format(
                task_description=content,
                agent_context=self._get_agent_context()
            )

            response = await self.think(prompt, {"task": task})
            return {
                "agent": self.agent_id,
                "task_id": task.get("id"),
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "decision_made": self._extract_decision(response)
            }

    async def collaborate(self, other_agents: List[BaseAgent], context: Dict[str, Any]) -> Dict[str, Any]:
        """Collaborate with other agents on strategic matters."""
        collaboration_context = {
            "ceo_vision": self.vision,
            "current_strategy": self.strategy,
            "other_agents": [agent.name for agent in other_agents],
            "collaboration_goal": context.get("goal", "strategic alignment")
        }

        prompt = f"""
        As CEO, you need to collaborate with your team on: {context.get('topic', 'strategic decision')}

        Your current vision: {self.vision}
        Team members: {', '.join([agent.name for agent in other_agents])}

        Context: {context}

        Provide leadership and guidance for this collaboration.
        """

        response = await self.think(prompt, collaboration_context)

        return {
            "leader": self.agent_id,
            "guidance": response,
            "collaboration_plan": self._create_collaboration_plan(other_agents, context),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_strategic_planning(self, content: str) -> Dict[str, Any]:
        """Handle strategic planning tasks."""
        prompt = f"""
        As CEO, develop a strategic plan for the following:

        {content}

        Consider:
        1. Market opportunity
        2. Competitive landscape
        3. Resource requirements
        4. Risk factors
        5. Timeline and milestones
        6. Success metrics

        Provide a comprehensive strategic plan.
        """

        plan = await self.think(prompt, {"task_type": "strategic_planning"})

        # Update internal strategy
        self.strategy = {
            "content": content,
            "plan": plan,
            "created_at": datetime.now().isoformat()
        }

        return {
            "agent": self.agent_id,
            "task_type": "strategic_planning",
            "strategic_plan": plan,
            "vision_statement": self._extract_vision(plan),
            "key_objectives": self._extract_objectives(plan),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_decision_making(self, content: str) -> Dict[str, Any]:
        """Handle critical decision making."""
        prompt = f"""
        As CEO, make a critical decision regarding:

        {content}

        Consider:
        1. Strategic alignment with company vision
        2. Risk vs. reward analysis
        3. Resource implications
        4. Timeline constraints
        5. Stakeholder impact

        Make a clear decision with rationale.
        """

        decision = await self.think(prompt, {"task_type": "decision_making"})

        # Store decision
        decision_record = {
            "content": content,
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        }
        self.key_decisions.append(decision_record)

        return {
            "agent": self.agent_id,
            "task_type": "decision_making",
            "decision": decision,
            "rationale": self._extract_rationale(decision),
            "risk_assessment": self._assess_risks(content),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_crisis_management(self, content: str) -> Dict[str, Any]:
        """Handle crisis situations."""
        prompt = f"""
        As CEO, manage this crisis situation:

        {content}

        Provide:
        1. Immediate action plan
        2. Communication strategy
        3. Risk mitigation steps
        4. Long-term recovery plan

        Lead the company through this crisis.
        """

        crisis_response = await self.think(prompt, {"task_type": "crisis_management"})

        return {
            "agent": self.agent_id,
            "task_type": "crisis_management",
            "crisis_response": crisis_response,
            "immediate_actions": self._extract_actions(crisis_response),
            "communication_plan": self._create_communication_plan(content),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_stakeholder_communication(self, content: str) -> Dict[str, Any]:
        """Handle stakeholder communications."""
        prompt = f"""
        As CEO, prepare communication for stakeholders regarding:

        {content}

        Craft a clear, professional message that addresses stakeholder concerns and maintains confidence.
        """

        communication = await self.think(prompt, {"task_type": "stakeholder_communication"})

        # Store communication
        comm_record = {
            "content": content,
            "communication": communication,
            "timestamp": datetime.now().isoformat()
        }
        self.stakeholder_communications.append(comm_record)

        return {
            "agent": self.agent_id,
            "task_type": "stakeholder_communication",
            "communication": communication,
            "tone": self._analyze_tone(communication),
            "key_messages": self._extract_key_messages(communication),
            "timestamp": datetime.now().isoformat()
        }

    def _get_agent_context(self) -> str:
        """Get context specific to CEO agent."""
        return f"""
        CEO Context:
        - Vision: {self.vision}
        - Recent decisions: {len(self.key_decisions)} made
        - Strategy in place: {'Yes' if self.strategy else 'No'}
        - Leadership style: Strategic, decisive, stakeholder-focused
        """

    def _extract_decision(self, response: str) -> Optional[str]:
        """Extract decision from response."""
        # Simple extraction logic - can be enhanced
        if "decide" in response.lower() or "decision" in response.lower():
            return response.split('.')[0] + '.'
        return None

    def _extract_vision(self, plan: str) -> str:
        """Extract vision statement from strategic plan."""
        # Look for vision-related keywords
        lines = plan.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['vision', 'mission', 'goal', 'objective']):
                return line.strip()
        return "Vision to be determined"

    def _extract_objectives(self, plan: str) -> List[str]:
        """Extract key objectives from plan."""
        objectives = []
        lines = plan.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')) or 'objective' in line.lower():
                objectives.append(line)
        return objectives[:5]  # Limit to 5 objectives

    def _extract_rationale(self, decision: str) -> str:
        """Extract rationale from decision."""
        # Simple extraction - look for reasoning keywords
        if "because" in decision.lower():
            return decision.split("because", 1)[1].strip()
        return "Rationale not explicitly stated"

    def _assess_risks(self, content: str) -> Dict[str, Any]:
        """Assess risks in a decision."""
        # Basic risk assessment - can be enhanced with ML
        risk_keywords = ['risk', 'uncertain', 'challenge', 'problem', 'issue']
        risk_level = "low"
        if any(word in content.lower() for word in risk_keywords):
            risk_level = "medium"
        if sum(1 for word in risk_keywords if word in content.lower()) > 2:
            risk_level = "high"

        return {
            "level": risk_level,
            "factors": [word for word in risk_keywords if word in content.lower()],
            "mitigation_needed": risk_level in ["medium", "high"]
        }

    def _extract_actions(self, response: str) -> List[str]:
        """Extract action items from response."""
        actions = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•', '1.', '2.', '3.')):
                actions.append(line)
        return actions

    def _create_communication_plan(self, crisis: str) -> Dict[str, Any]:
        """Create communication plan for crisis."""
        return {
            "immediate": "Notify key stakeholders within 1 hour",
            "internal": "Team meeting within 4 hours",
            "external": "Press release within 24 hours",
            "follow_up": "Regular updates every 48 hours"
        }

    def _analyze_tone(self, communication: str) -> str:
        """Analyze tone of communication."""
        positive_words = ['confident', 'optimistic', 'strong', 'committed']
        negative_words = ['concerned', 'challenging', 'difficult', 'uncertain']

        pos_count = sum(1 for word in positive_words if word in communication.lower())
        neg_count = sum(1 for word in negative_words if word in communication.lower())

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "cautious"
        else:
            return "neutral"

    def _extract_key_messages(self, communication: str) -> List[str]:
        """Extract key messages from communication."""
        sentences = communication.split('.')
        key_messages = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and not sentence.startswith(('The', 'A', 'An', 'In')):
                key_messages.append(sentence)
        return key_messages[:3]

    def _create_collaboration_plan(self, other_agents: List[BaseAgent], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan for collaboration with other agents."""
        return {
            "participants": [agent.name for agent in other_agents],
            "goal": context.get("goal", "collaboration"),
            "steps": [
                "Gather input from all agents",
                "Facilitate discussion",
                "Reach consensus",
                "Document decisions"
            ],
            "timeline": "Within current planning cycle"
        }