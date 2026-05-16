"""
Streamlit application for the Multi-Agent Startup Simulator.
"""

import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from ..crew.startup_crew import StartupCrew
from ..api.routes import set_crew_instance

# Global crew instance
crew = None


def create_app():
    """Create the Streamlit application."""
    global crew

    st.set_page_config(
        page_title="Multi-Agent Startup Simulator",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    _apply_style()

    st.markdown(
        """
        <div class="hero">
            <div>
                <h1>🚀 Multi-Agent Startup Simulator</h1>
                <p class="subtitle">Interactive startup orchestration with AI agents, real-time analytics and prompt-driven strategy.</p>
            </div>
            <div class="hero-badge">Streamlit · Ollama · Professional UI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if crew is None:
        crew = StartupCrew()
        asyncio.run(crew.initialize())
        set_crew_instance(crew)

    _render_sidebar()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", "Agents", "Prompt Lab", "Tasks", "Analytics"
    ])

    with tab1:
        _show_dashboard()
    with tab2:
        _show_agents()
    with tab3:
        _show_prompt_lab()
    with tab4:
        _show_tasks()
    with tab5:
        _show_analytics()


def _apply_style():
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #0a1128 0%, #101f3c 50%, #061021 100%); color: #f8fafc; }
        .hero { display: flex; justify-content: space-between; align-items: center; gap: 1rem; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 1.6rem; margin-bottom: 1.5rem; }
        .hero h1 { margin: 0; color: #ffffff; }
        .subtitle { margin: 0.25rem 0 0; color: #cbd5e1; font-size: 1.05rem; }
        .hero-badge { background: linear-gradient(135deg, #4f46e5, #0ea5e9); color: white; padding: 0.75rem 1rem; border-radius: 999px; font-weight: 700; box-shadow: 0 12px 28px rgba(14,165,233,0.26); }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.10); border-radius: 18px; padding: 1.2rem; margin-bottom: 1rem; }
        .stButton>button { background: linear-gradient(135deg, #34d399, #0ea5e9) !important; color: white !important; border: none !important; box-shadow: 0 10px 30px rgba(14,165,233,0.25); }
        .stButton>button:hover { filter: brightness(1.05); }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div>div { background: rgba(255,255,255,0.08) !important; color: #f8fafc !important; border: 1px solid rgba(255,255,255,0.14) !important; }
        .stSidebar .css-1d391kg, .stSidebar .css-1aumxhk { background: #07101f; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar():
    with st.sidebar:
        st.markdown("## Controls")
        st.write("Manage simulation flow and create custom tasks from the sidebar.")

        if st.button("Start Simulation"):
            if not crew.is_active:
                asyncio.run(crew.start())
                st.success("Simulation started!")
                st.experimental_rerun()

        if st.button("Stop Simulation"):
            if crew.is_active:
                asyncio.run(crew.stop())
                st.info("Simulation stopped!")
                st.experimental_rerun()

        if st.button("Reset Simulation"):
            asyncio.run(crew.reset())
            st.warning("Simulation reset!")
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("### Custom Task")
        with st.form("task_form"):
            agent_options = [agent.role.value for agent in crew.agents]
            selected_agent = st.selectbox("Agent", agent_options)
            task_type = st.selectbox("Task Type", [
                "planning", "development", "funding", "legal_review",
                "marketing", "product_strategy", "custom"
            ])
            task_content = st.text_area("Task Content", height=100)
            priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])

            if st.form_submit_button("Create Task"):
                if task_content.strip():
                    task_data = {
                        "type": task_type,
                        "content": task_content,
                        "priority": priority
                    }
                    target_agent = next((agent for agent in crew.agents if agent.role.value == selected_agent), None)
                    if target_agent:
                        result = asyncio.run(target_agent.process_task(task_data))
                        st.success("Task created and executed!")
                        st.info(result.get("response", "No response"))
                    else:
                        st.error("Agent not found")
                else:
                    st.error("Please enter task content")

        st.markdown("---")
        st.markdown("### Prompt Ideas")
        st.write("• Generate a go-to-market plan")
        st.write("• Audit product-market fit")
        st.write("• Brainstorm growth tactics")


def _show_dashboard():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Simulation Overview")

    status = _safe_status()
    current_cycle = status.get("current_cycle", 0)
    tasks_completed = status.get("tasks_completed", 0)
    agent_count = len(status.get("agents", []))
    is_active = status.get("is_active", False)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", "Running" if is_active else "Stopped", delta="Live" if is_active else "Paused")
    col2.metric("Current Cycle", current_cycle)
    col3.metric("Tasks Completed", tasks_completed)
    col4.metric("Active Agents", agent_count)

    st.markdown("</div>", unsafe_allow_html=True)

    if crew.is_active:
        st.success("Simulation is active and progressing.")
    else:
        st.warning("Simulation is currently stopped.")


def _show_prompt_lab():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Prompt Lab")
    st.write("Ask the running Ollama model questions and get instant responses.")

    providers = asyncio.run(crew.model_loader.get_available_providers())
    provider = providers[0] if providers else "ollama"
    st.write(f"**Provider:** {provider}")

    prompt = st.text_area(
        "Enter your prompt",
        value="List 5 low-cost user acquisition ideas for an early-stage B2B SaaS product.",
        height=180
    )

    if st.button("Generate Response"):
        with st.spinner("Generating response..."):
            response = asyncio.run(crew.model_loader.generate_response(prompt, provider=provider))
            st.markdown("### Response")
            st.write(response)

    st.markdown("---")
    st.write("#### Example prompts")
    st.write("- Launch a product roadmap")
    st.write("- Summarize competitors and target segments")
    st.write("- Create a product strategy checklist")
    st.markdown("</div>", unsafe_allow_html=True)


def _show_agents():
    st.header("Agent Overview")
    status = _safe_status()
    agents = status.get("agents", [])

    if not agents:
        st.info("No agents available yet.")
        return

    for agent_data in agents:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        cols = st.columns([1, 3])
        with cols[0]:
            st.markdown(f"### {agent_data.get('name', 'Agent')}")
            st.write(f"**Role:** {agent_data.get('role', 'Unknown')}")
            active = "🟢 Active" if agent_data.get("is_active") else "🔴 Inactive"
            st.write(f"**Status:** {active}")
        with cols[1]:
            st.write(f"**Current Task:** {agent_data.get('current_task', 'None')}")
            metrics = agent_data.get("performance_metrics", {})
            if metrics:
                st.write(f"- Tasks Completed: {metrics.get('tasks_completed', 0)}")
                st.write(f"- Success Rate: {metrics.get('success_rate', 0):.1%}")
                st.write(f"- Collaboration Score: {metrics.get('collaboration_score', 0):.2f}")
        st.markdown("</div>", unsafe_allow_html=True)


def _show_tasks():
    st.header("Task Management")
    task_data = [
        {"id": "task_1", "type": "planning", "status": "completed", "agent": "CEO"},
        {"id": "task_2", "type": "development", "status": "in_progress", "agent": "Engineer"},
        {"id": "task_3", "type": "marketing", "status": "pending", "agent": "Marketer"}
    ]

    if task_data:
        st.dataframe(pd.DataFrame(task_data))
        completed = len([t for t in task_data if t["status"] == "completed"])
        pending = len([t for t in task_data if t["status"] == "pending"])
        in_progress = len([t for t in task_data if t["status"] == "in_progress"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Completed", completed)
        c2.metric("In Progress", in_progress)
        c3.metric("Pending", pending)
    else:
        st.info("No tasks available.")


def _show_analytics():
    st.header("Analytics")
    st.write("Visualize simulation performance and trends.")

    history = []
    try:
        history = crew.scorer.get_performance_history(limit=12)
    except Exception:
        history = []

    if history:
        df = pd.DataFrame(history)
        if not df.empty and "cycle" in df.columns and "overall_score" in df.columns:
            fig = px.line(df, x="cycle", y="overall_score", markers=True, title="Simulation Performance")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Performance data format not available.")
    else:
        st.info("No performance history available yet.")


def _safe_status() -> dict:
    try:
        return asyncio.run(crew.get_status())
    except Exception:
        return {}
