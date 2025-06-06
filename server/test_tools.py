#!/usr/bin/env python3
"""
Test individual MCP tools to identify which one is causing loops.
"""

import requests
import json

def test_mcp_tool(tool_name, tool_input):
    """Test calling an MCP tool directly."""
    print(f"\n🔧 Testing tool: {tool_name}")
    print(f"📥 Input: {tool_input}")
    
    try:
        # This is a simple test - actual MCP protocol is more complex
        response = requests.get("http://localhost:8080/mcp/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is reachable")
            print(f"📋 Response: {response.text}")
        else:
            print(f"❌ Server returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def test_simple_search():
    """Test the simple search function directly."""
    print("\n🔍 Testing Simple Search Function")
    
    # Import and test the search function directly
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    
    try:
        # Initialize the search engine directly
        from luxembourg_legal_server.search import LuxembourgSearch
        search = LuxembourgSearch("https://data.legilux.public.lu/sparqlendpoint")
        
        # Test domain identification
        domains = search.identify_legal_domains("Question juridique test")
        print(f"✅ Domain identification: {domains}")
        
        # Test simple search
        result = search.simple_title_search("SARL", 5)
        print(f"✅ Search result: Found {result.get('total_found', 0)} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct search test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing MCP Tools")
    print("=" * 50)
    
    # Test server connectivity
    test_mcp_tool("identify_legal_domain", {"legal_question": "Comment créer une SARL?"})
    
    # Test search function directly
    test_simple_search()