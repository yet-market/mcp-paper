#!/usr/bin/env python3
"""
CLI Client for Luxembourg Legal Intelligence MCP Server
Interactive workflow with phase control and content extraction
"""

import os
import json
import asyncio
import argparse
from typing import Dict, List, Any, Optional
import anthropic
from groq import AsyncGroq
from dotenv import load_dotenv
import logging
import time
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

load_dotenv()
logger = logging.getLogger(__name__)


class InteractiveLegalClient:
    """Interactive CLI client with phase control for Luxembourg Legal Intelligence."""

    def __init__(self):
        # Model configuration
        self.model_provider = os.getenv("MODEL_PROVIDER", "groq")
        self.mcp_server_url = "http://localhost:8080/mcp"

        # Initialize AI client
        if self.model_provider == "groq":
            self.groq_api_key = os.getenv("GROQ_API_KEY")
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.model = "llama-3.3-70b-versatile"
            self.client = AsyncGroq(api_key=self.groq_api_key)
            self.is_groq = True
        else:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.model = "claude-3-5-sonnet-20241022"
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            self.is_groq = False

        self.available_tools = []
        self._tools_initialized = False

    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return

        logger.info("🔧 Initializing workflow tools...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()

                expected_tools = [
                    # Phase 1: Discovery
                    "find_most_cited_laws", "find_most_changed_laws",
                    "find_newest_active_laws", "find_highest_authority_laws",
                    # Phase 2: Analysis
                    "compare_results", "check_connections",
                    # Phase 3: Relationships
                    "find_what_law_references", "find_what_references_law", "find_amendment_chain",
                    # Phase 4: Final
                    "verify_still_valid", "rank_by_importance", "create_final_map",
                    # Content & Bonus
                    "extract_content", "basic_document_search"
                ]

                self.available_tools = []
                for tool in tools:
                    if tool.name in expected_tools:
                        claude_tool = {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        }
                        self.available_tools.append(claude_tool)

            self._tools_initialized = True
            logger.info(f"✅ Initialized {len(self.available_tools)} workflow tools")

        except Exception as e:
            logger.error(f"❌ Failed to initialize tools: {e}")
            self.available_tools = []

    async def call_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool and return result."""
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, tool_input)
                return {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name,
                    "tool_input": tool_input
                }
        except Exception as e:
            logger.error(f"❌ MCP tool call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_input": tool_input
            }

    def get_phase_tools(self, phase: int) -> List[str]:
        """Get tools for a specific phase."""
        phase_tools = {
            1: ["find_most_cited_laws", "find_most_changed_laws", "find_newest_active_laws", "find_highest_authority_laws"],
            2: ["compare_results", "check_connections"],
            3: ["find_what_law_references", "find_what_references_law", "find_amendment_chain"],
            4: ["verify_still_valid", "rank_by_importance", "create_final_map"]
        }
        return phase_tools.get(phase, [])

    def get_system_prompt(self, target_phase: int, include_content: bool = False) -> str:
        """Generate system prompt based on target phase."""
        base_prompt = """Vous êtes un assistant juridique expert en droit luxembourgeois avec accès à un système de recherche légale professionnel en 4 phases.

OUTILS DISPONIBLES (workflow par phases) :

🏗️ PHASE 1 - DÉCOUVERTE (Trouver les grandes lois) :
- find_most_cited_laws : Lois les plus citées = importantes
- find_most_changed_laws : Lois les plus modifiées = actives  
- find_newest_active_laws : Lois récentes non annulées = actuelles
- find_highest_authority_laws : Documents LOI/CODE = autorité suprême

🔍 PHASE 2 - ANALYSE (Vérifier les résultats) :
- compare_results : Comparer les résultats pour trouver les recoupements
- check_connections : Voir comment les lois importantes se connectent

🕸️ PHASE 3 - RELATIONS (Arbre généalogique légal) :
- find_what_law_references : Ce que cette loi référence
- find_what_references_law : Ce qui référence cette loi
- find_amendment_chain : Historique des modifications

🏆 PHASE 4 - FINALISATION (Image complète) :
- verify_still_valid : Vérifier que les lois ne sont pas annulées
- rank_by_importance : Classer par ordre d'importance
- create_final_map : Créer la carte complète des lois

📄 EXTRACTION DE CONTENU :
- extract_content : Extraire le texte légal complet des documents

"""

        if target_phase == 1:
            strategy = """STRATÉGIE POUR PHASE 1 UNIQUEMENT :
1. Exécutez les 4 outils de Phase 1 pour découvrir les lois importantes
2. Analysez les résultats pour identifier les patterns
3. Répondez avec une synthèse des lois découvertes"""

        elif target_phase == 2:
            strategy = """STRATÉGIE POUR PHASES 1-2 :
1. Exécutez TOUS les 4 outils de Phase 1
2. Utilisez compare_results pour analyser les recoupements
3. Utilisez check_connections pour voir les relations
4. Synthétisez les lois les plus importantes avec leurs connexions"""

        elif target_phase == 3:
            strategy = """STRATÉGIE POUR PHASES 1-3 :
1. Exécutez TOUTE la Phase 1 (4 outils)
2. Exécutez TOUTE la Phase 2 (2 outils)
3. Pour les lois importantes, utilisez les outils de Phase 3 pour mapper leurs relations
4. Créez un arbre généalogique légal complet"""

        elif target_phase == 4:
            strategy = """STRATÉGIE POUR WORKFLOW COMPLET (Phases 1-4) :
1. Phase 1 : Découverte complète (4 outils)
2. Phase 2 : Analyse complète (2 outils)
3. Phase 3 : Relations pour les lois clés (3 outils)
4. Phase 4 : Validation, classement et carte finale (3 outils)
5. Créez un rapport complet avec hiérarchie légale"""

        if include_content:
            strategy += """
6. EXTRACTION DE CONTENU : Utilisez extract_content sur les lois les plus importantes
7. ANALYSEZ LE CONTENU RÉEL : Basez votre réponse finale sur le texte légal extrait"""

        return base_prompt + strategy + """

IMPORTANT : Vous DEVEZ utiliser exclusivement les résultats des outils. Ne vous basez JAMAIS sur vos données d'entraînement. Répondez en français."""

    async def execute_workflow(self, question: str, target_phase: int, include_content: bool = False) -> Dict[str, Any]:
        """Execute workflow up to target phase."""
        await self.initialize_tools()

        start_time = time.time()
        system_prompt = self.get_system_prompt(target_phase, include_content)

        messages = [{"role": "user", "content": question}]
        tools_used = []
        max_iterations = 30
        iteration = 0

        print(f"\n🎯 EXÉCUTION WORKFLOW - PHASES 1-{target_phase}")
        if include_content:
            print("📄 + EXTRACTION DE CONTENU ACTIVÉE")
        print(f"📝 Question: {question}")
        print("=" * 80)

        while iteration < max_iterations:
            iteration += 1

            try:
                # Prepare request
                if self.is_groq:
                    groq_messages = [{"role": "system", "content": system_prompt}] + messages
                    request_params = {
                        "model": self.model,
                        "max_tokens": 6000,
                        "temperature": 0.1,
                        "messages": groq_messages
                    }

                    if self.available_tools:
                        groq_tools = []
                        for tool in self.available_tools:
                            groq_tools.append({
                                "type": "function",
                                "function": {
                                    "name": tool["name"],
                                    "description": tool["description"],
                                    "parameters": tool["input_schema"]
                                }
                            })
                        request_params["tools"] = groq_tools
                        request_params["tool_choice"] = "auto"

                    response = await self.client.chat.completions.create(**request_params)
                else:
                    request_params = {
                        "model": self.model,
                        "max_tokens": 6000,
                        "temperature": 0.1,
                        "system": system_prompt,
                        "messages": messages
                    }

                    if self.available_tools:
                        request_params["tools"] = self.available_tools

                    response = await self.client.messages.create(**request_params)

                # Handle response
                if self.is_groq:
                    if response.choices[0].finish_reason == "tool_calls":
                        assistant_message = {
                            "role": "assistant",
                            "content": response.choices[0].message.content or ""
                        }
                        if response.choices[0].message.tool_calls:
                            assistant_message["tool_calls"] = []
                            for tool_call in response.choices[0].message.tool_calls:
                                assistant_message["tool_calls"].append({
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                })
                        messages.append(assistant_message)

                        tool_results = []
                        for tool_call in response.choices[0].message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_input = json.loads(tool_call.function.arguments)

                            phase_info = self.get_tool_phase(tool_name)
                            print(f"\n{phase_info} - EXÉCUTION: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "iteration": iteration, "phase": phase_info})

                            if tool_result["success"]:
                                print(f"✅ Succès: {tool_name}")
                                if tool_name == "extract_content" and tool_result["result"]:
                                    # Show content extraction summary
                                    result_data = tool_result["result"]
                                    success_count = result_data.get("success_count", 0)
                                    total = result_data.get("total_processed", 0)
                                    print(f"📄 Contenu extrait: {success_count}/{total} documents")
                            else:
                                print(f"❌ Erreur: {tool_result['error']}")

                            # Handle TextContent objects from Groq
                            try:
                                formatted_result = json.dumps(tool_result["result"], ensure_ascii=False, indent=2)
                            except TypeError:
                                # Fallback for non-serializable objects
                                formatted_result = str(tool_result["result"])

                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": formatted_result
                            })

                        messages.extend(tool_results)
                        continue

                    else:
                        # Final response
                        final_response = response.choices[0].message.content or ""
                        processing_time = time.time() - start_time

                        phases_used = list(set([tool.get("phase", "Unknown") for tool in tools_used]))

                        print(f"\n✅ WORKFLOW TERMINÉ")
                        print(f"🔧 Outils utilisés: {len(tools_used)}")
                        print(f"⏱️ Temps: {processing_time:.2f}s")
                        print(f"🎯 Phases: {', '.join(phases_used)}")
                        print("=" * 80)

                        return {
                            "response": final_response,
                            "tools_used": tools_used,
                            "phases_used": phases_used,
                            "processing_time": processing_time,
                            "target_phase": target_phase,
                            "content_extracted": include_content and any(t["name"] == "extract_content" for t in tools_used),
                            "success": True
                        }

                elif response.stop_reason == "tool_use":
                    assistant_message = {"role": "assistant", "content": response.content}
                    messages.append(assistant_message)

                    tool_results = []
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input

                            phase_info = self.get_tool_phase(tool_name)
                            print(f"\n{phase_info} - EXÉCUTION: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "iteration": iteration, "phase": phase_info})

                            if tool_result["success"]:
                                print(f"✅ Succès: {tool_name}")
                                if tool_name == "extract_content" and tool_result["result"]:
                                    result_data = tool_result["result"]
                                    success_count = result_data.get("success_count", 0)
                                    total = result_data.get("total_processed", 0)
                                    print(f"📄 Contenu extrait: {success_count}/{total} documents")
                            else:
                                print(f"❌ Erreur: {tool_result['error']}")

                            # Handle TextContent objects from Anthropic
                            try:
                                formatted_result = json.dumps(tool_result["result"], ensure_ascii=False, indent=2)
                            except TypeError:
                                # Fallback for non-serializable objects
                                formatted_result = str(tool_result["result"])

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": formatted_result
                            })

                    messages.append({"role": "user", "content": tool_results})
                    continue

                else:
                    # Final response
                    final_response = ""
                    for content_block in response.content:
                        if content_block.type == "text":
                            final_response += content_block.text

                    processing_time = time.time() - start_time
                    phases_used = list(set([tool.get("phase", "Unknown") for tool in tools_used]))

                    print(f"\n✅ WORKFLOW TERMINÉ")
                    print(f"🔧 Outils utilisés: {len(tools_used)}")
                    print(f"⏱️ Temps: {processing_time:.2f}s")
                    print(f"🎯 Phases: {', '.join(phases_used)}")
                    print("=" * 80)

                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "phases_used": phases_used,
                        "processing_time": processing_time,
                        "target_phase": target_phase,
                        "content_extracted": include_content and any(t["name"] == "extract_content" for t in tools_used),
                        "success": True
                    }

            except Exception as e:
                logger.error(f"❌ Error: {e}")
                return {
                    "response": f"Erreur: {str(e)}",
                    "tools_used": tools_used,
                    "error": str(e),
                    "success": False
                }

        return {
            "response": "Limite d'itérations atteinte.",
            "tools_used": tools_used,
            "warning": "Max iterations reached",
            "success": False
        }

    def get_tool_phase(self, tool_name: str) -> str:
        """Get phase for a tool."""
        phase_map = {
            # Phase 1
            "find_most_cited_laws": "🏗️ PHASE 1",
            "find_most_changed_laws": "🏗️ PHASE 1",
            "find_newest_active_laws": "🏗️ PHASE 1",
            "find_highest_authority_laws": "🏗️ PHASE 1",
            # Phase 2
            "compare_results": "🔍 PHASE 2",
            "check_connections": "🔍 PHASE 2",
            # Phase 3
            "find_what_law_references": "🕸️ PHASE 3",
            "find_what_references_law": "🕸️ PHASE 3",
            "find_amendment_chain": "🕸️ PHASE 3",
            # Phase 4
            "verify_still_valid": "🏆 PHASE 4",
            "rank_by_importance": "🏆 PHASE 4",
            "create_final_map": "🏆 PHASE 4",
            # Content & Bonus
            "extract_content": "📄 CONTENU",
            "basic_document_search": "🎁 BONUS"
        }
        return phase_map.get(tool_name, "❓ UNKNOWN")

    def show_phase_options(self):
        """Show available phase options."""
        print("\n🎯 OPTIONS DE WORKFLOW DISPONIBLES:")
        print("=" * 50)
        print("1️⃣  Phase 1 uniquement (Découverte)")
        print("    - Trouve les lois importantes par 4 méthodes")
        print("    - Rapide, vue d'ensemble")
        print()
        print("2️⃣  Phases 1-2 (Découverte + Analyse)")
        print("    - Phase 1 + comparaison des résultats")
        print("    - Identifie les lois qui reviennent souvent")
        print()
        print("3️⃣  Phases 1-3 (+ Relations)")
        print("    - Phases 1-2 + arbre généalogique légal")
        print("    - Comprend comment les lois se connectent")
        print()
        print("4️⃣  Phases 1-4 (Workflow complet)")
        print("    - Toutes les phases + validation et classement")
        print("    - Analyse complète, carte légale finale")
        print()
        print("🚀 Full (Workflow complet + Extraction de contenu)")
        print("    - Workflow complet + texte légal des documents")
        print("    - Analyse basée sur le contenu réel des lois")
        print("=" * 50)


