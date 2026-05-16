# Multi-Agent Startup Simulator

A sophisticated simulation platform that models the dynamics of a startup ecosystem using multiple AI agents. Each agent represents a key role in a startup (CEO, Engineer, Investor, Legal, Marketer, Product Manager) and collaborates to simulate realistic startup scenarios.

## Features

- **Multi-Agent Collaboration**: Six specialized agents working together
- **CrewAI Integration**: Advanced task orchestration and workflow management
- **Memory System**: Persistent memory with Redis and vector embeddings
- **LLM Support**: Native Ollama integration for local/hosted model serving
- **Real-time Dashboard**: Streamlit-based UI for monitoring simulations
- **API Endpoints**: RESTful API for external integrations
- **Market Research Tools**: Competitor analysis and market validation
- **Financial Modeling**: Investment and financial planning tools

## Architecture

The system consists of:

- **Agents**: Specialized AI agents for different startup roles
- **Crew**: Task orchestration using CrewAI framework
- **Memory**: Vector-based memory system for context retention
- **Orchestration**: Debate engines and discussion managers
- **Tools**: Specialized tools for research and analysis
- **UI**: Web interface for interaction and monitoring

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run setup: `.\setup.ps1`
5. Start the application: `python run.py`

## Usage

### Running the Simulation

```bash
python run.py
```

### Web Interface

Access the Streamlit dashboard at `http://localhost:8501`

### API

The FastAPI server runs on `http://localhost:8000`

## Configuration

Edit `app/utils/config.py` for system configuration.

## Docker

Build and run with Docker Compose:

```bash
docker-compose up --build
```

## Testing

Run tests with:

```bash
python -m pytest tests/
```