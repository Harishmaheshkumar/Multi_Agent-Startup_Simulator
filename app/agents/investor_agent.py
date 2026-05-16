"""
Investor Agent for the Multi-Agent Startup Simulator.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..utils.constants import AgentRole, TaskType
from ..utils.helpers import read_file_content


class InvestorAgent(BaseAgent):
    """Investor Agent responsible for financial analysis and funding strategy."""

    def __init__(self, model_loader, memory_manager, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            role=AgentRole.INVESTOR,
            name="Chief Financial Officer",
            model_loader=model_loader,
            memory_manager=memory_manager,
            config=config
        )

        # Load investor prompt
        self.prompt_template = read_file_content("app/prompts/investor_prompt.txt")

        # Investor-specific attributes
        self.financial_projections = {}
        self.funding_rounds = []
        self.investment_criteria = {}
        self.portfolio_companies = []

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process an investor/financial task."""
        task_type = task.get("type", "")
        content = task.get("content", "")

        self.logger.info(f"Investor processing task: {task_type}")

        if task_type == TaskType.FUNDING:
            return await self._handle_funding_strategy(content)
        elif task_type == "financial_analysis":
            return await self._handle_financial_analysis(content)
        elif task_type == "valuation":
            return await self._handle_valuation(content)
        elif task_type == "investment_pitch":
            return await self._handle_investment_pitch(content)
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
                "success": True,
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_funding_strategy(self, content: str) -> Dict[str, Any]:
        """Handle funding strategy tasks."""
        prompt = f"""
        Develop a comprehensive funding strategy for:

        {content}

        Include:
        1. Funding stages and amounts
        2. Investor targeting strategy
        3. Dilution management
        4. Use of funds allocation
        5. Exit strategy considerations

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "funding"})
        self.funding_rounds.append({
            "strategy": content,
            "plan": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "funding_strategy": response,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_financial_analysis(self, content: str) -> Dict[str, Any]:
        """Handle financial analysis tasks."""
        prompt = f"""
        Perform detailed financial analysis for:

        {content}

        Provide:
        1. Revenue projections and assumptions
        2. Cost structure analysis
        3. Cash flow projections
        4. Break-even analysis
        5. Key financial metrics and KPIs
        6. Risk assessment

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "financial_analysis"})
        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "financial_analysis": self._extract_financial_metrics(response),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_valuation(self, content: str) -> Dict[str, Any]:
        """Handle valuation tasks."""
        prompt = f"""
        Determine company valuation for:

        {content}

        Consider:
        1. Market comparables
        2. Discounted cash flow analysis
        3. Venture capital method
        4. Stage-based valuation
        5. Negotiation strategy

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "valuation"})
        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "valuation_range": self._extract_valuation_range(response),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_investment_pitch(self, content: str) -> Dict[str, Any]:
        """Handle investment pitch preparation."""
        prompt = f"""
        Prepare a compelling investment pitch for:

        {content}

        Structure the pitch to include:
        1. Problem and solution
        2. Market opportunity
        3. Business model
        4. Traction and milestones
        5. Team strengths
        6. Financial projections
        7. Ask and use of funds

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "pitch"})
        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "investment_pitch": response,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_financial_metrics(self, response: str) -> Dict[str, Any]:
        """Extract financial metrics from response."""
        return {
            "revenue_projection": "TBD",
            "burn_rate": "TBD",
            "runway_months": 0,
            "key_assumptions": []
        }

    def _extract_valuation_range(self, response: str) -> Dict[str, Any]:
        """Extract valuation range from response."""
        return {
            "pre_money_valuation": "TBD",
            "post_money_valuation": "TBD",
            "valuation_method": "TBD"
        }

    def _get_agent_context(self) -> str:
        """Get agent-specific context."""
        return f"""
        Financial Projections: {len(self.financial_projections)}
        Funding Rounds: {len(self.funding_rounds)}
        Investment Criteria: {self.investment_criteria}
        Portfolio Companies: {len(self.portfolio_companies)}
        """

    def get_investment_metrics(self) -> Dict[str, Any]:
        """Get investment-specific metrics."""
        return {
            "funding_rounds_completed": len(self.funding_rounds),
            "total_funding_secured": 0,  # Could track actual amounts
            "portfolio_companies": len(self.portfolio_companies),
            "investment_success_rate": self.performance_metrics.get("success_rate", 0)
        }