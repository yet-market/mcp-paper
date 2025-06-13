#!/usr/bin/env python3
"""
API-based CLI client for invoking individual MCP tools via the serverless API.
Allows listing available tools, prompting for their input parameters, and calling them.
"""

import os
import sys
import json
import requests

API_URL = os.environ.get(
    "LEGAL_API_URL",
    "https://ymtocda5s2.execute-api.eu-west-2.amazonaws.com/prod"
)
API_KEY = os.environ.get("LEGAL_API_KEY", "o7tKNwreM48ojccC4ck6j5ZtIhWiNVFj7ffrGuMw")


def fetch_tools():
    """Retrieve the list of available MCP tools and their schemas."""
    resp = requests.get(f"{API_URL}/tools", headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    })
    resp.raise_for_status()
    return resp.json().get("available_tools", [])


def prompt_tool_selection(tools):
    """Prompt the user to select one tool from the list."""
    print("\nAvailable MCP Tools:")
    for idx, tool in enumerate(tools, start=1):
        name = tool.get("name")
        desc = tool.get("description", "")
        print(f"  {idx:2d}. {name} - {desc}")
    print()
    choice = input("Select tool number: ").strip()
    try:
        i = int(choice)
        if 1 <= i <= len(tools):
            return tools[i-1]
    except ValueError:
        pass
    print(f"Invalid selection '{choice}'\n")
    return None


def collect_params(input_schema):
    """Interactively collect parameters per inputSchema."""
    props = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))
    params = {}

    for name, info in props.items():
        ptype = info.get("type", "string")
        desc = info.get("description", "")
        req = name in required
        prompt = f"{name} ({ptype}){' [required]' if req else ''}: "
        if desc:
            print(f"  - {desc}")
        while True:
            val = input(prompt).strip()
            if not val and not req:
                break
            if ptype == 'array':
                items = [v.strip() for v in val.split(',') if v.strip()]
                params[name] = items
                break
            elif ptype == 'integer':
                try:
                    params[name] = int(val)
                    break
                except ValueError:
                    print("Please enter a valid integer.")
            elif ptype == 'boolean':
                l = val.lower()
                if l in ('y','yes','true','1'):
                    params[name] = True
                    break
                if l in ('n','no','false','0'):
                    params[name] = False
                    break
                print("Enter yes/no or true/false.")
            else:
                params[name] = val
                break
        print()
    return params


def call_tool(tool_name, payload):
    """Invoke the chosen tool via the API and return the JSON result."""
    url = f"{API_URL}/tool/{tool_name}"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()


def main():
    print("\n🔧 MCP TOOL-CLIENT (via API)")
    print("API URL:", API_URL)
    print("API Key:", API_KEY)

    try:
        tools = fetch_tools()
    except Exception as e:
        print(f"❌ Failed to fetch tools list: {e}")
        sys.exit(1)

    selected = None
    while not selected:
        selected = prompt_tool_selection(tools)

    input_schema = selected.get('inputSchema') or {}
    params = collect_params(input_schema)

    print(f"\n🚀 Calling tool '{selected['name']}' with parameters:")
    print(json.dumps(params, indent=2, ensure_ascii=False))

    try:
        result = call_tool(selected['name'], params)
        print("\n📄 Tool Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Tool invocation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()