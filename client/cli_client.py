"""
CLI Client for Luxembourg Legal Intelligence MCP Server
Interactive tool selection and execution system
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import logging
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from dotenv import load_dotenv
import sys

load_dotenv()
logger = logging.getLogger(__name__)


class LegalIntelligenceCLI:
    """CLI Client for Luxembourg Legal Intelligence tools."""

    def __init__(self):
        # MCP Server configuration
        self.mcp_server_url = "http://localhost:8080/mcp"
        self.available_tools = []
        self._tools_initialized = False

        # Store previous results for analysis tools
        self.previous_results = []
        self.result_history = {}

        # Tool organization
        self.tool_phases = {
            "🏗️ PHASE 1 - DISCOVERY": [
                "find_most_cited_laws",
                "find_most_changed_laws",
                "find_newest_active_laws",
                "find_highest_authority_laws"
            ],
            "🔍 PHASE 2 - ANALYSIS": [
                "compare_results",
                "check_connections"
            ],
            "🕸️ PHASE 3 - RELATIONSHIPS": [
                "find_what_law_references",
                "find_what_references_law",
                "find_amendment_chain"
            ],
            "🏆 PHASE 4 - FINAL": [
                "verify_still_valid",
                "rank_by_importance",
                "create_final_map"
            ],
            "🎁 BONUS": [
                "basic_document_search",
                "extract_content"
            ]
        }

    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return

        print("🔧 Connecting to MCP server...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                self.available_tools = {tool.name: tool for tool in tools}

            self._tools_initialized = True
            print(f"✅ Connected! {len(self.available_tools)} tools available")

        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            print(f"💡 Make sure your server is running on {self.mcp_server_url}")
            sys.exit(1)

    async def call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool."""
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, tool_input)
                return {"success": True, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def display_tools_menu(self):
        """Display organized tools menu."""
        print("\n" + "="*80)
        print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - TOOL SELECTOR")
        print("="*80)

        tool_index = 1
        tool_map = {}

        for phase, tool_names in self.tool_phases.items():
            print(f"\n{phase}:")
            for tool_name in tool_names:
                if tool_name in self.available_tools:
                    tool = self.available_tools[tool_name]
                    print(f"  {tool_index:2d}. {tool_name}")
                    print(f"      📝 {tool.description}")
                    tool_map[tool_index] = tool_name
                    tool_index += 1

        print(f"\n🔧 SPECIAL OPTIONS:")
        print(f"  {tool_index}. list_all_tools - Show detailed tool information")
        tool_map[tool_index] = "list_all_tools"
        tool_index += 1

        print(f"  {tool_index}. quit - Exit CLI")
        tool_map[tool_index] = "quit"

        print(f"\n  0. Show this menu again")

        return tool_map

    def display_tool_details(self, tool_name: str):
        """Display detailed information about a tool."""
        if tool_name not in self.available_tools:
            print(f"❌ Tool '{tool_name}' not found")
            return

        tool = self.available_tools[tool_name]

        print(f"\n📋 TOOL DETAILS: {tool_name}")
        print("="*60)
        print(f"📝 Description: {tool.description}")

        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            print(f"\n📥 INPUT PARAMETERS:")
            schema = tool.inputSchema

            if 'properties' in schema:
                for param_name, param_info in schema['properties'].items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')
                    required = param_name in schema.get('required', [])
                    required_mark = " ⭐ REQUIRED" if required else ""

                    print(f"  • {param_name} ({param_type}){required_mark}")
                    print(f"    {param_desc}")

                    # Show examples for specific types
                    if param_type == 'array' and 'items' in param_info:
                        items_type = param_info['items'].get('type', 'unknown')
                        print(f"    📋 Array of {items_type}")
                        if items_type == 'string':
                            print(f"    💡 Example: [\"société\", \"commercial\"]")
                    elif param_type == 'string':
                        if 'uri' in param_name.lower():
                            print(f"    💡 Example: http://data.legilux.public.lu/resource/...</")
                        else:
                            print(f"    💡 Example: \"société\"")
                    elif param_type == 'integer':
                        print(f"    💡 Example: 10")

        print("="*60)

    def get_tool_input(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Interactive input collection for a tool."""
        if tool_name not in self.available_tools:
            print(f"❌ Tool '{tool_name}' not found")
            return None

        tool = self.available_tools[tool_name]

        print(f"\n📥 COLLECTING INPUT FOR: {tool_name}")
        print("="*50)

        if not hasattr(tool, 'inputSchema') or not tool.inputSchema:
            print("ℹ️  This tool requires no input parameters")
            return {}

        schema = tool.inputSchema
        tool_input = {}

        if 'properties' not in schema:
            print("ℹ️  This tool requires no input parameters")
            return {}

        for param_name, param_info in schema['properties'].items():
            param_type = param_info.get('type', 'unknown')
            param_desc = param_info.get('description', 'No description')
            required = param_name in schema.get('required', [])

            print(f"\n📋 Parameter: {param_name} ({param_type})")
            print(f"    {param_desc}")

            if required:
                print("    ⭐ REQUIRED")

            # Special handling for analysis tools
            if tool_name == "compare_results" and param_name == "result_sets":
                special_value = self.handle_compare_results_parameter()
                if special_value is not None:
                    tool_input[param_name] = special_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None
                continue
            elif tool_name == "check_connections" and param_name == "document_uris":
                special_value = self.handle_document_uris_parameter()
                if special_value is not None:
                    tool_input[param_name] = special_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None
                continue
            elif tool_name == "verify_still_valid" and param_name == "document_uris":
                special_value = self.handle_document_uris_parameter()
                if special_value is not None:
                    tool_input[param_name] = special_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None
                continue
            elif tool_name == "rank_by_importance" and param_name == "laws_data":
                special_value = self.handle_laws_data_parameter()
                if special_value is not None:
                    tool_input[param_name] = special_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None
                continue
            elif tool_name == "create_final_map" and param_name in ["ranked_laws", "connections"]:
                if param_name == "ranked_laws":
                    special_value = self.handle_ranked_laws_parameter()
                else:
                    special_value = self.handle_connections_parameter()
                if special_value is not None:
                    tool_input[param_name] = special_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None
                continue

            # Regular parameter handling
            if param_type == 'array':
                items_type = param_info.get('items', {}).get('type', 'string')
                if items_type == 'string':
                    print("    💡 Enter comma-separated values")
                    print("    💡 Example: société, commercial, SARL")

                    user_input = input(f"    ➤ {param_name}: ").strip()
                    if user_input:
                        # Split by comma and clean up
                        tool_input[param_name] = [item.strip().strip('"').strip("'") for item in user_input.split(',') if item.strip()]
                    elif required:
                        print("    ❌ Required parameter cannot be empty!")
                        return None

            elif param_type == 'string':
                if 'uri' in param_name.lower():
                    print("    💡 Enter a complete URI")
                    print("    💡 Example: http://data.legilux.public.lu/resource/eli/etat/leg/loi/2016/08/10/n13")
                else:
                    print("    💡 Enter a text value")

                user_input = input(f"    ➤ {param_name}: ").strip().strip('"').strip("'")
                if user_input:
                    tool_input[param_name] = user_input
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None

            elif param_type == 'integer':
                print("    💡 Enter a number")
                default_value = param_info.get('default', 10 if 'limit' in param_name else None)
                prompt = f"    ➤ {param_name}"
                if default_value is not None:
                    prompt += f" (default: {default_value})"
                prompt += ": "

                user_input = input(prompt).strip()
                if user_input:
                    try:
                        tool_input[param_name] = int(user_input)
                    except ValueError:
                        print("    ❌ Invalid number format!")
                        return None
                elif default_value is not None:
                    tool_input[param_name] = default_value
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None

            elif param_type == 'object':
                print("    💡 This parameter requires complex object input")
                print("    💡 Enter JSON format or press Enter to skip")
                user_input = input(f"    ➤ {param_name} (JSON): ").strip()
                if user_input:
                    try:
                        tool_input[param_name] = json.loads(user_input)
                    except json.JSONDecodeError:
                        print("    ❌ Invalid JSON format!")
                        return None
                elif required:
                    print("    ❌ Required parameter cannot be empty!")
                    return None

        print(f"\n✅ Input collected for {tool_name}:")
        print(json.dumps(tool_input, indent=2, ensure_ascii=False))

        confirm = input("\n🤔 Execute with these parameters? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            return tool_input
        else:
            print("❌ Execution cancelled")
            return None

    def handle_compare_results_parameter(self) -> Optional[List[Dict]]:
        """Handle the result_sets parameter for compare_results tool."""
        print("    🔍 Auto-detecting previous discovery results...")

        # Show available previous results
        discovery_results = [r for r in self.previous_results if r.get('tool_name') in self.tool_phases["🏗️ PHASE 1 - DISCOVERY"]]

        if not discovery_results:
            print("    ❌ No discovery results available!")
            print("    💡 Run discovery tools first (find_most_cited_laws, find_most_changed_laws, etc.)")
            manual = input("    ➤ Enter JSON manually? (y/N): ").strip().lower()
            if manual == 'y':
                json_input = input("    ➤ Enter JSON array: ").strip()
                try:
                    return json.loads(json_input)
                except json.JSONDecodeError:
                    print("    ❌ Invalid JSON format!")
            return None

        print(f"    📋 Found {len(discovery_results)} discovery results:")
        for i, result in enumerate(discovery_results, 1):
            print(f"      {i}. {result['tool_name']} - {result.get('summary', 'No summary')}")

        choice = input("    ➤ Use all results? (Y/n/select): ").strip().lower()

        if choice in ['', 'y', 'yes']:
            # Use all discovery results
            result_sets = []
            for result in discovery_results:
                if result.get('parsed_data'):
                    result_sets.append(result['parsed_data'])
            return result_sets

        elif choice in ['s', 'select']:
            selection = input("    ➤ Select results (comma-separated numbers): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                result_sets = []
                for i in indices:
                    if 0 <= i < len(discovery_results) and discovery_results[i].get('parsed_data'):
                        result_sets.append(discovery_results[i]['parsed_data'])
                return result_sets
            except ValueError:
                print("    ❌ Invalid selection format!")
                return None
        else:
            return None

    def handle_document_uris_parameter(self) -> Optional[List[str]]:
        """Handle document_uris parameter for connection/validation tools."""
        print("    🔗 Auto-extracting URIs from previous results...")

        # Look for URIs in previous results
        all_uris = set()
        for result in self.previous_results:
            if result.get('parsed_data') and isinstance(result['parsed_data'], dict):
                data = result['parsed_data']
                if 'laws' in data:
                    for law in data['laws']:
                        for key in ['cited_doc', 'modified_doc', 'doc', 'uri']:
                            if key in law:
                                all_uris.add(law[key])
                                break

        if not all_uris:
            print("    ❌ No document URIs found in previous results!")
            manual = input("    ➤ Enter URIs manually? (y/N): ").strip().lower()
            if manual == 'y':
                manual_input = input("    ➤ Enter URIs (comma-separated): ").strip()
                if manual_input:
                    return [uri.strip() for uri in manual_input.split(',') if uri.strip()]
            return None

        uris_list = list(all_uris)[:20]  # Limit to 20 for performance
        print(f"    📋 Found {len(all_uris)} unique URIs, using top {len(uris_list)}")

        confirm = input(f"    ➤ Use these {len(uris_list)} URIs? (Y/n): ").strip().lower()
        if confirm in ['', 'y', 'yes']:
            return uris_list
        else:
            return None

    def handle_laws_data_parameter(self) -> Optional[Dict]:
        """Handle laws_data parameter for rank_by_importance tool."""
        print("    🏆 Auto-detecting comparison and validation results...")

        # Look for comparison results and validation results
        comparison_result = None
        validation_result = None

        for result in self.previous_results:
            if result.get('tool_name') == 'compare_results' and result.get('parsed_data'):
                comparison_result = result['parsed_data']
            elif result.get('tool_name') == 'verify_still_valid' and result.get('parsed_data'):
                validation_result = result['parsed_data']

        if not comparison_result:
            print("    ❌ No comparison results found!")
            print("    💡 Run 'compare_results' tool first")
            return None

        laws_data = {"ranked_laws": comparison_result.get("ranked_laws", [])}

        if validation_result:
            laws_data["law_statuses"] = validation_result.get("law_statuses", [])
            print("    ✅ Using comparison results + validation results")
        else:
            print("    ⚠️  Using comparison results only (no validation data)")

        return laws_data

    def handle_ranked_laws_parameter(self) -> Optional[List[Dict]]:
        """Handle ranked_laws parameter for create_final_map tool."""
        print("    🗺️ Auto-detecting ranking results...")

        for result in self.previous_results:
            if result.get('tool_name') == 'rank_by_importance' and result.get('parsed_data'):
                ranked_laws = result['parsed_data'].get("ranked_laws", [])
                print(f"    ✅ Found {len(ranked_laws)} ranked laws")
                return ranked_laws

        print("    ❌ No ranking results found! Run 'rank_by_importance' tool first")
        return None

    def handle_connections_parameter(self) -> Optional[List[Dict]]:
        """Handle connections parameter for create_final_map tool."""
        print("    🗺️ Auto-detecting connection results...")

        for result in self.previous_results:
            if result.get('tool_name') == 'check_connections' and result.get('parsed_data'):
                connections = result['parsed_data'].get("connections", [])
                print(f"    ✅ Found {len(connections)} connections")
                return connections

        print("    ❌ No connection results found! Run 'check_connections' tool first")
        return None

    def format_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool execution result."""
        if not result["success"]:
            return f"❌ ERROR: {result['error']}"

        data = result["result"]

        # Handle MCP TextContent objects
        if isinstance(data, list) and len(data) > 0:
            # Extract text from TextContent objects
            if hasattr(data[0], 'text'):
                try:
                    # Parse the JSON text from the first TextContent object
                    json_text = data[0].text
                    data = json.loads(json_text)
                except (json.JSONDecodeError, AttributeError) as e:
                    return f"❌ Failed to parse result JSON: {e}\nRaw data: {data}"

        # Pretty print the JSON result
        try:
            formatted = json.dumps(data, indent=2, ensure_ascii=False)

            # Add summary information if available
            summary_lines = []

            if isinstance(data, dict):
                if data.get("success"):
                    summary_lines.append("✅ Operation successful")

                # Extract key metrics
                if "total_found" in data:
                    summary_lines.append(f"📊 Found: {data['total_found']} items")

                if "keywords" in data:
                    summary_lines.append(f"🔍 Keywords: {', '.join(data['keywords'])}")

                if "method" in data:
                    summary_lines.append(f"📋 Method: {data['method']}")

                if "statistics" in data:
                    stats = data["statistics"]
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            summary_lines.append(f"📈 {key.replace('_', ' ').title()}: {value}")

                # Show number of items in main result arrays
                if "laws" in data and isinstance(data["laws"], list):
                    summary_lines.append(f"📋 Laws returned: {len(data['laws'])}")

                if "documents" in data and isinstance(data["documents"], list):
                    summary_lines.append(f"📄 Documents returned: {len(data['documents'])}")

                if "connections" in data and isinstance(data["connections"], list):
                    summary_lines.append(f"🔗 Connections found: {len(data['connections'])}")

                if "references" in data and isinstance(data["references"], list):
                    summary_lines.append(f"📚 References found: {len(data['references'])}")

                if "citing_laws" in data and isinstance(data["citing_laws"], list):
                    summary_lines.append(f"📜 Citing laws found: {len(data['citing_laws'])}")

                if "amendments" in data and isinstance(data["amendments"], list):
                    summary_lines.append(f"📝 Amendments found: {len(data['amendments'])}")

            if summary_lines:
                return "\n".join(summary_lines) + "\n\n" + "="*60 + "\nFULL RESULT:\n" + "="*60 + "\n" + formatted
            else:
                return formatted

        except Exception as e:
            return f"Result formatting error: {e}\nRaw result: {str(data)}"

    async def run_cli(self):
        """Main CLI loop."""
        print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE CLI")
        print("="*80)
        print("Interactive tool execution system")
        print("Each tool can be run independently with custom parameters")
        print("="*80)

        await self.initialize_tools()

        tool_map = self.display_tools_menu()

        while True:
            try:
                print(f"\n📋 Available tools: {len(self.available_tools)}")
                choice = input("🎯 Select tool number (0 for menu): ").strip()

                if not choice or choice == "0":
                    tool_map = self.display_tools_menu()
                    continue

                try:
                    choice_num = int(choice)
                except ValueError:
                    print("❌ Please enter a valid number")
                    continue

                if choice_num not in tool_map:
                    print("❌ Invalid tool number")
                    continue

                selected_tool = tool_map[choice_num]

                if selected_tool == "quit":
                    print("👋 Goodbye!")
                    break

                elif selected_tool == "list_all_tools":
                    print("\n📋 DETAILED TOOL INFORMATION:")
                    for phase, tool_names in self.tool_phases.items():
                        print(f"\n{phase}:")
                        for tool_name in tool_names:
                            if tool_name in self.available_tools:
                                self.display_tool_details(tool_name)
                    continue

                # Execute selected tool
                print(f"\n🔧 SELECTED TOOL: {selected_tool}")

                # Show tool details
                self.display_tool_details(selected_tool)

                # Get input parameters
                tool_input = self.get_tool_input(selected_tool)
                if tool_input is None:
                    continue

                # Execute tool
                print(f"\n⚡ Executing {selected_tool}...")
                print("="*50)

                result = await self.call_tool(selected_tool, tool_input)

                # Store result for future use
                if result["success"] and "result" in result:
                    parsed_data = None
                    try:
                        # Extract and parse JSON from TextContent
                        raw_result = result["result"]
                        if isinstance(raw_result, list) and len(raw_result) > 0:
                            if hasattr(raw_result[0], 'text'):
                                parsed_data = json.loads(raw_result[0].text)
                        elif isinstance(raw_result, dict):
                            parsed_data = raw_result
                    except:
                        pass

                    # Create summary for display
                    summary = f"Success"
                    if parsed_data and isinstance(parsed_data, dict):
                        if "total_found" in parsed_data:
                            summary = f"{parsed_data['total_found']} items found"
                        elif "laws" in parsed_data:
                            summary = f"{len(parsed_data['laws'])} laws"
                        elif "connections" in parsed_data:
                            summary = f"{len(parsed_data['connections'])} connections"

                    self.previous_results.append({
                        "tool_name": selected_tool,
                        "input": tool_input,
                        "result": result,
                        "parsed_data": parsed_data,
                        "summary": summary,
                        "timestamp": asyncio.get_event_loop().time()
                    })

                # Display results
                print(f"\n📤 RESULTS FOR: {selected_tool}")
                print("="*60)
                formatted_result = self.format_result(selected_tool, result)
                print(formatted_result)
                print("="*60)

                # Show result history
                if len(self.previous_results) > 0:
                    print(f"\n📚 RESULT HISTORY ({len(self.previous_results)} results stored):")
                    for i, prev_result in enumerate(self.previous_results[-5:], len(self.previous_results)-4):  # Show last 5
                        if i > 0:
                            print(f"  {i}. {prev_result['tool_name']} - {prev_result['summary']}")

                # Ask if user wants to save results
                save = input("\n💾 Save results to file? (y/N): ").strip().lower()
                if save in ['y', 'yes']:
                    filename = f"{selected_tool}_result_{int(asyncio.get_event_loop().time())}.json"
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump({
                                "tool_name": selected_tool,
                                "input": tool_input,
                                "result": result,
                                "timestamp": asyncio.get_event_loop().time()
                            }, f, indent=2, ensure_ascii=False)
                        print(f"✅ Results saved to: {filename}")
                    except Exception as e:
                        print(f"❌ Failed to save file: {e}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                continue


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Quick tool execution mode
        tool_name = sys.argv[1]
        cli = LegalIntelligenceCLI()
        await cli.initialize_tools()

        if tool_name in cli.available_tools:
            cli.display_tool_details(tool_name)
            tool_input = cli.get_tool_input(tool_name)
            if tool_input is not None:
                result = await cli.call_tool(tool_name, tool_input)
                print(f"\n📤 RESULTS:")
                print("="*40)
                print(cli.format_result(tool_name, result))
        else:
            print(f"❌ Tool '{tool_name}' not found")
            print(f"Available tools: {', '.join(cli.available_tools.keys())}")
    else:
        # Interactive CLI mode
        cli = LegalIntelligenceCLI()
        await cli.run_cli()


if __name__ == "__main__":
    asyncio.run(main())
