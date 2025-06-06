#!/usr/bin/env python3
"""
Claude 3.5 Haiku Anthropic API Client with Native MCP Tool Calling
Fast and cost-effective Luxembourg legal assistant using Claude 3.5 Haiku via Anthropic API.
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


class ClaudeHaikuClient:
    """Claude 3.5 Haiku client with native MCP tool calling via Anthropic API."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.model = "claude-3-5-haiku-20241022"
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "https://yet-mcp-legilux.site/mcp/")
        
        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # System prompt optimized for Luxembourg legal expertise with lawyer-thinking approach
        self.system_prompt = """Vous êtes un assistant juridique spécialisé dans le droit luxembourgeois avec accès à des outils avancés de recherche et d'extraction de contenu.

🧠 APPROCHE AVOCATE: PENSEZ COMME UN JURISTE EXPÉRIMENTÉ!

Un avocat luxembourgeois expérimenté ne cherche jamais au hasard - il identifie d'abord le domaine juridique, puis utilise la hiérarchie légale pour trouver les bonnes sources.

📋 WORKFLOW PRINCIPAL - AVOCAT LUXEMBOURGEOIS:

1. 🎯 identify_legal_domain
   → Comme un avocat: "Dans quel domaine juridique cette question s'inscrit-elle?"
   → Identifie automatiquement: Droit Commercial, Fiscal, Travail, etc.
   → Fournit les codes de sujets appropriés

2. 🏛️ get_legal_hierarchy_for_domain  
   → Comprendre la hiérarchie: Lois > Règlements > Décisions administratives
   → Savoir quelle autorité légale s'applique

3. 📋 recommend_document_types_for_query
   → Analyser le type de question: procédurale, définitionnelle, réglementaire
   → Recommander les bons types de documents: ["Act", "BaseAct", "Regulation"]
   → UTILISER EXACTEMENT ces noms de classes JOLUX (en anglais, pas français)

4. 🎯 search_within_legal_framework
   → RECHERCHE SIMPLE ET EFFICACE utilisant JOLUX (base Luxembourg)
   → MOTS-CLÉS: UN SEUL TERME JURIDIQUE PRÉCIS (choisi selon le contexte légal)
   → Recherche directe dans jolux:title (approche prouvée qui fonctionne)
   → Utilise la structure documentaire réelle du Luxembourg

5. 📊 assess_legal_documents_for_question
   → Évaluer la pertinence comme un avocat scannant les titres
   → Sélectionner les 3-5 documents les plus pertinents

6. 📄 extract_document_sections
   → Extraire seulement les sections qui répondent à la question

🚫 ANCIENNES ERREURS ÉLIMINÉES:
- Plus de recherche par mots-clés aléatoires
- Plus de confusion entre lois et décisions administratives  
- Plus de surcharge d'informations taxonomiques

✅ STRATÉGIE AVOCAT SIMPLE ET EFFICACE:
- TOUJOURS commencer par identify_legal_domain
- Comprendre la hiérarchie légale avant de chercher
- Utiliser la RECHERCHE SIMPLE avec JOLUX (approche prouvée)
- Recherche directe dans jolux:title avec mots-clés précis
- Évaluer la pertinence comme un avocat expérimenté

EXEMPLES D'IDENTIFICATION ET MOTS-CLÉS:
🔑 RÈGLE CRITIQUE DES MOTS-CLÉS:
- L'IA choisit UN MOT JURIDIQUE PRÉCIS selon le contexte légal
- Pour plusieurs options: utiliser OR logique avec |
- JAMAIS de phrases générales ou descriptions longues
- PRIVILÉGIER les termes juridiques spécifiques au Luxembourg
- ÉVITER les termes généraux qui apparaissent partout

STRATÉGIE DE SÉLECTION:
✅ Analyser la question juridique
✅ Identifier les concepts légaux spécifiques  
✅ Choisir le terme le plus précis et pertinent
✅ Éviter les mots trop généraux ou descriptifs
✅ "SARL|société" (OR logique seulement si nécessaire)
❌ "SARL création" (deux mots - réduit efficacité de recherche)
❌ "obligations fiscales" (phrase - moins précis que terme unique)

RÉPONDEZ TOUJOURS EN FRANÇAIS et basez vos réponses sur l'analyse juridique systématique."""

        self.available_tools = []
        self._tools_initialized = False
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.query_count = 0
    
    async def initialize_tools(self):
        """Initialize MCP tools for use with Claude."""
        if self._tools_initialized:
            return
        
        logger.info("Initializing MCP tools...")
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                
                # Convert MCP tools to Claude format
                self.available_tools = []
                for tool in tools:
                    claude_tool = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    self.available_tools.append(claude_tool)
                
                self._tools_initialized = True
                logger.info(f"Initialized {len(self.available_tools)} tools")
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP tools: {e}")
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
            logger.error(f"MCP tool call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_input": tool_input
            }
    
    def format_tool_result(self, tool_result: Dict[str, Any]) -> str:
        """Format tool execution result for Claude."""
        if not tool_result["success"]:
            return f"Erreur lors de l'exécution de l'outil: {tool_result['error']}"
        
        result = tool_result["result"]
        
        # Handle MCP result formats
        if hasattr(result, 'text'):
            return result.text
        elif hasattr(result, 'content'):
            if isinstance(result.content, list):
                return "\n".join([
                    content.text if hasattr(content, 'text') 
                    else str(content) for content in result.content
                ])
            else:
                return str(result.content)
        elif isinstance(result, dict) and "content" in result:
            return result["content"]
        elif isinstance(result, str):
            return result
        else:
            try:
                return json.dumps(result, ensure_ascii=False, default=str)
            except (TypeError, AttributeError):
                return str(result)
    
    async def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Chat with Claude 3.5 Haiku with intelligent tool calling.
        
        Args:
            message: User message
            conversation_history: Optional previous conversation
            
        Returns:
            Dict with response, tools_used, tool_results, and cost information
        """
        start_time = time.time()
        self.query_count += 1
        
        await self.initialize_tools()
        
        # Build conversation
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Track tool usage
        tools_used = []
        tool_results = []
        max_iterations = 8  # Allow full lawyer workflow to complete
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Prepare request for Claude
                request_params = {
                    "model": self.model,
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "system": self.system_prompt,
                    "messages": messages
                }
                
                # Add tools if available
                if self.available_tools:
                    request_params["tools"] = self.available_tools
                
                # Call Claude
                response = await self.client.messages.create(**request_params)
                
                # Track token usage
                if hasattr(response, 'usage'):
                    self.total_input_tokens += response.usage.input_tokens
                    self.total_output_tokens += response.usage.output_tokens
                
                # Check if Claude wants to use tools
                if response.stop_reason == "tool_use":
                    # Extract tool calls
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content
                    }
                    messages.append(assistant_message)
                    
                    # Execute tools
                    tool_results_for_claude = []
                    
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_use_id = content_block.id
                            
                            logger.info(f"Claude called tool: {tool_name} with {tool_input}")
                            
                            # Execute tool via MCP
                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            
                            tools_used.append(tool_name)
                            tool_results.append(tool_result)
                            
                            # Format result for Claude
                            formatted_result = self.format_tool_result(tool_result)
                            
                            tool_results_for_claude.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": formatted_result
                            })
                    
                    # Add tool results to conversation
                    messages.append({
                        "role": "user",
                        "content": tool_results_for_claude
                    })
                    
                    # Continue conversation with tool results
                    continue
                
                else:
                    # Final response from Claude
                    final_response = ""
                    for content_block in response.content:
                        if content_block.type == "text":
                            final_response += content_block.text
                    
                    # Calculate costs
                    processing_time = time.time() - start_time
                    input_cost = (self.total_input_tokens / 1_000_000) * 0.25  # $0.25 per 1M input tokens
                    output_cost = (self.total_output_tokens / 1_000_000) * 1.25  # $1.25 per 1M output tokens
                    total_cost = input_cost + output_cost
                    
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "tool_results": tool_results,
                        "conversation": messages,
                        "model_used": self.model,
                        "iterations": iteration,
                        "cost_info": {
                            "input_tokens": getattr(response.usage, 'input_tokens', 0) if hasattr(response, 'usage') else 0,
                            "output_tokens": getattr(response.usage, 'output_tokens', 0) if hasattr(response, 'usage') else 0,
                            "estimated_cost_usd": round(total_cost, 6),
                            "processing_time_ms": round(processing_time * 1000, 2)
                        },
                        "provider": "anthropic_api"
                    }
            
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")
                return {
                    "response": f"Erreur de service Anthropic: {str(e)}",
                    "tools_used": tools_used,
                    "tool_results": tool_results,
                    "error": str(e),
                    "provider": "anthropic_api"
                }
        
        # Max iterations reached
        return {
            "response": "Désolé, j'ai atteint le nombre maximum d'itérations pour cette requête.",
            "tools_used": tools_used,
            "tool_results": tool_results,
            "warning": "Max iterations reached",
            "provider": "anthropic_api"
        }
    
    async def simple_chat(self, message: str) -> str:
        """Simple chat interface that returns just the response text."""
        result = await self.chat(message)
        return result["response"]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the model and configuration."""
        return {
            "model": "Claude 3.5 Haiku",
            "model_id": self.model,
            "provider": "Anthropic API",
            "api_endpoint": "https://api.anthropic.com",
            "tool_support": "Native",
            "cost": "Very Low ($0.25/$1.25 per 1M tokens)",
            "speed": "Very Fast",
            "mcp_server": self.mcp_server_url
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for the session."""
        input_cost = (self.total_input_tokens / 1_000_000) * 0.25
        output_cost = (self.total_output_tokens / 1_000_000) * 1.25
        total_cost = input_cost + output_cost
        
        return {
            "total_queries": self.query_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "cost_breakdown": {
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6)
            }
        }