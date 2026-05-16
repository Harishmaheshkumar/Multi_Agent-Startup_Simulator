"""Run a few sanity prompts against the local Ollama provider and print outputs.

Usage:
    python scripts/run_ollama_prompts.py

This script uses the project's `OllamaClient` to discover models and generate responses.
"""

import asyncio
from pathlib import Path

from app.llm.ollama_client import OllamaClient

PROMPTS = [
    ("Capability check", "What are your main capabilities and limitations for startup planning and research?"),
    ("Go-to-market", "You are an expert startup advisor. Provide a 3-step go-to-market plan for a SaaS productivity app."),
    ("Brainstorm acquisition", "List 5 low-cost user acquisition ideas for an early-stage B2B SaaS product."),
]

async def main():
    client = OllamaClient()
    await client.initialize()

    if not client.is_initialized():
        print("Ollama client not initialized or no models available."
              " Ensure Ollama is running and a model is pulled.")
        return

    print("Using model:", client.get_available_models_list()[:3])

    for title, prompt in PROMPTS:
        print('\n' + '='*10 + f' {title} ' + '='*10)
        try:
            resp = await client.generate_with_model(prompt)
            print(resp)
        except Exception as e:
            print(f"Error generating response for '{title}': {e}")

if __name__ == '__main__':
    asyncio.run(main())
