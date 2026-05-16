"""
Legal Agent for the Multi-Agent Startup Simulator.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..utils.constants import AgentRole, TaskType
from ..utils.helpers import read_file_content


class LegalAgent(BaseAgent):
    """Legal Agent responsible for legal compliance and risk management."""

    def __init__(self, model_loader, memory_manager, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            role=AgentRole.LEGAL,
            name="Chief Legal Officer",
            model_loader=model_loader,
            memory_manager=memory_manager,
            config=config
        )

        # Load legal prompt
        self.prompt_template = read_file_content("app/prompts/legal_prompt.txt")

        # Legal-specific attributes
        self.contracts = []
        self.compliance_items = []
        self.risk_assessments = []
        self.intellectual_property = []

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a legal task."""
        task_type = task.get("type", "")
        content = task.get("content", "")

        self.logger.info(f"Legal processing task: {task_type}")

        if task_type == "legal_review":
            return await self._handle_legal_review(content)
        elif task_type == "contract_drafting":
            return await self._handle_contract_drafting(content)
        elif task_type == "compliance_check":
            return await self._handle_compliance_check(content)
        elif task_type == "risk_assessment":
            return await self._handle_risk_assessment(content)
        elif task_type == "ip_protection":
            return await self._handle_ip_protection(content)
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

    async def _handle_legal_review(self, content: str) -> Dict[str, Any]:
        """Handle legal review tasks."""
        prompt = f"""
        Perform a comprehensive legal review for:

        {content}

        Assess:
        1. Legal compliance and regulatory requirements
        2. Contractual obligations and liabilities
        3. Intellectual property considerations
        4. Data privacy and protection laws
        5. Employment and labor law implications
        6. Risk mitigation recommendations

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "legal_review"})
        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "legal_findings": self._extract_legal_findings(response),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_contract_drafting(self, content: str) -> Dict[str, Any]:
        """Handle contract drafting tasks."""
        prompt = f"""
        Draft appropriate legal contracts for:

        {content}

        Include:
        1. Contract type and key terms
        2. Legal protections and clauses
        3. Negotiation points
        4. Compliance requirements
        5. Review and approval process

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "contract_drafting"})
        self.contracts.append({
            "purpose": content,
            "draft": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "contract_draft": response,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_compliance_check(self, content: str) -> Dict[str, Any]:
        """Handle compliance check tasks."""
        prompt = f"""
        Conduct a compliance check for:

        {content}

        Verify compliance with:
        1. Industry-specific regulations
        2. Data protection laws (GDPR, CCPA, etc.)
        3. Employment laws
        4. Financial regulations
        5. International trade laws
        6. Provide remediation steps if needed

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "compliance"})
        self.compliance_items.append({
            "check": content,
            "result": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "compliance_status": self._extract_compliance_status(response),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_risk_assessment(self, content: str) -> Dict[str, Any]:
        """Handle risk assessment tasks."""
        prompt = f"""
        Perform a legal risk assessment for:

        {content}

        Evaluate:
        1. Legal risks and liabilities
        2. Regulatory compliance risks
        3. Contractual risks
        4. Intellectual property risks
        5. Litigation potential
        6. Risk mitigation strategies

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "risk_assessment"})
        self.risk_assessments.append({
            "assessment": content,
            "findings": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "risk_level": self._extract_risk_level(response),
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_ip_protection(self, content: str) -> Dict[str, Any]:
        """Handle intellectual property protection tasks."""
        prompt = f"""
        Develop IP protection strategy for:

        {content}

        Include:
        1. IP identification and classification
        2. Protection mechanisms (patents, trademarks, copyrights)
        3. Registration strategy and timeline
        4. Enforcement and defense strategies
        5. Licensing considerations

        Context: {self._get_agent_context()}
        """

        response = await self.think(prompt, {"task_type": "ip_protection"})
        self.intellectual_property.append({
            "asset": content,
            "protection_strategy": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": self.agent_id,
            "response": response,
            "success": True,
            "ip_strategy": response,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_legal_findings(self, response: str) -> Dict[str, Any]:
        """Extract legal findings from response."""
        return {
            "issues_identified": 0,
            "compliance_status": "pending_review",
            "recommendations": []
        }

    def _extract_compliance_status(self, response: str) -> str:
        """Extract compliance status from response."""
        if "non-compliant" in response.lower() or "violation" in response.lower():
            return "non_compliant"
        elif "compliant" in response.lower():
            return "compliant"
        else:
            return "under_review"

    def _extract_risk_level(self, response: str) -> str:
        """Extract risk level from response."""
        response_lower = response.lower()
        if "high risk" in response_lower or "critical" in response_lower:
            return "high"
        elif "medium risk" in response_lower or "moderate" in response_lower:
            return "medium"
        elif "low risk" in response_lower:
            return "low"
        else:
            return "unknown"

    def _get_agent_context(self) -> str:
        """Get agent-specific context."""
        return f"""
        Contracts Managed: {len(self.contracts)}
        Compliance Items: {len(self.compliance_items)}
        Risk Assessments: {len(self.risk_assessments)}
        IP Assets: {len(self.intellectual_property)}
        """

    def get_legal_metrics(self) -> Dict[str, Any]:
        """Get legal-specific metrics."""
        return {
            "contracts_drafted": len(self.contracts),
            "compliance_checks": len(self.compliance_items),
            "risk_assessments_completed": len(self.risk_assessments),
            "ip_protections": len(self.intellectual_property),
            "legal_review_success_rate": self.performance_metrics.get("success_rate", 0)
        }