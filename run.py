#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Startup Simulator.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.main import main

if __name__ == "__main__":
    asyncio.run(main())