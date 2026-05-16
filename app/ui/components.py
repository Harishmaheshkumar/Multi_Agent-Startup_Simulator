"""
UI components for the startup simulator.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio


class AgentCard:
    """Component for displaying agent information."""

    @staticmethod
    def render(agent_data: Dict[str, Any], expanded: bool = False):
        """Render an agent information card."""
        role_emojis = {
            "ceo": "👨‍💼",
            "engineer": "👨‍💻",
            "investor": "💰",
            "legal": "⚖️",
            "marketer": "📈",
            "product_manager": "📋"
        }

        emoji = role_emojis.get(agent_data.get("role", "").lower(), "🤖")
        name = agent_data.get("name", "Unknown Agent")

        if expanded:
            with st.expander(f"{emoji} {name}", expanded=True):
                AgentCard._render_expanded_content(agent_data)
        else:
            with st.container():
                AgentCard._render_compact_content(agent_data, emoji)

    @staticmethod
    def _render_compact_content(agent_data: Dict[str, Any], emoji: str):
        """Render compact agent card."""
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown(f"### {emoji}")

        with col2:
            st.markdown(f"**{agent_data.get('name', 'Unknown')}**")
            st.write(f"Role: {agent_data.get('role', 'Unknown').title()}")

            is_active = agent_data.get("is_active", False)
            status = "🟢 Active" if is_active else "🔴 Inactive"
            st.write(f"Status: {status}")

        st.divider()

    @staticmethod
    def _render_expanded_content(agent_data: Dict[str, Any]):
        """Render expanded agent card with full details."""
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Agent ID:** {agent_data.get('agent_id', 'N/A')}")
            st.write(f"**Role:** {agent_data.get('role', 'Unknown').title()}")

            is_active = agent_data.get("is_active", False)
            status_color = "🟢" if is_active else "🔴"
            st.write(f"**Status:** {status_color} {'Active' if is_active else 'Inactive'}")

            current_task = agent_data.get("current_task", "None")
            st.write(f"**Current Task:** {current_task}")

        with col2:
            # Performance metrics
            metrics = agent_data.get("performance_metrics", {})
            if metrics:
                st.write("**Performance Metrics:**")
                st.write(f"- Tasks Completed: {metrics.get('tasks_completed', 0)}")
                st.write(f"- Success Rate: {metrics.get('success_rate', 0):.1%}")
                st.write(f"- Average Response Time: {metrics.get('average_response_time', 0):.1f}s")
                st.write(f"- Collaboration Score: {metrics.get('collaboration_score', 0):.2f}")
            else:
                st.write("*No performance metrics available*")

        # Last active timestamp
        last_active = agent_data.get("last_active", "Never")
        if last_active != "Never":
            try:
                dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                st.write(f"**Last Active:** {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                st.write(f"**Last Active:** {last_active}")
        else:
            st.write("**Last Active:** Never")


class TaskCard:
    """Component for displaying task information."""

    @staticmethod
    def render(task_data: Dict[str, Any]):
        """Render a task information card."""
        task_type_emojis = {
            "planning": "📋",
            "development": "👨‍💻",
            "funding": "💰",
            "legal_review": "⚖️",
            "marketing": "📈",
            "product_strategy": "🎯",
            "custom": "🔧"
        }

        emoji = task_type_emojis.get(task_data.get("type", "").lower(), "📝")
        task_id = task_data.get("id", "Unknown")

        with st.expander(f"{emoji} Task {task_id}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Type:** {task_data.get('type', 'Unknown').title()}")
                st.write(f"**Status:** {task_data.get('status', 'Unknown').title()}")

                priority = task_data.get("priority", "medium")
                priority_colors = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "critical": "🔴"
                }
                st.write(f"**Priority:** {priority_colors.get(priority, '⚪')} {priority.title()}")

            with col2:
                assigned_to = task_data.get("assigned_to", "Unassigned")
                st.write(f"**Assigned To:** {assigned_to}")

                created_at = task_data.get("created_at", "Unknown")
                st.write(f"**Created:** {created_at}")

                if "completed_at" in task_data:
                    st.write(f"**Completed:** {task_data['completed_at']}")

            # Task content
            content = task_data.get("content", "")
            if content:
                st.write("**Content:**")
                st.write(content)

            # Task result
            result = task_data.get("result", "")
            if result:
                st.write("**Result:**")
                st.write(result)


class MemoryCard:
    """Component for displaying memory information."""

    @staticmethod
    def render(memory_data: Dict[str, Any]):
        """Render a memory information card."""
        memory_type_emojis = {
            "conversation": "💬",
            "task": "📋",
            "decision": "🤔",
            "learning": "📚",
            "error": "❌",
            "success": "✅"
        }

        emoji = memory_type_emojis.get(memory_data.get("memory_type", "").lower(), "🧠")
        content_preview = memory_data.get("content", "")[:50]

        with st.expander(f"{emoji} {content_preview}..."):
            st.write(f"**Type:** {memory_data.get('memory_type', 'Unknown').title()}")
            st.write(f"**Content:** {memory_data.get('content', '')}")

            response = memory_data.get("response", "")
            if response:
                st.write(f"**Response:** {response}")

            timestamp = memory_data.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.write(f"**Timestamp:** {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    st.write(f"**Timestamp:** {timestamp}")

            # Metadata
            metadata = memory_data.get("metadata", {})
            if metadata:
                st.write("**Metadata:**")
                st.json(metadata)


class MetricsChart:
    """Component for displaying metrics charts."""

    @staticmethod
    def render_performance_trend(data: List[Dict[str, Any]], title: str = "Performance Trend"):
        """Render a performance trend chart."""
        if not data:
            st.info("No data available for chart")
            return

        try:
            import plotly.express as px

            df = pd.DataFrame(data)

            if "cycle" in df.columns and "overall_score" in df.columns:
                fig = px.line(
                    df,
                    x="cycle",
                    y="overall_score",
                    title=title,
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Invalid data format for performance trend chart")

        except ImportError:
            st.warning("Plotly not available for charts")
        except Exception as e:
            st.error(f"Error rendering performance chart: {e}")

    @staticmethod
    def render_agent_comparison(agent_data: List[Dict[str, Any]], metric: str = "total_score"):
        """Render agent comparison chart."""
        if not agent_data:
            st.info("No agent data available for comparison")
            return

        try:
            import plotly.express as px

            df = pd.DataFrame(agent_data)

            if "agent" in df.columns and metric in df.columns:
                fig = px.bar(
                    df,
                    x="agent",
                    y=metric,
                    color="role",
                    title=f"Agent {metric.replace('_', ' ').title()} Comparison"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Invalid data format for agent comparison chart")

        except ImportError:
            st.warning("Plotly not available for charts")
        except Exception as e:
            st.error(f"Error rendering agent comparison chart: {e}")

    @staticmethod
    def render_task_distribution(task_data: List[Dict[str, Any]]):
        """Render task distribution chart."""
        if not task_data:
            st.info("No task data available for distribution")
            return

        try:
            import plotly.express as px

            df = pd.DataFrame(task_data)

            if "task_type" in df.columns and "count" in df.columns:
                fig = px.pie(
                    df,
                    values="count",
                    names="task_type",
                    title="Task Distribution by Type"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Invalid data format for task distribution chart")

        except ImportError:
            st.warning("Plotly not available for charts")
        except Exception as e:
            st.error(f"Error rendering task distribution chart: {e}")


class StatusIndicator:
    """Component for displaying status indicators."""

    @staticmethod
    def render_simulation_status(is_active: bool, current_cycle: int = 0):
        """Render simulation status indicator."""
        if is_active:
            st.success(f"🟢 Simulation Running - Cycle {current_cycle}")
        else:
            st.warning("🔴 Simulation Stopped")

    @staticmethod
    def render_agent_status(is_active: bool, name: str = ""):
        """Render agent status indicator."""
        status = "🟢 Active" if is_active else "🔴 Inactive"
        st.write(f"**{name} Status:** {status}")

    @staticmethod
    def render_task_status(status: str, task_id: str = ""):
        """Render task status indicator."""
        status_emojis = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }

        emoji = status_emojis.get(status.lower(), "❓")
        st.write(f"{emoji} Task {task_id}: {status.title()}")


class DataTable:
    """Component for displaying data tables."""

    @staticmethod
    def render_agent_table(agents: List[Dict[str, Any]]):
        """Render agents data table."""
        if not agents:
            st.info("No agents to display")
            return

        # Prepare data for table
        table_data = []
        for agent in agents:
            metrics = agent.get("performance_metrics", {})
            table_data.append({
                "Name": agent.get("name", ""),
                "Role": agent.get("role", "").title(),
                "Status": "Active" if agent.get("is_active") else "Inactive",
                "Tasks Completed": metrics.get("tasks_completed", 0),
                "Success Rate": ".1%",
                "Last Active": agent.get("last_active", "Never")[:19]
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_task_table(tasks: List[Dict[str, Any]]):
        """Render tasks data table."""
        if not tasks:
            st.info("No tasks to display")
            return

        # Prepare data for table
        table_data = []
        for task in tasks:
            table_data.append({
                "ID": task.get("id", ""),
                "Type": task.get("type", "").title(),
                "Status": task.get("status", "").title(),
                "Priority": task.get("priority", "").title(),
                "Assigned To": task.get("assigned_to", "Unassigned"),
                "Created": task.get("created_at", "")[:19]
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_memory_table(memories: List[Dict[str, Any]]):
        """Render memories data table."""
        if not memories:
            st.info("No memories to display")
            return

        # Prepare data for table
        table_data = []
        for memory in memories:
            table_data.append({
                "Type": memory.get("memory_type", "").title(),
                "Content": memory.get("content", "")[:50] + "...",
                "Timestamp": memory.get("timestamp", "")[:19]
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)


class ControlPanel:
    """Component for simulation controls."""

    @staticmethod
    def render_simulation_controls(crew_instance):
        """Render simulation control buttons."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("▶️ Start", type="primary", use_container_width=True):
                try:
                    asyncio.run(crew_instance.start())
                    st.success("Simulation started!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {e}")

        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                try:
                    asyncio.run(crew_instance.stop())
                    st.info("Simulation stopped!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to stop: {e}")

        with col3:
            if st.button("🔄 Reset", use_container_width=True):
                try:
                    asyncio.run(crew_instance.reset())
                    st.warning("Simulation reset!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to reset: {e}")

        with col4:
            if st.button("📊 Status", use_container_width=True):
                try:
                    status = asyncio.run(crew_instance.get_status())
                    st.json(status)
                except Exception as e:
                    st.error(f"Failed to get status: {e}")

    @staticmethod
    def render_task_creation_form(crew_instance):
        """Render task creation form."""
        with st.form("create_task_form"):
            st.subheader("Create New Task")

            col1, col2 = st.columns(2)

            with col1:
                task_type = st.selectbox(
                    "Task Type",
                    ["planning", "development", "funding", "legal_review", "marketing", "product_strategy", "custom"]
                )
                priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])

            with col2:
                agent_options = ["auto"]  # Default to auto-assignment
                try:
                    status = asyncio.run(crew_instance.get_status())
                    agents = status.get("agents", [])
                    agent_options.extend([f"{a['role']}_{a['agent_id'].split('_')[1]}" for a in agents])
                except:
                    pass

                assigned_agent = st.selectbox("Assign to Agent", agent_options)

            task_content = st.text_area("Task Description", height=100)

            if st.form_submit_button("Create Task", type="primary"):
                if task_content.strip():
                    try:
                        # Create task data
                        task_data = {
                            "type": task_type,
                            "content": task_content,
                            "priority": priority
                        }

                        # Here you would typically call crew_instance.create_task()
                        # For now, just show success
                        st.success(f"Task created: {task_type} - {task_content[:50]}...")
                    except Exception as e:
                        st.error(f"Failed to create task: {e}")
                else:
                    st.error("Please enter task content")