"""
Main application entry point for the Multi-Agent Startup Simulator.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import streamlit.web.cli as st_cli

from .api.routes import router as api_router
from .crew.startup_crew import StartupCrew
from .ui.streamlit_app import create_app as create_streamlit_app
from .utils.config import Config
from .utils.logger import setup_logger

logger = setup_logger(__name__)

class StartupSimulatorApp:
    """Main application class."""

    def __init__(self):
        self.config = Config()
        self.crew: Optional[StartupCrew] = None
        self.fastapi_app = self._create_fastapi_app()

    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="Multi-Agent Startup Simulator API",
            description="API for the Multi-Agent Startup Simulator",
            version="1.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include API routes
        app.include_router(api_router, prefix="/api")

        @app.get("/")
        async def root():
            return {"message": "Multi-Agent Startup Simulator API"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        return app

    async def initialize(self):
        """Initialize the application components."""
        logger.info("Initializing Startup Simulator...")

        # Initialize the startup crew
        self.crew = StartupCrew()
        await self.crew.initialize()

        logger.info("Startup Simulator initialized successfully")

    async def run_api_server(self):
        """Run the FastAPI server."""
        config = uvicorn.Config(
            self.fastapi_app,
            host=self.config.api_host,
            port=self.config.api_port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        logger.info(f"Starting API server on {self.config.api_host}:{self.config.api_port}")
        await server.serve()

    async def run_streamlit_app(self):
        """Run the Streamlit application."""
        import sys
        from streamlit.web import cli

        # Change to the UI directory
        ui_dir = Path(__file__).parent / "ui"
        os.chdir(ui_dir)

        # Run streamlit
        sys.argv = ["streamlit", "run", "streamlit_app.py", "--server.port", str(self.config.ui_port)]
        cli.main()

    async def run_simulation(self):
        """Run the main simulation loop."""
        logger.info("Starting simulation...")

        while True:
            try:
                # Run crew tasks
                if self.crew:
                    await self.crew.run_cycle()

                # Wait before next cycle
                await asyncio.sleep(self.config.simulation_interval)

            except KeyboardInterrupt:
                logger.info("Simulation stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in simulation cycle: {e}")
                await asyncio.sleep(5)  # Wait before retrying

async def main():
    """Main application entry point."""
    app = StartupSimulatorApp()

    try:
        await app.initialize()

        # Create tasks for concurrent execution
        tasks = []

        # Always run the API server
        tasks.append(asyncio.create_task(app.run_api_server()))

        # Run simulation if configured
        if app.config.run_simulation:
            tasks.append(asyncio.create_task(app.run_simulation()))

        # Run Streamlit UI if configured
        if app.config.run_ui:
            # Streamlit needs to run in main thread, so we'll run it separately
            pass

        # Wait for tasks
        await asyncio.gather(*tasks, return_exceptions=True)

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())