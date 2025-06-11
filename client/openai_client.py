#!/usr/bin/env python3
"""
Simple Client for Luxembourg Legal Intelligence MCP Server
Workflow Edition using the new streamlined 13-tool workflow system
"""

import os
import json
import asyncio
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


class LegalIntelligenceClient:
    """Client for the new 13-tool Luxembourg Legal Intelligence workflow system."""

    def __init__(self):
        # Model configuration - easy to change
        self.model_provider = os.getenv("MODEL_PROVIDER", "groq")  # anthropic or groq
        # URL of the MCP endpoint (must include '/mcp' path)
        self.mcp_server_url = "http://localhost:8080/mcp"

        # Initialize the appropriate client and model
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

        # Updated system prompt for the new workflow tools
        self.system_prompt = """Vous êtes un assistant juridique expert en droit luxembourgeois avec accès à un système de recherche légale professionnel en 4 phases.

OUTILS DISPONIBLES (13 outils organisés en workflow) :

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

🎁 BONUS :
- basic_document_search : Recherche simple par mots-clés

STRATÉGIE RECOMMANDÉE :
1. Pour une recherche complète : Suivez les 4 phases dans l'ordre
2. Pour une recherche rapide : Utilisez basic_document_search
3. Pour analyser une loi spécifique : Utilisez les outils de Phase 3

Utilisez ces outils de manière stratégique selon la complexité de la question. Répondez en français en vous basant exclusivement sur les résultats des outils."""

        self.available_tools = []
        self._tools_initialized = False

    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return

        logger.info("🔧 Initializing new workflow tools...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()

                # Define expected workflow tools
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
                    # Bonus
                    "basic_document_search"
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

            # Show organized tools
            print(f"\n🔧 OUTILS DE WORKFLOW DISPONIBLES ({len(self.available_tools)} outils):")
            print("🏗️ Phase 1 (Découverte):", [t["name"] for t in self.available_tools if t["name"].startswith("find_")])
            print("🔍 Phase 2 (Analyse):", [t["name"] for t in self.available_tools if t["name"] in ["compare_results", "check_connections"]])
            print("🕸️ Phase 3 (Relations):", [t["name"] for t in self.available_tools if "reference" in t["name"] or "amendment" in t["name"]])
            print("🏆 Phase 4 (Final):", [t["name"] for t in self.available_tools if t["name"] in ["verify_still_valid", "rank_by_importance", "create_final_map"]])
            print("🎁 Bonus:", [t["name"] for t in self.available_tools if t["name"] == "basic_document_search"])
            print()

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

    def format_tool_result(self, tool_result: Dict[str, Any]) -> str:
        """Format tool execution result for Claude."""
        if not tool_result["success"]:
            return f"❌ Erreur lors de l'exécution de l'outil {tool_result['tool_name']}: {tool_result['error']}"

        result = tool_result["result"]
        tool_name = tool_result["tool_name"]

        # Enhanced formatting for workflow tools
        if tool_name in ["find_most_cited_laws", "find_most_changed_laws", "find_newest_active_laws", "find_highest_authority_laws"]:
            if isinstance(result, dict) and result.get("success"):
                laws_count = result.get("total_found", 0)
                method = result.get("method", "unknown")
                keywords = result.get("keywords", [])
                phase = "🏗️ PHASE 1 - DÉCOUVERTE"
                return f"{phase} - {tool_name.upper()}\n📊 Méthode: {method}\n🔍 Mots-clés: {keywords}\n📋 Trouvé: {laws_count} lois\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "compare_results":
            if isinstance(result, dict) and result.get("success"):
                total_laws = result.get("statistics", {}).get("total_laws", 0)
                multi_method = result.get("statistics", {}).get("multi_method_count", 0)
                high_confidence = result.get("statistics", {}).get("high_confidence_count", 0)
                phase = "🔍 PHASE 2 - ANALYSE"
                return f"{phase} - COMPARAISON DES RÉSULTATS\n📊 Total: {total_laws} lois\n🎯 Multi-méthodes: {multi_method} lois\n✅ Haute confiance: {high_confidence} lois\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "check_connections":
            if isinstance(result, dict) and result.get("success"):
                connections = result.get("statistics", {}).get("total_connections", 0)
                connected_laws = result.get("statistics", {}).get("connected_laws", 0)
                phase = "🔍 PHASE 2 - ANALYSE"
                return f"{phase} - VÉRIFICATION DES CONNEXIONS\n🔗 Connexions: {connections}\n📋 Lois connectées: {connected_laws}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name in ["find_what_law_references", "find_what_references_law"]:
            if isinstance(result, dict) and result.get("success"):
                total_found = result.get("total_found", 0)
                relationship_type = result.get("relationship_type", "unknown")
                phase = "🕸️ PHASE 3 - RELATIONS"
                return f"{phase} - {tool_name.upper()}\n📊 Type: {relationship_type}\n📋 Trouvé: {total_found} relations\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "find_amendment_chain":
            if isinstance(result, dict) and result.get("success"):
                total_amendments = result.get("total_amendments", 0)
                incoming = len(result.get("incoming_amendments", []))
                outgoing = len(result.get("outgoing_amendments", []))
                phase = "🕸️ PHASE 3 - RELATIONS"
                return f"{phase} - CHAÎNE D'AMENDEMENTS\n📝 Total: {total_amendments} amendements\n⬇️ Entrants: {incoming}\n⬆️ Sortants: {outgoing}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "verify_still_valid":
            if isinstance(result, dict) and result.get("success"):
                total_checked = result.get("statistics", {}).get("total_checked", 0)
                valid_count = result.get("statistics", {}).get("valid_count", 0)
                validity_rate = result.get("statistics", {}).get("validity_rate", 0)
                phase = "🏆 PHASE 4 - FINALISATION"
                return f"{phase} - VÉRIFICATION DE VALIDITÉ\n📊 Vérifiées: {total_checked} lois\n✅ Valides: {valid_count} lois\n📈 Taux: {validity_rate:.1%}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "rank_by_importance":
            if isinstance(result, dict) and result.get("success"):
                total_laws = result.get("statistics", {}).get("total_laws", 0)
                average_score = result.get("statistics", {}).get("average_score", 0)
                critical_laws = len(result.get("critical_laws", []))
                phase = "🏆 PHASE 4 - FINALISATION"
                return f"{phase} - CLASSEMENT PAR IMPORTANCE\n📊 Total: {total_laws} lois\n🎯 Score moyen: {average_score}\n🔥 Critiques: {critical_laws} lois\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "create_final_map":
            if isinstance(result, dict) and result.get("success"):
                total_mapped = result.get("summary", {}).get("total_laws_mapped", 0)
                core_framework = result.get("summary", {}).get("core_legal_framework", 0)
                total_relationships = result.get("summary", {}).get("total_relationships", 0)
                phase = "🏆 PHASE 4 - FINALISATION"
                return f"{phase} - CARTE LÉGALE FINALE\n🗺️ Lois cartographiées: {total_mapped}\n🏛️ Cadre central: {core_framework} lois\n🔗 Relations: {total_relationships}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        elif tool_name == "basic_document_search":
            if isinstance(result, dict) and result.get("success"):
                total_found = result.get("total_found", 0)
                keywords = result.get("keywords", [])
                phase = "🎁 BONUS"
                return f"{phase} - RECHERCHE SIMPLE\n🔍 Mots-clés: {keywords}\n📋 Trouvé: {total_found} documents\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"

        # Default formatting
        try:
            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        except (TypeError, AttributeError):
            return str(result)

    async def chat(self, message: str) -> Dict[str, Any]:
        """Enhanced chat with professional legal research workflow."""
        start_time = time.time()

        await self.initialize_tools()

        messages = [{"role": "user", "content": message}]
        tools_used = []
        max_iterations = 25  # Increased for comprehensive workflow
        iteration = 0

        print(f"\n🧠 RECHERCHE LÉGALE WORKFLOW PROFESSIONNEL")
        print(f"📝 Question: {message}")
        print(f"🔧 Outils disponibles: {len(self.available_tools)} (workflow complet)")
        print("=" * 80)

        while iteration < max_iterations:
            iteration += 1

            try:
                # Prepare request parameters based on provider
                if self.is_groq:
                    # Groq/Llama format (OpenAI-compatible)
                    groq_messages = [{"role": "system", "content": self.system_prompt}] + messages
                    request_params = {
                        "model": self.model,
                        "max_tokens": 4000,
                        "temperature": 0.3,
                        "messages": groq_messages
                    }

                    if self.available_tools:
                        # Convert Anthropic MCP tools to OpenAI format
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
                    # Anthropic format
                    request_params = {
                        "model": self.model,
                        "max_tokens": 4000,
                        "temperature": 0.3,
                        "system": self.system_prompt,
                        "messages": messages
                    }

                    if self.available_tools:
                        request_params["tools"] = self.available_tools

                    response = await self.client.messages.create(**request_params)

                # Handle response based on provider
                if self.is_groq:
                    # Groq/OpenAI format
                    if response.choices[0].finish_reason == "tool_calls":
                        # Handle tool calls for Groq
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

                        tool_results_for_claude = []

                        for tool_call in response.choices[0].message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_input = json.loads(tool_call.function.arguments)
                            tool_use_id = tool_call.id

                            # Show which phase this tool belongs to
                            phase_info = self.get_tool_phase(tool_name)
                            print(f"\n{phase_info} - EXÉCUTION: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False)}")

                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "iteration": iteration, "phase": phase_info})

                            formatted_result = self.format_tool_result(tool_result)
                            print(f"📤 Résultat:")
                            print("─" * 60)
                            print(formatted_result)
                            print("─" * 60)

                            tool_results_for_claude.append({
                                "role": "tool",
                                "tool_call_id": tool_use_id,
                                "content": formatted_result
                            })

                        messages.extend(tool_results_for_claude)
                        continue

                    else:
                        # Final response from Groq
                        final_response = response.choices[0].message.content or ""

                        processing_time = time.time() - start_time

                        print(f"\n✅ WORKFLOW TERMINÉ")
                        print(f"🔧 Outils utilisés: {len(tools_used)}")
                        print(f"⏱️ Temps: {processing_time:.2f}s")
                        print(f"🎯 Phases couvertes: {self.get_phases_used(tools_used)}")
                        print("=" * 80)

                        return {
                            "response": final_response,
                            "tools_used": tools_used,
                            "iterations": iteration,
                            "processing_time": processing_time,
                            "provider": f"groq_{self.model}",
                            "phases_used": self.get_phases_used(tools_used)
                        }

                elif response.stop_reason == "tool_use":
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content
                    }
                    messages.append(assistant_message)

                    tool_results_for_claude = []

                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_use_id = content_block.id

                            # Show which phase this tool belongs to
                            phase_info = self.get_tool_phase(tool_name)
                            print(f"\n{phase_info} - EXÉCUTION: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False)}")

                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "iteration": iteration, "phase": phase_info})

                            formatted_result = self.format_tool_result(tool_result)
                            print(f"📤 Résultat:")
                            print("─" * 60)
                            print(formatted_result)
                            print("─" * 60)

                            tool_results_for_claude.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": formatted_result
                            })

                    messages.append({
                        "role": "user",
                        "content": tool_results_for_claude
                    })

                    continue

                else:
                    # Final response
                    final_response = ""
                    for content_block in response.content:
                        if content_block.type == "text":
                            final_response += content_block.text

                    processing_time = time.time() - start_time

                    print(f"\n✅ WORKFLOW TERMINÉ")
                    print(f"🔧 Outils utilisés: {len(tools_used)}")
                    print(f"⏱️ Temps: {processing_time:.2f}s")
                    print(f"🎯 Phases couvertes: {self.get_phases_used(tools_used)}")
                    print("=" * 80)

                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "iterations": iteration,
                        "processing_time": processing_time,
                        "provider": f"anthropic_{self.model}",
                        "phases_used": self.get_phases_used(tools_used)
                    }

            except Exception as e:
                logger.error(f"❌ Error: {e}")
                return {
                    "response": f"Erreur: {str(e)}",
                    "tools_used": tools_used,
                    "error": str(e)
                }

        return {
            "response": "Limite d'itérations atteinte.",
            "tools_used": tools_used,
            "warning": "Max iterations reached"
        }

    def get_tool_phase(self, tool_name: str) -> str:
        """Get the phase emoji and name for a tool."""
        if tool_name.startswith("find_"):
            return "🏗️ PHASE 1"
        elif tool_name in ["compare_results", "check_connections"]:
            return "🔍 PHASE 2"
        elif "reference" in tool_name or "amendment" in tool_name:
            return "🕸️ PHASE 3"
        elif tool_name in ["verify_still_valid", "rank_by_importance", "create_final_map"]:
            return "🏆 PHASE 4"
        elif tool_name == "basic_document_search":
            return "🎁 BONUS"
        else:
            return "❓ UNKNOWN"

    def get_phases_used(self, tools_used: List[Dict]) -> List[str]:
        """Get unique phases used in the workflow."""
        phases = set()
        for tool in tools_used:
            phase = tool.get("phase", "❓ UNKNOWN")
            phases.add(phase)
        return sorted(list(phases))


