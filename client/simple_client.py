#!/usr/bin/env python3
"""
Simple wrapper around the openai_client to run a one-off question interactively.
"""

import os
import sys
import asyncio

# Add project root to path so we can import the openai_client module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from client.openai_client import LegalIntelligenceClient  # noqa: E402


async def main():
    cli = LegalIntelligenceClient()
    question = input("🔍 Question: ")
    result = await cli.chat(question)

    print("\n📄 RÉPONSE COMPLÈTE:")
    print("=" * 80)
    # Show full structured JSON (response + tools_used, phases, etc.)
    import json
    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ))
    print("=" * 80)

    tools = result.get("tools_used", [])
    if tools:
        print("\n🔧 WORKFLOW EXÉCUTÉ:")
        phases = {}
        for tool in tools:
            phase = tool.get("phase", "❓ UNKNOWN")
            phases.setdefault(phase, []).append(
                f"{tool['name']} (iter {tool['iteration']})"
            )
        for phase, items in phases.items():
            print(f"   {phase}:")
            for item in items:
                print(f"      • {item}")


if __name__ == '__main__':
    asyncio.run(main())
