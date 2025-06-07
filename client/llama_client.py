#!/usr/bin/env python3
"""
Llama-Optimized Client for Luxembourg Legal Intelligence MCP Server
Specialized system prompt and instructions for Llama models (Groq)
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from groq import AsyncGroq
from dotenv import load_dotenv
import logging
import time
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

load_dotenv()
logger = logging.getLogger(__name__)

class LlamaLegalIntelligenceClient:
    """Llama-optimized client for Luxembourg Legal Intelligence."""
    
    def __init__(self):
        # Groq/Llama configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.model = os.getenv("LLAMA_MODEL", "llama-3.3-70b-versatile")
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
        self.client = AsyncGroq(api_key=self.groq_api_key)
        
        # Llama-optimized system prompt - simpler and more explicit
        self.system_prompt = """You are a Luxembourg legal research assistant. Follow these EXACT rules:

🚨 CRITICAL SEARCH RULES:
1. ONLY use single keywords: "SARL", "société", "commercial", "entreprise"
2. NEVER use phrases like "SARL Luxembourg" - they return 0 results
3. NEVER use multiple words together - JOLUX only works with single words

🔧 REQUIRED TOOL SEQUENCE:
Step 1: search_documents("SARL") 
Step 2: search_documents("commercial")
Step 3: ANALYZE search results and pick URIs related to SARL/company law
Step 4: Look for URIs containing "1915" (foundational law) or "societes" or "commerciales"
Step 5: get_citations(most_relevant_uri_for_sarl_creation)
Step 6: get_amendments(most_relevant_uri_for_sarl_creation) 
Step 7: check_legal_status(most_relevant_uri_for_sarl_creation)
Step 8: get_relationships(most_relevant_uri_for_sarl_creation)
Step 9: extract_content([best_uris_for_sarl_creation])

🚨 CRITICAL URI VALIDATION:
- ONLY use URIs that appear in search_documents results
- NEVER use URIs from your training data or knowledge  
- If search returns 0 documents, you CANNOT proceed with analysis
- Pick URIs about COMPANY LAW, not random laws
- Look for "1915" (base law), "societes commerciales", or "SARL" in titles

✅ GOOD KEYWORDS: "SARL", "société", "commercial", "loi", "règlement"
❌ BAD KEYWORDS: "SARL Luxembourg", "loi en vigueur", "société commerciale"

🎯 RESPONSE FORMAT:
Always include these sections:
## LEGAL ANALYSIS
[Your analysis]

## PRIMARY SOURCES
- URI: [full URI]
  Title: [title]
  Status: [active/repealed]

## CITATION NETWORK
- Cites: [URIs]
- Cited by: [URIs]

## AMENDMENTS
- [Date]: [Change] - URI: [URI]

## LEGAL STATUS
- [Current validity confirmation]

