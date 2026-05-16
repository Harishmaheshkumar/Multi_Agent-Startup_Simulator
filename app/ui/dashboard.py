"""
Dashboard components for the startup simulator UI.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Any

from ..crew.startup_crew import StartupCrew
from ..orchestration.startup_scorer import StartupScorer


class Dashboard:
    """Dashboard class for displaying simulation metrics and controls."""

    def __init__(self, crew: StartupCrew, scorer: StartupScorer):
        self.crew = crew
        self.scorer = scorer

    def render_dashboard(self):
        """Render the main dashboard."""
        st.header("📊 Simulation Dashboard")

        # Quick stats
        self._render_quick_stats()

        # Real-time status
        self._render_real_time_status()

        # Performance overview
        self._render_performance_overview()

        # Agent status grid
        self._render_agent_status_grid()

    def _render_quick_stats(self):
        """Render quick statistics cards."""
        try:
            status = asyncio.run(self.crew.get_status())

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                is_active = status.get("is_active", False)
                st.metric(
                    "Status",
                    "🟢 Running" if is_active else "🔴 Stopped",
                    delta="Active" if is_active else "Inactive"
                )

            with col2:
                cycle = status.get("current_cycle", 0)
                st.metric("Current Cycle", cycle)

            with col3:
                tasks = status.get("tasks_completed", 0)
                st.metric("Tasks Completed", tasks)

            with col4:
                agents = len(status.get("agents", []))
                st.metric("Active Agents", agents)

        except Exception as e:
            st.error(f"Error loading quick stats: {e}")

    def _render_real_time_status(self):
        """Render real-time simulation status."""
        st.subheader("Real-time Status")

        # Simulation progress
        try:
            status = asyncio.run(self.crew.get_status())

            if status.get("is_active"):
                progress = min(100, (status.get("current_cycle", 0) / 10) * 100)  # Assume 10 cycles max
                st.progress(progress / 100, text=f"Cycle {status.get('current_cycle', 0)} / 10")

                # Current activities
                st.info("🔄 Simulation is running - agents are collaborating")

                # Recent activities
                activities = status.get("recent_activities", [])
                if activities:
                    st.subheader("Recent Activities")
                    for activity in activities[-5:]:  # Show last 5
                        st.write(f"• {activity}")
            else:
                st.warning("⏸️ Simulation is stopped")

        except Exception as e:
            st.error(f"Error loading real-time status: {e}")

    def _render_performance_overview(self):
        """Render performance overview charts."""
        st.subheader("Performance Overview")

        try:
            # Get performance history
            history = self.scorer.get_performance_history(limit=20)

            if history:
                # Performance trend
                cycles = [h["cycle"] for h in history]
                scores = [h["overall_score"] for h in history]

                fig = px.line(
                    x=cycles,
                    y=scores,
                    title="Overall Performance Trend",
                    labels={"x": "Cycle", "y": "Score"}
                )
                fig.update_traces(mode="lines+markers")
                st.plotly_chart(fig, use_container_width=True)

                # Current KPIs
                kpis = self.scorer.get_kpis()
                if kpis:
                    st.subheader("Key Performance Indicators")

                    kpi_cols = st.columns(len(kpis))
                    for i, (kpi_name, value) in enumerate(kpis.items()):
                        with kpi_cols[i]:
                            formatted_name = kpi_name.replace("_", " ").title()
                            st.metric(formatted_name, ".2f")
            else:
                st.info("No performance data available yet")

        except Exception as e:
            st.error(f"Error loading performance overview: {e}")

    def _render_agent_status_grid(self):
        """Render agent status grid."""
        st.subheader("Agent Status")

        try:
            status = asyncio.run(self.crew.get_status())
            agents = status.get("agents", [])

            if agents:
                # Create agent status cards
                cols = st.columns(min(3, len(agents)))

                for i, agent_data in enumerate(agents):
                    with cols[i % 3]:
                        self._render_agent_card(agent_data)
            else:
                st.info("No agents available")

        except Exception as e:
            st.error(f"Error loading agent status: {e}")

    def _render_agent_card(self, agent_data: Dict[str, Any]):
        """Render a single agent status card."""
        role_emojis = {
            "ceo": "👨‍💼",
            "engineer": "👨‍💻",
            "investor": "💰",
            "legal": "⚖️",
            "marketer": "📈",
            "product_manager": "📋"
        }

        emoji = role_emojis.get(agent_data.get("role", "").lower(), "🤖")

        with st.container():
            st.markdown(f"### {emoji} {agent_data['name']}")

            # Status indicator
            is_active = agent_data.get("is_active", False)
            status_color = "🟢" if is_active else "🔴"
            st.write(f"**Status:** {status_color} {'Active' if is_active else 'Inactive'}")

            # Current task
            current_task = agent_data.get("current_task", "None")
            st.write(f"**Current Task:** {current_task}")

            # Performance metrics
            metrics = agent_data.get("performance_metrics", {})
            if metrics:
                st.write("**Performance:**")
                st.write(f"- Tasks: {metrics.get('tasks_completed', 0)}")
                st.write(f"- Success: {metrics.get('success_rate', 0):.1%}")

            # Last active
            last_active = agent_data.get("last_active", "Never")
            if last_active != "Never":
                try:
                    dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    st.write(f"**Last Active:** {dt.strftime('%H:%M:%S')}")
                except:
                    st.write(f"**Last Active:** {last_active[:19]}")
            else:
                st.write("**Last Active:** Never")

            st.divider()


class AnalyticsDashboard:
    """Analytics dashboard for detailed performance analysis."""

    def __init__(self, crew: StartupCrew, scorer: StartupScorer):
        self.crew = crew
        self.scorer = scorer

    def render_analytics(self):
        """Render the analytics dashboard."""
        st.header("📈 Analytics & Insights")

        # Performance analytics
        self._render_performance_analytics()

        # Agent analytics
        self._render_agent_analytics()

        # Task analytics
        self._render_task_analytics()

        # Memory analytics
        self._render_memory_analytics()

    def _render_performance_analytics(self):
        """Render performance analytics."""
        st.subheader("Performance Analytics")

        try:
            history = self.scorer.get_performance_history(limit=50)

            if history:
                # Create performance DataFrame
                df = pd.DataFrame([{
                    "cycle": h["cycle"],
                    "overall_score": h["overall_score"],
                    "timestamp": h["timestamp"]
                } for h in history])

                # Performance over time
                fig = px.line(
                    df,
                    x="cycle",
                    y="overall_score",
                    title="Performance Trend",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

                # Performance distribution
                fig2 = px.histogram(
                    df,
                    x="overall_score",
                    title="Performance Distribution",
                    nbins=10
                )
                st.plotly_chart(fig2, use_container_width=True)

                # Performance statistics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Average Score", ".2f")

                with col2:
                    st.metric("Best Score", ".2f")

                with col3:
                    st.metric("Current Score", ".2f")

                with col4:
                    trend = "↗️ Improving" if len(df) > 1 and df["overall_score"].iloc[-1] > df["overall_score"].iloc[0] else "↘️ Declining"
                    st.metric("Trend", trend)
            else:
                st.info("No performance data available")

        except Exception as e:
            st.error(f"Error loading performance analytics: {e}")

    def _render_agent_analytics(self):
        """Render agent performance analytics."""
        st.subheader("Agent Performance Analytics")

        try:
            # Get latest evaluation
            latest_eval = self.scorer.get_current_scores()

            if latest_eval and "agent_scores" in latest_eval:
                agent_scores = latest_eval["agent_scores"]

                # Agent performance comparison
                agents_df = pd.DataFrame([{
                    "agent": name,
                    "role": score["role"],
                    "total_score": score["total_score"],
                    "task_completion": score["component_scores"]["task_completion"],
                    "success_rate": score["component_scores"]["success_rate"],
                    "collaboration": score["component_scores"]["collaboration"],
                    "response_time": score["component_scores"]["response_time"]
                } for name, score in agent_scores.items()])

                # Overall scores
                fig = px.bar(
                    agents_df,
                    x="agent",
                    y="total_score",
                    color="role",
                    title="Agent Performance Scores"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Component scores
                component_cols = ["task_completion", "success_rate", "collaboration", "response_time"]
                component_names = ["Task Completion", "Success Rate", "Collaboration", "Response Time"]

                fig2 = go.Figure()
                for i, (col, name) in enumerate(zip(component_cols, component_names)):
                    fig2.add_trace(go.Bar(
                        name=name,
                        x=agents_df["agent"],
                        y=agents_df[col]
                    ))

                fig2.update_layout(
                    barmode='group',
                    title="Component Performance Scores"
                )
                st.plotly_chart(fig2, use_container_width=True)

                # Agent details table
                st.dataframe(agents_df.round(3))
            else:
                st.info("No agent performance data available")

        except Exception as e:
            st.error(f"Error loading agent analytics: {e}")

    def _render_task_analytics(self):
        """Render task analytics."""
        st.subheader("Task Analytics")

        try:
            # Mock task data for now
            task_data = {
                "task_type": ["planning", "development", "funding", "marketing", "legal", "custom"],
                "count": [15, 25, 10, 20, 8, 12],
                "avg_duration": [45, 120, 30, 60, 90, 75],
                "success_rate": [0.85, 0.90, 0.75, 0.88, 0.80, 0.82]
            }

            df = pd.DataFrame(task_data)

            col1, col2 = st.columns(2)

            with col1:
                fig = px.pie(
                    df,
                    values="count",
                    names="task_type",
                    title="Task Distribution by Type"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    df,
                    x="task_type",
                    y="success_rate",
                    title="Task Success Rates"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Task statistics table
            st.dataframe(df)

        except Exception as e:
            st.error(f"Error loading task analytics: {e}")

    def _render_memory_analytics(self):
        """Render memory system analytics."""
        st.subheader("Memory Analytics")

        try:
            # Get memory stats
            memory_stats = asyncio.run(self.crew.memory_manager.get_memory_stats())

            col1, col2, col3 = st.columns(3)

            with col1:
                total = memory_stats.get("total_memories", 0)
                st.metric("Total Memories", total)

            with col2:
                stores = memory_stats.get("stores", {})
                active = sum(1 for status in stores.values() if status == "available")
                st.metric("Active Stores", active)

            with col3:
                types = len(memory_stats.get("types", {}))
                st.metric("Memory Types", types)

            # Memory type distribution
            if "types" in memory_stats:
                types_data = memory_stats["types"]
                if types_data:
                    fig = px.pie(
                        values=list(types_data.values()),
                        names=list(types_data.keys()),
                        title="Memory Distribution by Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading memory analytics: {e}")


def create_dashboard_components(crew: StartupCrew, scorer: StartupScorer):
    """Create dashboard component instances."""
    return {
        "main_dashboard": Dashboard(crew, scorer),
        "analytics_dashboard": AnalyticsDashboard(crew, scorer)
    }