async def test_legal_workflow():
    """Test the Luxembourg Legal Intelligence workflow system."""
    client = LegalIntelligenceClient()

    print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - WORKFLOW EDITION")
    print("=" * 80)
    print("🎯 13 Specialized Workflow Tools organized in 4 phases")
    print("🏗️ Phase 1: Discovery (4 tools) - Find big laws")
    print("🔍 Phase 2: Analysis (2 tools) - Check results") 
    print("🕸️ Phase 3: Relationships (3 tools) - Build family tree")
    print("🏆 Phase 4: Final (3 tools) - Complete picture")
    print("🎁 Bonus: Simple search (1 tool)")
    print("⚡ Smart workflow strategy with phase-based progression")
    print(f"🤖 AI Model: {client.model_provider.upper()} - {client.model}")
    print("=" * 80)

    test_question = "Quelles sont les lois fondamentales pour créer une SARL au Luxembourg ?"

    print(f"\n🧪 TEST DU WORKFLOW LÉGAL COMPLET")
    print(f"📝 Question: {test_question}")

    try:
        result = await client.chat(test_question)

        print(f"\n📋 RÉSULTATS DU WORKFLOW:")
        print(f"✅ Réponse: {len(result['response'])} caractères")
        print(f"🔧 Outils: {len(result.get('tools_used', []))}")
        print(f"⏱️ Temps: {result.get('processing_time', 0):.2f}s")
        print(f"🎯 Phases: {', '.join(result.get('phases_used', []))}")

        print(f"\n📄 RÉPONSE COMPLÈTE:")
        print("=" * 80)
        print(result['response'])
        print("=" * 80)

        # Show workflow details
        if result.get('tools_used'):
            print(f"\n🔧 WORKFLOW EXÉCUTÉ:")
            phases = {}
            for tool in result['tools_used']:
                phase = tool.get('phase', '❓ UNKNOWN')
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(f"{tool['name']} (iter {tool['iteration']})")
            
            for phase, tools in phases.items():
                print(f"   {phase}:")
                for tool in tools:
                    print(f"      • {tool}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_legal_workflow())