Remember: Single keywords only. Multiple tool usage required. Include all URIs in response."""

        self.available_tools = []
        self._tools_initialized = False
    
    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return
        
        logger.info("🔧 Initializing Tools for Llama...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                
                self.available_tools = []
                for tool in tools:
                    # Convert to OpenAI format for Groq
                    groq_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    }
                    self.available_tools.append(groq_tool)
            
            self._tools_initialized = True
            logger.info(f"✅ Initialized {len(self.available_tools)} tools for Llama")
                
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
        """Format tool execution result for Llama."""
        if not tool_result["success"]:
            return f"❌ Tool {tool_result['tool_name']} failed: {tool_result['error']}"
        
        result = tool_result["result"]
        tool_name = tool_result["tool_name"]
        
        # Simple formatting optimized for Llama
        if tool_name == "search_documents":
            if isinstance(result, dict):
                doc_count = result.get("total_found", 0)
                keyword = result.get("keyword_used", "")
                return f"SEARCH RESULT: '{keyword}' found {doc_count} documents\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        # Default formatting
        try:
            return f"{tool_name.upper()} RESULT:\n{json.dumps(result, ensure_ascii=False, indent=2, default=str)}"
        except (TypeError, AttributeError):
            return f"{tool_name.upper()} RESULT:\n{str(result)}"
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Llama-optimized chat with explicit tool guidance."""
        start_time = time.time()
        
        await self.initialize_tools()
        
        # Llama-specific message format
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message}
        ]
        
        tools_used = []
        max_iterations = 15  # Slightly lower for Llama
        iteration = 0
        
        print(f"\n🦙 LLAMA LEGAL INTELLIGENCE")
        print(f"📝 Question: {message}")
        print(f"🔧 Tools available: {len(self.available_tools)}")
        print(f"🤖 Model: {self.model}")
        print("=" * 80)
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Iteration {iteration}")
            
            try:
                request_params = {
                    "model": self.model,
                    "max_tokens": 4000,
                    "temperature": 0.1,  # Lower temperature for more consistent following
                    "messages": messages,
                    "tools": self.available_tools,
                    "tool_choice": "auto"
                }
                
                response = await self.client.chat.completions.create(**request_params)
                
                if response.choices[0].finish_reason == "tool_calls":
                    # Handle tool calls
                    assistant_message = {
                        "role": "assistant",
                        "content": response.choices[0].message.content or "",
                        "tool_calls": []
                    }
                    
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
                    
                    # Execute tools
                    for tool_call in response.choices[0].message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_input = json.loads(tool_call.function.arguments)
                        tool_use_id = tool_call.id
                        
                        print(f"\n🔧 EXECUTING: {tool_name}")
                        print(f"📥 Input: {json.dumps(tool_input, ensure_ascii=False)}")
                        
                        # Enhanced validation and logging
                        if tool_name == "search_documents":
                            keyword = tool_input.get("keyword", "")
                            if " " in keyword:
                                print(f"⚠️  WARNING: Multi-word keyword detected: '{keyword}'")
                                print(f"🔧 This will likely return 0 results with JOLUX")
                        
                        # Log URI selection for analysis tools
                        if tool_name in ["get_citations", "get_amendments", "check_legal_status", "get_relationships"]:
                            uri = tool_input.get("document_uri", "")
                            print(f"🔍 URI SELECTED: {uri}")
                            
                            # Check if URI came from search results
                            uri_in_search = False
                            if hasattr(self, '_last_search_uris'):
                                if uri in self._last_search_uris:
                                    print(f"✅ URI FOUND in search results")
                                    uri_in_search = True
                            
                            if not uri_in_search:
                                print(f"🚨 WARNING: URI NOT found in search results - Llama invented this URI!")
                                print(f"🧠 Source: Likely from Llama's training data or reasoning")
                                print(f"❌ BLOCKING TOOL CALL - Only using URIs from search results")
                                
                                # Skip this tool call and add error message
                                formatted_result = f"❌ BLOCKED: URI '{uri}' not found in search results. Please use only URIs from previous search_documents results."
                                print(f"📤 Result: {formatted_result}")
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_use_id,
                                    "content": formatted_result
                                })
                                continue
                            
                            if "1915" in uri and "n7" in uri:
                                print(f"⚠️  WARNING: Using n7 version, consider n1 for main commercial law")
                        
                        # Log content extraction requests
                        if tool_name == "extract_content":
                            uris = tool_input.get("document_uris", [])
                            print(f"📄 CONTENT EXTRACTION FOR: {len(uris)} documents")
                            
                            # Validate all URIs come from search results
                            invalid_uris = []
                            if hasattr(self, '_last_search_uris'):
                                for uri in uris:
                                    if uri not in self._last_search_uris:
                                        invalid_uris.append(uri)
                            
                            if invalid_uris:
                                print(f"🚨 WARNING: {len(invalid_uris)} URI(s) not from search results:")
                                for uri in invalid_uris:
                                    print(f"   ❌ {uri}")
                                print(f"❌ BLOCKING TOOL CALL - Only using URIs from search results")
                                
                                formatted_result = f"❌ BLOCKED: {len(invalid_uris)} URI(s) not found in search results. Please use only URIs from previous search_documents results."
                                print(f"📤 Result: {formatted_result}")
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_use_id,
                                    "content": formatted_result
                                })
                                continue
                            
                            for i, uri in enumerate(uris):
                                print(f"   {i+1}. {uri}")
                        
                        tool_result = await self.call_mcp_tool(tool_name, tool_input)
                        tools_used.append({"name": tool_name, "iteration": iteration})
                        
                        formatted_result = self.format_tool_result(tool_result)
                        
                        # Enhanced search result analysis
                        if tool_name == "search_documents" and tool_result.get("success"):
                            try:
                                result_data = tool_result.get("result", [])
                                if isinstance(result_data, list) and len(result_data) > 0:
                                    # Handle different result formats
                                    first_result = result_data[0]
                                    if hasattr(first_result, 'text'):
                                        result_text = first_result.text
                                    elif isinstance(first_result, dict):
                                        result_text = first_result.get("text", "{}")
                                    else:
                                        result_text = str(first_result)
                                    
                                    # Extract JSON from the text
                                    if result_text.startswith("'") and result_text.endswith("'"):
                                        result_text = result_text[1:-1]  # Remove quotes
                                    
                                    # Find JSON part
                                    json_start = result_text.find('{')
                                    if json_start >= 0:
                                        json_text = result_text[json_start:]
                                        result_json = json.loads(json_text)
                                        documents = result_json.get("documents", [])
                                        
                                        print(f"📊 SEARCH ANALYSIS:")
                                        print(f"   Found: {len(documents)} documents")
                                        
                                        # Highlight relevant documents
                                        relevant_docs = []
                                        for doc in documents[:10]:  # Check first 10
                                            uri = doc.get("uri", "")
                                            title = doc.get("title", "")
                                            
                                            # Look for commercial law indicators
                                            if any(indicator in uri.lower() or indicator in title.lower() 
                                                   for indicator in ["1915", "commercial", "societe", "sarl"]):
                                                relevant_docs.append({"uri": uri, "title": title[:100]})
                                        
                                        # Store URIs for tracking
                                        all_uris = [doc.get("uri", "") for doc in documents]
                                        if not hasattr(self, '_last_search_uris'):
                                            self._last_search_uris = []
                                        self._last_search_uris.extend(all_uris)
                                        
                                        if relevant_docs:
                                            print(f"   🎯 RELEVANT DOCUMENTS FOUND:")
                                            for i, doc in enumerate(relevant_docs[:3]):
                                                print(f"      {i+1}. {doc['uri']}")
                                                print(f"         {doc['title']}")
                                        else:
                                            print(f"   ⚠️  No obviously relevant documents in first 10 results")
                                            
                                        # Show if any LOI (laws) were found
                                        loi_count = sum(1 for uri in all_uris if "/leg/loi/" in uri)
                                        amin_count = sum(1 for uri in all_uris if "/adm/amin/" in uri)
                                        print(f"   📊 Document types: {loi_count} LOI (laws), {amin_count} AMIN (ministerial)")
                                            
                            except Exception as e:
                                print(f"   📊 SEARCH ANALYSIS: Could not parse results - {str(e)}")
                                pass
                        
                        print(f"📤 Result: {formatted_result[:200]}{'...' if len(formatted_result) > 200 else ''}")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_use_id,
                            "content": formatted_result
                        })
                    
                    continue
                
                else:
                    # Final response
                    final_response = response.choices[0].message.content or ""
                    
                    processing_time = time.time() - start_time
                    
                    print(f"\n✅ LLAMA RESEARCH COMPLETE")
                    print(f"🔧 Tools used: {len(tools_used)}")
                    print(f"⏱️ Time: {processing_time:.2f}s")
                    print("=" * 80)
                    
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "iterations": iteration,
                        "processing_time": processing_time,
                        "provider": f"groq_{self.model}"
                    }
            
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                return {
                    "response": f"Error: {str(e)}",
                    "tools_used": tools_used,
                    "error": str(e)
                }
        
        return {
            "response": "Max iterations reached.",
            "tools_used": tools_used,
            "warning": "Max iterations reached"
        }

