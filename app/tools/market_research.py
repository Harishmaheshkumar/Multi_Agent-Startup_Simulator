"""
Market research tool for the startup simulator.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..utils.logger import LoggerMixin


class MarketResearchTool(LoggerMixin):
    """Tool for conducting market research and analysis."""

    def __init__(self):
        self.market_data: Dict[str, Any] = {}
        self.search_history: List[Dict[str, Any]] = []

    async def analyze_market_size(self, industry: str, region: str = "global") -> Dict[str, Any]:
        """Analyze market size for a given industry."""
        # Mock market size analysis
        base_sizes = {
            "saas": 200000000000,  # $200B
            "fintech": 150000000000,  # $150B
            "healthtech": 100000000000,  # $100B
            "ecommerce": 5000000000000,  # $5T
            "ai": 50000000000,  # $50B
        }

        market_size = base_sizes.get(industry.lower(), 10000000000)  # $10B default

        # Adjust for region
        region_multipliers = {
            "global": 1.0,
            "north_america": 0.4,
            "europe": 0.3,
            "asia": 0.5,
            "other": 0.1
        }

        multiplier = region_multipliers.get(region.lower(), 1.0)
        regional_size = market_size * multiplier

        analysis = {
            "industry": industry,
            "region": region,
            "total_market_size": market_size,
            "regional_market_size": regional_size,
            "growth_rate": 0.15 + (asyncio.get_event_loop().time() % 0.1),  # 15-25% growth
            "key_players": self._get_key_players(industry),
            "trends": self._get_market_trends(industry),
            "timestamp": datetime.now().isoformat()
        }

        self.market_data[f"{industry}_{region}"] = analysis
        return analysis

    async def competitor_analysis(self, company: str, industry: str) -> Dict[str, Any]:
        """Analyze competitors in the market."""
        competitors = self._get_competitors(company, industry)

        analysis = {
            "target_company": company,
            "industry": industry,
            "direct_competitors": competitors[:3],
            "indirect_competitors": competitors[3:6],
            "market_share_analysis": self._analyze_market_share(competitors),
            "competitive_advantages": self._identify_competitive_advantages(company, competitors),
            "threats": self._identify_threats(competitors),
            "recommendations": self._generate_competitor_recommendations(company, competitors),
            "timestamp": datetime.now().isoformat()
        }

        return analysis

    async def customer_segmentation(self, industry: str) -> Dict[str, Any]:
        """Analyze customer segments for an industry."""
        segments = self._get_customer_segments(industry)

        analysis = {
            "industry": industry,
            "segments": segments,
            "segment_sizes": {seg["name"]: seg["size"] for seg in segments},
            "growth_segments": [seg for seg in segments if seg.get("growth_rate", 0) > 0.1],
            "high_value_segments": sorted(segments, key=lambda x: x.get("lifetime_value", 0), reverse=True)[:3],
            "recommendations": self._generate_segmentation_recommendations(segments),
            "timestamp": datetime.now().isoformat()
        }

        return analysis

    async def trend_analysis(self, industry: str, timeframe: str = "1year") -> Dict[str, Any]:
        """Analyze market trends."""
        trends = self._get_market_trends(industry)

        analysis = {
            "industry": industry,
            "timeframe": timeframe,
            "emerging_trends": [t for t in trends if t.get("status") == "emerging"],
            "mature_trends": [t for t in trends if t.get("status") == "mature"],
            "declining_trends": [t for t in trends if t.get("status") == "declining"],
            "impact_assessment": self._assess_trend_impact(trends),
            "opportunities": self._identify_trend_opportunities(trends),
            "timestamp": datetime.now().isoformat()
        }

        return analysis

    async def search_market_data(self, query: str, industry: Optional[str] = None) -> Dict[str, Any]:
        """Search for market data based on query."""
        # Mock search results
        results = {
            "query": query,
            "industry": industry,
            "results": [
                {
                    "title": f"Market Analysis: {query}",
                    "source": "Mock Research Firm",
                    "summary": f"Comprehensive analysis of {query} in the market.",
                    "relevance_score": 0.85
                },
                {
                    "title": f"Trends in {query}",
                    "source": "Industry Report",
                    "summary": f"Latest trends and developments in {query}.",
                    "relevance_score": 0.72
                }
            ],
            "total_results": 2,
            "timestamp": datetime.now().isoformat()
        }

        self.search_history.append({
            "query": query,
            "results_count": len(results["results"]),
            "timestamp": datetime.now().isoformat()
        })

        return results

    def _get_key_players(self, industry: str) -> List[str]:
        """Get key players in an industry."""
        players = {
            "saas": ["Salesforce", "Microsoft", "Adobe", "Slack", "Zoom"],
            "fintech": ["Stripe", "PayPal", "Square", "Robinhood", "Coinbase"],
            "healthtech": ["Epic Systems", "Cerner", "Teladoc", "Oscar Health"],
            "ecommerce": ["Amazon", "Alibaba", "Shopify", "eBay", "Walmart"],
            "ai": ["OpenAI", "Google", "Microsoft", "Anthropic", "Cohere"]
        }

        return players.get(industry.lower(), ["Company A", "Company B", "Company C"])

    def _get_market_trends(self, industry: str) -> List[Dict[str, Any]]:
        """Get market trends for an industry."""
        base_trends = [
            {
                "name": "Digital Transformation",
                "status": "mature",
                "impact": "high",
                "description": "Continued adoption of digital technologies"
            },
            {
                "name": "AI Integration",
                "status": "emerging",
                "impact": "high",
                "description": "Integration of AI and machine learning"
            },
            {
                "name": "Remote Work",
                "status": "mature",
                "impact": "medium",
                "description": "Shift to remote and hybrid work models"
            },
            {
                "name": "Sustainability",
                "status": "emerging",
                "impact": "medium",
                "description": "Focus on sustainable and eco-friendly practices"
            }
        ]

        return base_trends

    def _get_competitors(self, company: str, industry: str) -> List[Dict[str, Any]]:
        """Get competitor information."""
        key_players = self._get_key_players(industry)

        competitors = []
        for player in key_players[:5]:
            competitor = {
                "name": player,
                "market_share": 5 + (hash(player) % 20),  # Mock market share
                "strengths": ["Strong brand", "Large user base", "Established technology"],
                "weaknesses": ["High costs", "Legacy systems", "Slow innovation"],
                "threat_level": "high" if player != company else "none"
            }
            competitors.append(competitor)

        return competitors

    def _analyze_market_share(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market share distribution."""
        total_share = sum(comp.get("market_share", 0) for comp in competitors)

        return {
            "total_analyzed_share": total_share,
            "concentration": "high" if total_share > 60 else "medium",
            "leader": max(competitors, key=lambda x: x.get("market_share", 0))["name"],
            "distribution": "oligopoly" if len([c for c in competitors if c.get("market_share", 0) > 15]) >= 3 else "fragmented"
        }

    def _identify_competitive_advantages(self, company: str, competitors: List[Dict[str, Any]]) -> List[str]:
        """Identify potential competitive advantages."""
        return [
            "Agile startup culture",
            "Innovative technology approach",
            "Customer-centric focus",
            "Lower operational costs",
            "Specialized domain expertise"
        ]

    def _identify_threats(self, competitors: List[Dict[str, Any]]) -> List[str]:
        """Identify competitive threats."""
        threats = []
        for comp in competitors:
            if comp.get("threat_level") == "high":
                threats.append(f"Strong competition from {comp['name']}")

        threats.extend([
            "Rapid technological changes",
            "Changing customer preferences",
            "New market entrants",
            "Regulatory changes"
        ])

        return threats

    def _generate_competitor_recommendations(self, company: str, competitors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on competitor analysis."""
        return [
            "Focus on underserved customer segments",
            "Differentiate through superior user experience",
            "Invest in technology advantages",
            "Build strategic partnerships",
            "Monitor competitor pricing strategies"
        ]

    def _get_customer_segments(self, industry: str) -> List[Dict[str, Any]]:
        """Get customer segments for an industry."""
        segments = [
            {
                "name": "Enterprise",
                "size": "large",
                "growth_rate": 0.08,
                "lifetime_value": 50000,
                "characteristics": ["Large organizations", "Complex needs", "High budget"]
            },
            {
                "name": "SMB",
                "size": "medium",
                "growth_rate": 0.12,
                "lifetime_value": 5000,
                "characteristics": ["Small businesses", "Cost-conscious", "Growing fast"]
            },
            {
                "name": "Consumer",
                "size": "large",
                "growth_rate": 0.15,
                "lifetime_value": 500,
                "characteristics": ["Individual users", "Price sensitive", "Mobile-first"]
            }
        ]

        return segments

    def _generate_segmentation_recommendations(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on segmentation analysis."""
        return [
            "Prioritize high-growth segments for expansion",
            "Develop tiered pricing for different segments",
            "Customize messaging for each segment",
            "Focus product development on high-value segments"
        ]

    def _assess_trend_impact(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the impact of market trends."""
        high_impact = len([t for t in trends if t.get("impact") == "high"])
        emerging_high = len([t for t in trends if t.get("status") == "emerging" and t.get("impact") == "high"])

        return {
            "high_impact_trends": high_impact,
            "emerging_high_impact": emerging_high,
            "overall_risk": "high" if emerging_high > 1 else "medium",
            "adaptation_needed": "urgent" if high_impact > 2 else "planned"
        }

    def _identify_trend_opportunities(self, trends: List[Dict[str, Any]]) -> List[str]:
        """Identify opportunities from market trends."""
        return [
            "Adopt emerging technologies early",
            "Address sustainability concerns",
            "Develop remote collaboration tools",
            "Create AI-powered solutions",
            "Focus on digital transformation services"
        ]

    def get_research_stats(self) -> Dict[str, Any]:
        """Get research tool statistics."""
        return {
            "total_searches": len(self.search_history),
            "market_analyses": len(self.market_data),
            "last_search": self.search_history[-1] if self.search_history else None
        }