"""
Startup scorer for evaluating progress and performance.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from statistics import mean

from ..agents.base_agent import BaseAgent
from ..utils.constants import StartupStage
from ..utils.logger import LoggerMixin


class StartupScorer(LoggerMixin):
    """Scorer for evaluating startup progress and agent performance."""

    def __init__(self):
        self.scores: Dict[str, Dict[str, Any]] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.kpis: Dict[str, float] = {}

    async def initialize(self):
        """Initialize the startup scorer."""
        self.logger.info("Startup scorer initialized")

        # Initialize default KPIs
        self.kpis = {
            "product_development": 0.0,
            "market_fit": 0.0,
            "team_performance": 0.0,
            "financial_health": 0.0,
            "customer_satisfaction": 0.0,
            "innovation_index": 0.0
        }

    async def evaluate_progress(
        self,
        agents: List[BaseAgent],
        cycle_number: int
    ) -> Dict[str, Any]:
        """Evaluate overall startup progress."""
        evaluation = {
            "cycle": cycle_number,
            "timestamp": datetime.now(),
            "agent_scores": {},
            "overall_score": 0.0,
            "kpi_updates": {},
            "recommendations": []
        }

        # Evaluate each agent
        agent_scores = {}
        for agent in agents:
            agent_score = await self._evaluate_agent(agent)
            agent_scores[agent.name] = agent_score

        evaluation["agent_scores"] = agent_scores

        # Calculate overall score
        if agent_scores:
            overall_score = mean(score["total_score"] for score in agent_scores.values())
            evaluation["overall_score"] = overall_score

        # Update KPIs based on agent performance
        kpi_updates = await self._update_kpis(agent_scores)
        evaluation["kpi_updates"] = kpi_updates

        # Generate recommendations
        recommendations = await self._generate_recommendations(agent_scores, kpi_updates)
        evaluation["recommendations"] = recommendations

        # Store evaluation
        self.performance_history.append(evaluation)
        self.scores[f"cycle_{cycle_number}"] = evaluation

        self.logger.info(f"Evaluated progress for cycle {cycle_number}: score {overall_score:.2f}")
        return evaluation

    async def _evaluate_agent(self, agent: BaseAgent) -> Dict[str, Any]:
        """Evaluate a single agent's performance."""
        status = await agent.get_status()
        metrics = status.get("performance_metrics", {})

        # Calculate component scores
        task_completion_score = min(1.0, metrics.get("tasks_completed", 0) / 10.0)  # Normalize
        success_rate_score = metrics.get("success_rate", 0.0)
        collaboration_score = metrics.get("collaboration_score", 0.0)

        # Response time score (lower is better, so invert)
        avg_response_time = metrics.get("average_response_time", 60.0)
        response_time_score = max(0.0, 1.0 - (avg_response_time / 300.0))  # Normalize to 5 min

        # Calculate weighted total score
        weights = {
            "task_completion": 0.3,
            "success_rate": 0.3,
            "collaboration": 0.2,
            "response_time": 0.2
        }

        total_score = (
            task_completion_score * weights["task_completion"] +
            success_rate_score * weights["success_rate"] +
            collaboration_score * weights["collaboration"] +
            response_time_score * weights["response_time"]
        )

        return {
            "agent_name": agent.name,
            "role": agent.role.value,
            "total_score": total_score,
            "component_scores": {
                "task_completion": task_completion_score,
                "success_rate": success_rate_score,
                "collaboration": collaboration_score,
                "response_time": response_time_score
            },
            "metrics": metrics,
            "grade": self._score_to_grade(total_score)
        }

    async def _update_kpis(self, agent_scores: Dict[str, Any]) -> Dict[str, float]:
        """Update KPIs based on agent performance."""
        updates = {}

        # Product development KPI (based on engineer performance)
        engineer_score = 0.0
        for agent_name, score in agent_scores.items():
            if score["role"] == "engineer":
                engineer_score = score["total_score"]
                break
        if engineer_score > 0:
            self.kpis["product_development"] = engineer_score
            updates["product_development"] = engineer_score

        # Market fit KPI (based on marketer and product manager)
        market_scores = []
        for agent_name, score in agent_scores.items():
            if score["role"] in ["marketer", "product_manager"]:
                market_scores.append(score["total_score"])

        if market_scores:
            self.kpis["market_fit"] = mean(market_scores)
            updates["market_fit"] = self.kpis["market_fit"]

        # Team performance KPI (average of all agents)
        if agent_scores:
            team_score = mean(score["total_score"] for score in agent_scores.values())
            self.kpis["team_performance"] = team_score
            updates["team_performance"] = team_score

        # Financial health KPI (based on investor and CEO)
        finance_scores = []
        for agent_name, score in agent_scores.items():
            if score["role"] in ["investor", "ceo"]:
                finance_scores.append(score["total_score"])

        if finance_scores:
            self.kpis["financial_health"] = mean(finance_scores)
            updates["financial_health"] = self.kpis["financial_health"]

        # Innovation index (based on collaboration and task completion)
        innovation_scores = []
        for score in agent_scores.values():
            innovation_score = (
                score["component_scores"]["collaboration"] * 0.5 +
                score["component_scores"]["task_completion"] * 0.5
            )
            innovation_scores.append(innovation_score)

        if innovation_scores:
            self.kpis["innovation_index"] = mean(innovation_scores)
            updates["innovation_index"] = self.kpis["innovation_index"]

        return updates

    async def _generate_recommendations(
        self,
        agent_scores: Dict[str, Any],
        kpi_updates: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on evaluation."""
        recommendations = []

        # Check for underperforming agents
        for agent_name, score in agent_scores.items():
            if score["total_score"] < 0.6:
                recommendations.append(
                    f"Provide additional support and training for {agent_name} "
                    f"(current score: {score['total_score']:.2f})"
                )

        # Check KPIs
        for kpi_name, value in kpi_updates.items():
            if value < 0.5:
                recommendations.append(
                    f"Focus on improving {kpi_name.replace('_', ' ')} "
                    f"(current value: {value:.2f})"
                )

        # Check for imbalance
        roles = [score["role"] for score in agent_scores.values()]
        if roles.count("engineer") > roles.count("marketer") + roles.count("product_manager"):
            recommendations.append(
                "Consider strengthening marketing and product management capabilities"
            )

        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Continue current trajectory - all systems performing well")

        return recommendations

    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def get_current_scores(self) -> Dict[str, Any]:
        """Get current evaluation scores."""
        if not self.performance_history:
            return {}

        return self.performance_history[-1]

    def get_kpis(self) -> Dict[str, float]:
        """Get current KPI values."""
        return self.kpis.copy()

    def get_performance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get performance history."""
        return self.performance_history[-limit:] if self.performance_history else []

    def get_scorer_stats(self) -> Dict[str, Any]:
        """Get scorer statistics."""
        if not self.performance_history:
            return {"evaluations": 0}

        latest = self.performance_history[-1]
        avg_score = mean(eval_["overall_score"] for eval_ in self.performance_history)

        return {
            "total_evaluations": len(self.performance_history),
            "latest_score": latest["overall_score"],
            "average_score": avg_score,
            "kpi_count": len(self.kpis),
            "trend": "improving" if len(self.performance_history) > 1 and
                    self.performance_history[-1]["overall_score"] >
                    self.performance_history[-2]["overall_score"] else "stable"
        }