async def test_llama_legal_system():
    """Test the Llama-optimized Luxembourg Legal Intelligence system."""
    client = LlamaLegalIntelligenceClient()
    
    print("🦙 LLAMA LUXEMBOURG LEGAL INTELLIGENCE - OPTIMIZED EDITION")
    print("=" * 80)
    print("🎯 6 Specialized Professional Tools")
    print("⚡ Single-keyword precision strategy (Llama-optimized)")
    print("🔗 Proven JOLUX relationship intelligence")
    print("📊 75K+ citations, 26K+ amendments, 17K+ repeals")
    print(f"🤖 AI Model: GROQ - {client.model}")
    print("🚨 Explicit instruction-following for Llama models")
    print("=" * 80)
    
    test_question = "Quelles sont les lois en vigueur pour créer une SARL au Luxembourg? Je veux les textes légaux complets, leur historique d'amendements, et toutes les références juridiques."
    
    print(f"\n🧪 TEST DE LA RECHERCHE LÉGALE LLAMA")
    print(f"📝 Question: {test_question}")
    
    try:
        result = await client.chat(test_question)
        
        print(f"\n📋 RÉSULTATS LLAMA:")
        print(f"✅ Réponse: {len(result['response'])} caractères")
        print(f"🔧 Outils: {len(result.get('tools_used', []))}")
        print(f"⏱️ Temps: {result.get('processing_time', 0):.2f}s")
        
        print(f"\n📄 RÉPONSE COMPLÈTE:")
        print("=" * 80)
        print(result['response'])
        print("=" * 80)
        
        # Show tools used details
        if result.get('tools_used'):
            print(f"\n🔧 OUTILS UTILISÉS:")
            for i, tool in enumerate(result['tools_used'], 1):
                print(f"   {i}. {tool['name']} (itération {tool['iteration']})")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_llama_legal_system())