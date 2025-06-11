#!/usr/bin/env python3
"""
CLI Client for Luxembourg Legal Intelligence MCP Server
Independent tool testing with example inputs
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


class IndependentToolClient:
    """Independent tool testing client for Luxembourg Legal Intelligence."""

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

        # Example inputs for each tool
        self.tool_examples = {
            "find_most_cited_laws": {
                "description": "Trouve les lois les plus citées",
                "example": {"keywords": ["SARL"], "limit": 5}
            },
            "find_most_changed_laws": {
                "description": "Trouve les lois les plus modifiées",
                "example": {"keywords": ["commercial"], "limit": 5}
            },
            "find_newest_active_laws": {
                "description": "Trouve les lois récentes actives",
                "example": {"keywords": ["société"], "limit": 5}
            },
            "find_highest_authority_laws": {
                "description": "Trouve les documents LOI/CODE",
                "example": {"keywords": ["travail"], "limit": 5}
            },
            "basic_document_search": {
                "description": "Recherche simple par mots-clés",
                "example": {"keywords": ["fiscalité"], "limit": 10}
            },
            "compare_results": {
                "description": "Compare plusieurs résultats de recherche",
                "example": {
                    "result_sets": [
                        {"laws": [{"uri": "test", "title": "Test Law"}], "method": "citation", "success": True},
                        {"laws": [{"uri": "test2", "title": "Test Law 2"}], "method": "modification", "success": True}
                    ]
                }
            },
            "check_connections": {
                "description": "Vérifie les connexions entre lois",
                "example": {
                    "document_uris": [
                        "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo"
                    ]
                }
            },
            "find_what_law_references": {
                "description": "Ce que cette loi référence",
                "example": {
                    "document_uri": "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo",
                    "limit": 10
                }
            },
            "find_what_references_law": {
                "description": "Ce qui référence cette loi",
                "example": {
                    "document_uri": "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo",
                    "limit": 10
                }
            },
            "find_amendment_chain": {
                "description": "Historique des modifications",
                "example": {
                    "document_uri": "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo",
                    "limit": 10
                }
            },
            "verify_still_valid": {
                "description": "Vérifie la validité des lois",
                "example": {
                    "document_uris": [
                        "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo"
                    ]
                }
            },
            "rank_by_importance": {
                "description": "Classe les lois par importance",
                "example": {
                    "laws_data": {
                        "ranked_laws": [
                            {"uri": "test", "title": "Test Law", "total_score": 100}
                        ],
                        "law_statuses": [
                            {"uri": "test", "legal_status": "active", "is_valid": True}
                        ]
                    }
                }
            },
            "create_final_map": {
                "description": "Crée la carte légale finale",
                "example": {
                    "ranked_laws": [
                        {"uri": "test", "title": "Test Law", "final_importance_score": 100}
                    ],
                    "connections": [
                        {"from_uri": "test1", "to_uri": "test2", "relationship": "cites"}
                    ]
                }
            },
            "extract_content": {
                "description": "Extrait le contenu des documents",
                "example": {
                    "document_uris": [
                        "http://data.legilux.public.lu/eli/etat/leg/constitution/1868/10/17/n1/jo"
                    ],
                    "max_documents": 2,
                    "prefer_html": True
                }
            }
        }

    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return

        logger.info("🔧 Initializing all available tools...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()

                self.available_tools = []
                tools_found = []

                for tool in tools:
                    if tool.name in self.tool_examples:
                        claude_tool = {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        }
                        self.available_tools.append(claude_tool)
                        tools_found.append(tool.name)

            self._tools_initialized = True
            logger.info(f"✅ Initialized {len(self.available_tools)} tools: {tools_found}")

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

    async def test_single_tool(self, tool_name: str, custom_input: Optional[Dict] = None) -> Dict[str, Any]:
        """Test a single tool with example or custom input."""
        await self.initialize_tools()

        if tool_name not in self.tool_examples:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in available tools",
                "available_tools": list(self.tool_examples.keys())
            }

        # Use custom input or example
        tool_input = custom_input if custom_input else self.tool_examples[tool_name]["example"]

        print(f"\n🔧 TESTING TOOL: {tool_name}")
        print(f"📝 Description: {self.tool_examples[tool_name]['description']}")
        print(f"📥 Input: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")
        print("=" * 60)

        start_time = time.time()

        # Execute the tool
        result = await self.call_mcp_tool(tool_name, tool_input)

        execution_time = time.time() - start_time

        if result["success"]:
            print(f"✅ SUCCESS ({execution_time:.2f}s)")
            print("📤 Result:")
            print("─" * 40)

            # Handle TextContent serialization
            try:
                formatted_result = json.dumps(result["result"], ensure_ascii=False, indent=2)
                print(formatted_result)
            except TypeError:
                print(str(result["result"]))

            print("─" * 40)
        else:
            print(f"❌ FAILED ({execution_time:.2f}s)")
            print(f"Error: {result['error']}")

        return {
            "success": result["success"],
            "tool_name": tool_name,
            "execution_time": execution_time,
            "result": result.get("result"),
            "error": result.get("error")
        }

    async def ai_tool_usage(self, question: str) -> Dict[str, Any]:
        """Let AI choose and use tools independently."""
        await self.initialize_tools()

        # Independent tool usage prompt
        system_prompt = """Tu es un expert juridique luxembourgeois avec accès à des outils MCP indépendants.