async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Luxembourg Legal Intelligence CLI")
    parser.add_argument("--question", "-q", help="Question légale à poser")
    parser.add_argument("--phase", "-p", help="Phase cible (1, 2, 3, 4, ou 'full')")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")

    args = parser.parse_args()

    client = InteractiveLegalClient()

    print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - CLI WORKFLOW")
    print("=" * 60)
    print(f"🤖 Modèle: {client.model_provider.upper()} - {client.model}")
    print("=" * 60)

    if args.interactive or not (args.question and args.phase):
        # Interactive mode
        while True:
            try:
                client.show_phase_options()

                # Get question
                if not args.question:
                    question = input("\n📝 Votre question légale: ").strip()
                    if not question:
                        print("❌ Question requise!")
                        continue
                else:
                    question = args.question
                    print(f"\n📝 Question: {question}")

                # Get phase
                if not args.phase:
                    phase_input = input("\n🎯 Choisissez la phase (1/2/3/4/full): ").strip().lower()
                else:
                    phase_input = args.phase.lower()
                    print(f"🎯 Phase sélectionnée: {phase_input}")

                # Parse phase
                include_content = False
                if phase_input == "full":
                    target_phase = 4
                    include_content = True
                elif phase_input in ["1", "2", "3", "4"]:
                    target_phase = int(phase_input)
                else:
                    print("❌ Phase invalide! Utilisez 1, 2, 3, 4, ou 'full'")
                    continue

                # Execute workflow
                result = await client.execute_workflow(question, target_phase, include_content)

                if result["success"]:
                    print(f"\n📄 RÉPONSE FINALE:")
                    print("=" * 80)
                    print(result["response"])
                    print("=" * 80)

                    # Show summary
                    print(f"\n📊 RÉSUMÉ:")
                    print(f"✅ Phase cible: {result['target_phase']}")
                    print(f"🔧 Outils utilisés: {len(result['tools_used'])}")
                    print(f"⏱️ Temps: {result['processing_time']:.2f}s")
                    if result.get('content_extracted'):
                        print("📄 Contenu extrait: OUI")
                    print(f"🎯 Phases exécutées: {', '.join(result['phases_used'])}")
                else:
                    print(f"❌ Erreur: {result.get('response', 'Erreur inconnue')}")

                # Continue or exit
                if args.question and args.phase:
                    break  # Non-interactive mode, exit after one execution

                continue_choice = input("\n🔄 Continuer? (o/n): ").strip().lower()
                if continue_choice != 'o':
                    break

            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                break
    else:
        # Direct execution mode
        include_content = args.phase.lower() == "full"
        target_phase = 4 if include_content else int(args.phase)

        result = await client.execute_workflow(args.question, target_phase, include_content)

        if result["success"]:
            print(f"\n📄 RÉPONSE:")
            print(result["response"])
        else:
            print(f"❌ Erreur: {result.get('response', 'Erreur inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())
