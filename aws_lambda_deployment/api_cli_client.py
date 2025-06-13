#!/usr/bin/env python3
"""
API CLI Client for Luxembourg Legal Intelligence
Interactive tool selection and execution using the deployed Lambda API
"""

import os
import json
import sys
from typing import Dict, List, Any, Optional
import requests

def load_deployment_info():
    """Load API URL and key from deployment info."""
    # Fallback to environment variables if deployment_info.json is missing
    if os.path.exists("deployment_info.json"):
        with open("deployment_info.json", "r") as f:
            info = json.load(f)
            return info["api_url"], info["api_key"]
    else:
        print("❌ deployment_info.json not found!")
        print("💡 Run ./deploy_api_function.sh first to deploy the API")
        sys.exit(1)

class LegalIntelligenceAPICLI:
    """CLI Client for Luxembourg Legal Intelligence API."""

    def __init__(self):
        # Load API configuration
        self.api_url, self.api_key = load_deployment_info()
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Store available tools
        self.available_tools = {}
        self._tools_initialized = False

        # Tool organization - will be populated dynamically
        self.tool_phases = {}

    def initialize_tools(self):
        """Initialize tools by calling the API /tools endpoint."""
        if self._tools_initialized:
            return

        print("🔧 Connecting to API...")
        try:
            response = requests.get(
                f"{self.api_url}/tools",
                headers={"X-API-Key": self.api_key}
            )
            response.raise_for_status()
            
            tools_data = response.json()
            
            # Convert to the format expected by display functions
            for tool in tools_data.get("available_tools", []):
                tool_name = tool["name"]
                self.available_tools[tool_name] = tool

            # Organize tools dynamically based on their names/functionality
            self._organize_tools_dynamically()
            
            self._tools_initialized = True
            print(f"✅ Connected! {len(self.available_tools)} tools available")
            print(f"🌐 API URL: {self.api_url}")

        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            print(f"💡 Make sure the API is deployed and accessible")
            sys.exit(1)

    def _organize_tools_dynamically(self):
        """Organize tools into logical phases based on their names and descriptions."""
        discovery_tools = []
        search_tools = []
        analysis_tools = []
        other_tools = []
        
        for tool_name in self.available_tools.keys():
            # Categorize based on tool name patterns
            if any(keyword in tool_name.lower() for keyword in ['find_most', 'find_highest', 'find_newest', 'discover']):
                discovery_tools.append(tool_name)
            elif any(keyword in tool_name.lower() for keyword in ['search', 'query', 'lookup']):
                search_tools.append(tool_name)
            elif any(keyword in tool_name.lower() for keyword in ['analyze', 'compare', 'extract', 'summarize']):
                analysis_tools.append(tool_name)
            else:
                other_tools.append(tool_name)
        
        # Build phases dictionary
        self.tool_phases = {}
        
        if discovery_tools:
            self.tool_phases["🏗️ DISCOVERY TOOLS"] = discovery_tools
        
        if search_tools:
            self.tool_phases["🔍 SEARCH TOOLS"] = search_tools
            
        if analysis_tools:
            self.tool_phases["📊 ANALYSIS TOOLS"] = analysis_tools
            
        if other_tools:
            self.tool_phases["🔧 OTHER TOOLS"] = other_tools

    def call_tool_via_api(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool via the API."""
        try:
            response = requests.post(
                f"{self.api_url}/tool/{tool_name}",
                headers=self.headers,
                json=tool_input
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                error_data = response.json() if response.content else {"error": "Unknown error"}
                return {"success": False, "error": f"API Error {response.status_code}: {error_data.get('error', 'Unknown error')}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def display_tools_menu(self):
        """Display organized tools menu."""
        print("\n" + "="*80)
        print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - API CLIENT")
        print("="*80)
        print(f"🌐 Using API: {self.api_url}")

        tool_index = 1
        tool_map = {}

        for phase, tool_names in self.tool_phases.items():
            print(f"\n{phase}:")
            for tool_name in tool_names:
                if tool_name in self.available_tools:
                    tool = self.available_tools[tool_name]
                    print(f"  {tool_index:2d}. {tool_name}")
                    print(f"      📝 {tool.get('description', 'No description')}")
                    tool_map[tool_index] = tool_name
                    tool_index += 1

        print(f"\n🔧 SPECIAL OPTIONS:")
        print(f"  {tool_index}. list_all_tools - Show detailed tool information")
        tool_map[tool_index] = "list_all_tools"
        tool_index += 1

        print(f"  {tool_index}. test_api_health - Test API health")
        tool_map[tool_index] = "test_api_health"
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
        print(f"📝 Description: {tool.get('description', 'No description')}")

        if 'inputSchema' in tool and tool['inputSchema']:
            print(f"\n📥 INPUT PARAMETERS:")
            schema = tool['inputSchema']

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
                        print(f"    💡 Example: \"société\"")
                    elif param_type == 'integer':
                        default = param_info.get('default', 10)
                        print(f"    💡 Example: {default}")

        print("="*60)

    def get_tool_input(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Interactive input collection for a tool."""
        if tool_name not in self.available_tools:
            print(f"❌ Tool '{tool_name}' not found")
            return None

        tool = self.available_tools[tool_name]

        print(f"\n📥 COLLECTING INPUT FOR: {tool_name}")
        print("="*50)

        if 'inputSchema' not in tool or not tool['inputSchema']:
            print("ℹ️  This tool requires no input parameters")
            return {}

        schema = tool['inputSchema']
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

            # Handle different parameter types
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

    def test_api_health(self):
        """Test API health endpoint."""
        print(f"\n🔍 Testing API health...")
        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers={"X-API-Key": self.api_key}
            )
            response.raise_for_status()
            
            health_data = response.json()
            print(f"✅ Status: {health_data.get('status')}")
            print(f"🏗️  Architecture: {health_data.get('pattern')}")
            print(f"📡 MCP Server: {health_data.get('mcp_server')}")
            print(f"⏰ Timestamp: {health_data.get('timestamp')}")
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")

    def format_api_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format API call result for display."""
        if not result["success"]:
            return f"❌ ERROR: {result['error']}"

        # The API returns the full response, so we extract the actual tool result
        api_response = result["result"]
        
        print(f"\n📡 API RESPONSE:")
        print("="*60)
        print(f"🔧 Tool: {api_response.get('tool_name')}")
        print(f"✅ Success: {api_response.get('success')}")
        print(f"⏱️  Execution: {api_response.get('execution_time')}")
        
        tool_result = api_response.get("result", {})
        
        print(f"\n📄 TOOL RESULT:")
        print("="*60)
        
        # Format the actual MCP tool result
        try:
            formatted = json.dumps(tool_result, indent=2, ensure_ascii=False)
            
            # Add summary information if available
            summary_lines = []
            
            if isinstance(tool_result, dict):
                if tool_result.get("success"):
                    summary_lines.append("✅ Tool execution successful")
                
                # Extract key metrics
                if "total_found" in tool_result:
                    summary_lines.append(f"📊 Found: {tool_result['total_found']} items")
                
                if "keywords" in tool_result:
                    summary_lines.append(f"🔍 Keywords: {', '.join(tool_result['keywords'])}")
                
                if "method" in tool_result:
                    summary_lines.append(f"📋 Method: {tool_result['method']}")
                
                # Show number of items in main result arrays
                if "laws" in tool_result and isinstance(tool_result["laws"], list):
                    summary_lines.append(f"📋 Laws returned: {len(tool_result['laws'])}")
                
                if "documents" in tool_result and isinstance(tool_result["documents"], list):
                    summary_lines.append(f"📄 Documents returned: {len(tool_result['documents'])}")
            
            if summary_lines:
                return "\n".join(summary_lines) + "\n\n" + "="*60 + "\nFULL RESULT:\n" + "="*60 + "\n" + formatted
            else:
                return formatted
                
        except Exception as e:
            return f"Result formatting error: {e}\nRaw result: {str(tool_result)}"

    def run_cli(self):
        """Main CLI loop."""
        print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE - API CLI")
        print("="*80)
        print("Interactive tool execution via deployed Lambda API")
        print("All tool calls are made through the REST API")
        print("="*80)

        self.initialize_tools()

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

                elif selected_tool == "test_api_health":
                    self.test_api_health()
                    continue

                # Execute selected tool via API
                print(f"\n🔧 SELECTED TOOL: {selected_tool}")

                # Show tool details
                self.display_tool_details(selected_tool)

                # Get input parameters
                tool_input = self.get_tool_input(selected_tool)
                if tool_input is None:
                    continue

                # Execute tool via API
                print(f"\n⚡ Calling API endpoint /tool/{selected_tool}...")
                print("="*50)

                result = self.call_tool_via_api(selected_tool, tool_input)

                # Display results
                print(f"\n📤 RESULTS FOR: {selected_tool}")
                print("="*60)
                formatted_result = self.format_api_result(selected_tool, result)
                print(formatted_result)
                print("="*60)

                # Ask if user wants to save results
                save = input("\n💾 Save results to file? (y/N): ").strip().lower()
                if save in ['y', 'yes']:
                    import time
                    filename = f"{selected_tool}_api_result_{int(time.time())}.json"
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump({
                                "tool_name": selected_tool,
                                "input": tool_input,
                                "api_response": result,
                                "timestamp": time.time(),
                                "api_url": self.api_url
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


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Quick tool execution mode
        tool_name = sys.argv[1]
        cli = LegalIntelligenceAPICLI()
        cli.initialize_tools()

        if tool_name in cli.available_tools:
            cli.display_tool_details(tool_name)
            tool_input = cli.get_tool_input(tool_name)
            if tool_input is not None:
                result = cli.call_tool_via_api(tool_name, tool_input)
                print(f"\n📤 RESULTS:")
                print("="*40)
                print(cli.format_api_result(tool_name, result))
        else:
            print(f"❌ Tool '{tool_name}' not found")
            print(f"Available tools: {', '.join(cli.available_tools.keys())}")
    else:
        # Interactive CLI mode
        cli = LegalIntelligenceAPICLI()
        cli.run_cli()


if __name__ == "__main__":
    main()