🔧 OUTILS DISPONIBLES (utilisation indépendante):

📚 DÉCOUVERTE:
- find_most_cited_laws(keywords, limit) - Lois les plus citées
- find_most_changed_laws(keywords, limit) - Lois les plus modifiées
- find_newest_active_laws(keywords, limit) - Lois récentes actives
- find_highest_authority_laws(keywords, limit) - Documents LOI/CODE
- basic_document_search(keywords, limit) - Recherche simple

🔍 ANALYSE:
- compare_results(result_sets) - Compare plusieurs résultats
- check_connections(document_uris) - Connexions entre lois

🕸️ RELATIONS:
- find_what_law_references(document_uri, limit) - Ce que la loi référence
- find_what_references_law(document_uri, limit) - Ce qui référence la loi
- find_amendment_chain(document_uri, limit) - Historique modifications

🏆 FINALISATION:
- verify_still_valid(document_uris) - Vérifie validité
- rank_by_importance(laws_data) - Classe par importance
- create_final_map(ranked_laws, connections) - Carte finale

📄 CONTENU:
- extract_content(document_uris, max_documents, prefer_html) - Extrait texte

🎯 STRATÉGIE: Choisis SEULEMENT les outils nécessaires pour répondre à cette question spécifique. Sois efficace!

Réponds en français en utilisant UNIQUEMENT les données des outils MCP."""

        messages = [{"role": "user", "content": question}]
        tools_used = []
        max_iterations = 15
        iteration = 0

        print(f"\n🤖 AI TOOL USAGE")
        print(f"📝 Question: {question}")
        print("=" * 80)

        start_time = time.time()

        while iteration < max_iterations:
            iteration += 1

            try:
                if self.is_groq:
                    groq_messages = [{"role": "system", "content": system_prompt}] + messages
                    request_params = {
                        "model": self.model,
                        "max_tokens": 4000,
                        "temperature": 0.3,
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

                            print(f"\n🔧 AI EXECUTING: {tool_name}")
                            print(f"📥 Parameters: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "input": tool_input, "iteration": iteration})

                            if tool_result["success"]:
                                print(f"✅ Success: {tool_name}")
                            else:
                                print(f"❌ Error: {tool_result['error']}")

                            try:
                                formatted_result = json.dumps(tool_result["result"], ensure_ascii=False, indent=2)
                            except TypeError:
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
                        break

                else:  # Anthropic
                    request_params = {
                        "model": self.model,
                        "max_tokens": 4000,
                        "temperature": 0.3,
                        "system": system_prompt,
                        "messages": messages
                    }

                    if self.available_tools:
                        request_params["tools"] = self.available_tools

                    response = await self.client.messages.create(**request_params)

                    if response.stop_reason == "tool_use":
                        assistant_message = {"role": "assistant", "content": response.content}
                        messages.append(assistant_message)

                        tool_results = []
                        for content_block in response.content:
                            if content_block.type == "tool_use":
                                tool_name = content_block.name
                                tool_input = content_block.input

                                print(f"\n🔧 AI EXECUTING: {tool_name}")
                                print(f"📥 Parameters: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

                                tool_result = await self.call_mcp_tool(tool_name, tool_input)
                                tools_used.append({"name": tool_name, "input": tool_input, "iteration": iteration})

                                if tool_result["success"]:
                                    print(f"✅ Success: {tool_name}")
                                else:
                                    print(f"❌ Error: {tool_result['error']}")

                                try:
                                    formatted_result = json.dumps(tool_result["result"], ensure_ascii=False, indent=2)
                                except TypeError:
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
                        break

            except Exception as e:
                logger.error(f"❌ Error in iteration {iteration}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tools_used": tools_used
                }

        processing_time = time.time() - start_time

        print(f"\n✅ AI WORKFLOW COMPLETED")
        print(f"🔧 Tools used: {len(tools_used)}")
        print(f"⏱️ Time: {processing_time:.2f}s")
        print("=" * 80)

        return {
            "success": True,
            "response": final_response,
            "tools_used": tools_used,
            "processing_time": processing_time,
            "iterations": iteration
        }

    def show_tool_options(self):
        """Show available tool options for testing."""
        print("\n🔧 OUTILS DISPONIBLES POUR TEST:")
        print("=" * 60)

        categories = {
            "📚 DÉCOUVERTE": [
                "find_most_cited_laws", "find_most_changed_laws",
                "find_newest_active_laws", "find_highest_authority_laws",
                "basic_document_search"
            ],
            "🔍 ANALYSE": [
                "compare_results", "check_connections"
            ],
            "🕸️ RELATIONS": [
                "find_what_law_references", "find_what_references_law",
                "find_amendment_chain"
            ],
            "🏆 FINALISATION": [
                "verify_still_valid", "rank_by_importance", "create_final_map"
            ],
            "📄 CONTENU": [
                "extract_content"
            ]
        }

        for category, tools in categories.items():
            print(f"\n{category}:")
            for tool in tools:
                if tool in self.tool_examples:
                    desc = self.tool_examples[tool]["description"]
                    print(f"  • {tool} - {desc}")

        print("\n🤖 IA (Special option):")
        print("  • ai - Let AI choose tools automatically")
        print("=" * 60)


async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Luxembourg Legal Intelligence - Independent Tool Testing")
    parser.add_argument("--tool", "-t", help="Tool name to test")
    parser.add_argument("--question", "-q", help="Question for AI tool usage")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    client = IndependentToolClient()

    print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - INDEPENDENT TOOL TESTING")
    print("=" * 70)
    print(f"🤖 Model: {client.model_provider.upper()} - {client.model}")
    print("=" * 70)

    if args.interactive or not (args.tool or args.question):
        # Interactive mode
        while True:
            try:
                client.show_tool_options()

                # Get tool choice
                tool_choice = input("\n🔧 Choose tool to test (or 'ai' for AI usage): ").strip().lower()

                if not tool_choice:
                    print("❌ Tool choice required!")
                    continue

                if tool_choice == "ai":
                    # AI tool usage mode
                    question = input("\n📝 Your legal question: ").strip()
                    if not question:
                        print("❌ Question required for AI mode!")
                        continue

                    result = await client.ai_tool_usage(question)

                    if result["success"]:
                        print(f"\n📄 AI RESPONSE:")
                        print("=" * 80)
                        print(result["response"])
                        print("=" * 80)

                        print(f"\n📊 SUMMARY:")
                        print(f"✅ Tools used: {len(result['tools_used'])}")
                        print(f"⏱️ Time: {result['processing_time']:.2f}s")
                        print(f"🔄 Iterations: {result['iterations']}")

                        if result['tools_used']:
                            print(f"\n🔧 TOOLS EXECUTED:")
                            for i, tool in enumerate(result['tools_used'], 1):
                                print(f"  {i}. {tool['name']} (iteration {tool['iteration']})")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}")

                elif tool_choice in client.tool_examples:
                    # Single tool testing
                    use_custom = input(f"\n🎛️ Use custom input? (y/N): ").strip().lower()
                    custom_input = None

                    if use_custom == 'y':
                        print(f"📋 Example input: {json.dumps(client.tool_examples[tool_choice]['example'], indent=2)}")
                        custom_json = input("📝 Enter custom JSON input: ").strip()
                        try:
                            custom_input = json.loads(custom_json)
                        except json.JSONDecodeError:
                            print("❌ Invalid JSON, using example input instead")

                    result = await client.test_single_tool(tool_choice, custom_input)

                    print(f"\n📊 TEST SUMMARY:")
                    print(f"✅ Success: {result['success']}")
                    print(f"⏱️ Time: {result['execution_time']:.2f}s")

                else:
                    print(f"❌ Unknown tool: {tool_choice}")
                    print(f"Available tools: {list(client.tool_examples.keys()) + ['ai']}")
                    continue

                # Continue or exit
                continue_choice = input("\n🔄 Test another tool? (y/N): ").strip().lower()
                if continue_choice != 'y':
                    break

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
    else:
        # Direct execution mode
        if args.tool:
            if args.tool == "ai":
                if not args.question:
                    print("❌ Question required for AI mode!")
                    return
                result = await client.ai_tool_usage(args.question)
                if result["success"]:
                    print(result["response"])
                else:
                    print(f"❌ Error: {result.get('error')}")
            else:
                result = await client.test_single_tool(args.tool)
                print(f"Result: {result['success']}")
        elif args.question:
            result = await client.ai_tool_usage(args.question)
            if result["success"]:
                print(result["response"])
            else:
                print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
