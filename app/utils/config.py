"""
Configuration management for the Multi-Agent Startup Simulator.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration settings."""

    # Environment
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # UI Settings
    ui_port: int = Field(default=8501, env="UI_PORT")
    run_ui: bool = Field(default=True, env="RUN_UI")

    # Simulation Settings
    run_simulation: bool = Field(default=True, env="RUN_SIMULATION")
    simulation_interval: int = Field(default=30, env="SIMULATION_INTERVAL")  # seconds

    # LLM Settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")

    # Memory Settings
    use_redis: bool = Field(default=False, env="USE_REDIS")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    vector_dimension: int = Field(default=384, env="VECTOR_DIMENSION")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")

    # CrewAI Settings
    max_iterations: int = Field(default=10, env="MAX_ITERATIONS")
    verbose: bool = Field(default=True, env="VERBOSE")

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "logs")
    conversations_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "conversations")
    embeddings_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "embeddings")
    startups_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "startups")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.conversations_dir.mkdir(exist_ok=True)
        self.embeddings_dir.mkdir(exist_ok=True)
        self.startups_dir.mkdir(exist_ok=True)


# Global config instance
config = Config()