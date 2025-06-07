#!/usr/bin/env python3
"""
Simple Client for Luxembourg Legal Intelligence MCP Server
Professional Edition with 6 specialized tools
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import anthropic
from dotenv import load_dotenv
import logging
import time
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

load_dotenv()
logger = logging.getLogger(__name__)

class LegalIntelligenceClient:
    """Simple client for the 6-tool Luxembourg Legal Intelligence system."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.model = "claude-3-5-sonnet-20241022"
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Clean system prompt for 6-tool system
        self.system_prompt = """Vous êtes un assistant juridique expert en droit luxembourgeois.

Vous avez accès à 6 outils spécialisés pour la recherche légale professionnelle:

1. **search_documents(keyword)** - Recherche de documents avec mot-clé unique précis
   - Utilise des mots-clés simples qui apparaissent dans les titres légaux
   - Retourne documents avec métadonnées complètes JOLUX

2. **get_citations(document_uri)** - Réseau de citations bidirectionnel
   - Analyse les précédents juridiques et références croisées
   - 75,123 relations de citation disponibles

3. **get_amendments(document_uri)** - Historique complet des amendements
   - Évolution législative et chronologie des modifications
   - 26,826 relations de modification

4. **check_legal_status(document_uri)** - Validité légale actuelle
   - Vérification de validité et versions consolidées
   - 17,910 relations d'abrogation + 368 consolidations

5. **get_relationships(document_uri)** - Fondements et hiérarchie légale
   - Structure du cadre juridique et dépendances

6. **extract_content(document_uris)** - Extraction du texte légal réel
   - Contenu légal structuré pour analyse détaillée

STRATÉGIE DE RECHERCHE:
- Utilisez des mots-clés simples et précis (ex: "SARL", "société", "règlement")
- Évitez les phrases complexes qui ne donnent aucun résultat
- Laissez l'IA découvrir les patterns dans les métadonnées JOLUX
- Analysez les types de documents (LOI, RGD, AMIN) et domaines légaux

Répondez en français avec une analyse juridique professionnelle complète."""

        self.available_tools = []
        self._tools_initialized = False
    
    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return
        
        logger.info("🔧 Initializing 6 Professional Legal Tools...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                
                self.available_tools = []
                for tool in tools:
                    claude_tool = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    self.available_tools.append(claude_tool)
            
            self._tools_initialized = True
            logger.info(f"✅ Initialized {len(self.available_tools)} professional tools")
            
            print(f"\n🔧 PROFESSIONAL LEGAL INTELLIGENCE TOOLS:")
            for i, tool in enumerate(self.available_tools, 1):
                print(f"   {i}. {tool['name']}: {tool['description']}")
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
        
        # Simple formatting for clean display
        if tool_name == "search_documents":
            if isinstance(result, dict):
                doc_count = result.get("total_found", 0)
                keyword = result.get("keyword_used", "")
                return f"🔍 RECHERCHE: '{keyword}' → {doc_count} documents trouvés\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "get_citations":
            if isinstance(result, dict):
                inbound = result.get("inbound_count", 0)
                outbound = result.get("outbound_count", 0)
                return f"📚 CITATIONS: {inbound} entrants, {outbound} sortants\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "get_amendments":
            if isinstance(result, dict):
                made = result.get("modifications_made_count", 0)
                received = result.get("modifications_received_count", 0)
                return f"📝 AMENDEMENTS: {made} effectués, {received} reçus\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "check_legal_status":
            if isinstance(result, dict):
                status = result.get("legal_status", "unknown")
                consolidations = result.get("consolidation_count", 0)
                return f"💰 STATUT LÉGAL: {status}, {consolidations} consolidations\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "get_relationships":
            if isinstance(result, dict):
                foundations = result.get("foundation_count", 0)
                implementations = result.get("implementation_count", 0)
                return f"🔗 RELATIONS: {foundations} fondements, {implementations} implémentations\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "extract_content":
            if isinstance(result, dict):
                processed = result.get("total_processed", 0)
                return f"📄 CONTENU: {processed} documents traités\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
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
        max_iterations = 10  # Reduced for simpler workflow
        iteration = 0
        
        print(f"\n🧠 RECHERCHE LÉGALE PROFESSIONNELLE")
        print(f"📝 Question: {message}")
        print(f"🔧 Outils disponibles: {len(self.available_tools)}")
        print("=" * 80)
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
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
                
                if response.stop_reason == "tool_use":
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
                            
                            print(f"\n🔧 EXÉCUTION: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False)}")
                            
                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            tools_used.append({"name": tool_name, "iteration": iteration})
                            
                            formatted_result = self.format_tool_result(tool_result)
                            print(f"📤 Résultat: {formatted_result[:200]}{'...' if len(formatted_result) > 200 else ''}")
                            
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
                    
                    print(f"\n✅ RECHERCHE TERMINÉE")
                    print(f"🔧 Outils utilisés: {len(tools_used)}")
                    print(f"⏱️ Temps: {processing_time:.2f}s")
                    print("=" * 80)
                    
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "iterations": iteration,
                        "processing_time": processing_time,
                        "provider": "luxembourg_legal_intelligence"
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

async def test_legal_system():
    """Test the Luxembourg Legal Intelligence system."""
    client = LegalIntelligenceClient()
    
    print("🏛️ LUXEMBOURG LEGAL INTELLIGENCE MCP SERVER - PROFESSIONAL EDITION")
    print("=" * 80)
    print("🎯 6 Specialized Professional Tools")
    print("⚡ Single-keyword precision strategy") 
    print("🔗 Proven JOLUX relationship intelligence")
    print("📊 75K+ citations, 26K+ amendments, 17K+ repeals")
    print("=" * 80)
    
    test_question = "Comment créer une SARL au Luxembourg? Quelles sont les procédures et obligations actuelles?"
    
    print(f"\n🧪 TEST DE LA RECHERCHE LÉGALE PROFESSIONNELLE")
    print(f"📝 Question: {test_question}")
    
    try:
        result = await client.chat(test_question)
        
        print(f"\n📋 RÉSULTATS:")
        print(f"✅ Réponse: {len(result['response'])} caractères")
        print(f"🔧 Outils: {len(result.get('tools_used', []))}")
        print(f"⏱️ Temps: {result.get('processing_time', 0):.2f}s")
        
        response_preview = result['response'][:500] + "..." if len(result['response']) > 500 else result['response']
        print(f"\n📄 APERÇU:")
        print(response_preview)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_legal_system())