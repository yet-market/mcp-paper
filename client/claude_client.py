#!/usr/bin/env python3
"""
Claude Client for Luxembourg Legal Intelligence MCP Server
Pure Anthropic implementation - Professional Edition
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

class ClaudeLegalIntelligenceClient:
    """Pure Claude client for Luxembourg Legal Intelligence system."""
    
    def __init__(self):
        # Claude configuration only
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.model = "claude-3-5-sonnet-20241022"
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Enhanced system prompt for comprehensive tool usage
        self.system_prompt = """Vous êtes un assistant juridique expert en droit luxembourgeois avec accès à un système d'intelligence légale avancé.

🎯 MÉTHODOLOGIE OBLIGATOIRE - UTILISEZ TOUS LES OUTILS:

1. **RECHERCHE INITIALE**
   - search_documents(keyword) avec mots-clés précis
   - TOUJOURS essayer plusieurs mots-clés (ex: "SARL", "société", "commercial")
   - Chercher les LOIS fondamentales, pas seulement les arrêtés d'application

2. **ANALYSE DES SOURCES** (OBLIGATOIRE pour chaque document trouvé)
   - get_citations(uri) - Découvrir le réseau juridique complet
   - get_amendments(uri) - Tracer l'évolution législative  
   - check_legal_status(uri) - Vérifier la validité actuelle
   - get_relationships(uri) - Comprendre la hiérarchie légale

3. **EXTRACTION DU CONTENU** (ESSENTIEL)
   - extract_content([uris]) - Obtenir le texte légal réel
   - Maximum 3-5 documents les plus pertinents
   - Prioriser les LOI sur les AMIN/RGD

🔧 OUTILS DISPONIBLES (UTILISEZ-LES TOUS):

1. **search_documents(keyword)** - Recherche précise par mot-clé unique
2. **get_citations(document_uri)** - 75K+ relations de citation 
3. **get_amendments(document_uri)** - 26K+ relations de modification
4. **check_legal_status(document_uri)** - Validité et consolidations
5. **get_relationships(document_uri)** - Hiérarchie et fondements légaux
6. **extract_content(document_uris)** - Texte légal complet avec fallback HTML/PDF

🎯 STRATÉGIE SYSTÉMATIQUE:
- Commencer par les termes juridiques précis (SARL, société, commercial, entreprise)
- Identifier les lois de base (LOI) vs arrêtés d'application (AMIN)
- Utiliser CHAQUE outil sur les documents les plus pertinents
- Construire un tableau complet avec sources, citations, amendements
- Extraire le contenu légal réel pour analyse détaillée

❗ EXIGENCES DE QUALITÉ ABSOLUES:
- TOUJOURS inclure les URIs sources complets dans votre réponse finale
- TOUJOURS citer les articles spécifiques avec leurs numéros (ex: Art. 26, Art. 30)
- TOUJOURS mentionner les sections et leurs noms (ex: Section II - Des sociétés anonymes)
- TOUJOURS extraire et citer les passages pertinents du texte légal
- TOUJOURS lister les citations découvertes avec leurs URIs
- TOUJOURS mentionner les amendements avec dates et URIs
- TOUJOURS indiquer le statut légal actuel de chaque source
- TOUJOURS créer une section "SOURCES JURIDIQUES" avec tous les liens
- TOUJOURS créer une section "RÉSEAU JURIDIQUE" avec les citations
- TOUJOURS créer une section "HISTORIQUE" avec les amendements

FORMAT DE RÉPONSE OBLIGATOIRE:

## RÉPONSE JURIDIQUE
[Votre analyse légale avec citations précises d'articles]

## ARTICLES ET SECTIONS PERTINENTS
- Article [numéro] - [Titre/objet] (URI: [uri])
  Extrait: "[citation textuelle pertinente]"
- Section [numéro] - [Nom de la section] (URI: [uri])
  Articles: [liste des articles dans cette section]

## SOURCES JURIDIQUES PRINCIPALES
- URI: [uri complet]
  Titre: [titre]
  Date: [date]  
  Statut: [actif/abrogé]
  Articles clés: [Art. X, Art. Y, Art. Z]

## RÉSEAU DE CITATIONS
- Cette loi cite: [URIs des lois citées]
- Cette loi est citée par: [URIs des lois qui la citent]

## HISTORIQUE DES AMENDEMENTS  
- [Date]: [Description] - URI: [uri]
  Articles modifiés: [Art. X, Art. Y]

## VALIDITÉ LÉGALE
- [Confirmation du statut actuel de chaque source]

Répondez en français avec cette structure OBLIGATOIRE incluant TOUS les URIs et liens découverts."""

        self.available_tools = []
        self._tools_initialized = False
    
    async def initialize_tools(self):
        """Initialize MCP tools."""
        if self._tools_initialized:
            return
        
        logger.info("🔧 Initializing 6 Professional Legal Tools for Claude...")
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
            logger.info(f"✅ Initialized {len(self.available_tools)} professional tools for Claude")
            
            print(f"\n🔧 CLAUDE PROFESSIONAL LEGAL INTELLIGENCE TOOLS:")
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
        """Format tool execution result for Claude with enhanced article parsing."""
        if not tool_result["success"]:
            return f"❌ Erreur lors de l'exécution de l'outil {tool_result['tool_name']}: {tool_result['error']}"
        
        result = tool_result["result"]
        tool_name = tool_result["tool_name"]
        
        # Enhanced formatting for clean display with article extraction
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
                # Add article structure analysis for legal content
                formatted_result = f"📄 CONTENU: {processed} documents traités\n"
                
                # Try to parse article structure from content
                if "documents" in result and result["documents"]:
                    for i, doc in enumerate(result["documents"]):
                        if "content" in doc:
                            content = doc.get("content", "")
                            articles = self._extract_article_references(content)
                            sections = self._extract_section_references(content)
                            
                            if articles or sections:
                                formatted_result += f"\n📋 STRUCTURE DOCUMENT {i+1}:\n"
                                if sections:
                                    formatted_result += f"   📚 Sections: {', '.join(sections[:5])}{'...' if len(sections) > 5 else ''}\n"
                                if articles:
                                    formatted_result += f"   📖 Articles: {', '.join(articles[:10])}{'...' if len(articles) > 10 else ''}\n"
                
                formatted_result += f"\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                return formatted_result
        
        # Default formatting
        try:
            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        except (TypeError, AttributeError):
            return str(result)
    
    def _extract_article_references(self, content: str) -> List[str]:
        """Extract article references from legal content."""
        import re
        articles = []
        
        # Pattern for articles: Art. 26, Article 30, etc.
        article_patterns = [
            r'Art\.\s*(\d+)',
            r'Article\s*(\d+)',
            r'art\.\s*(\d+)',
            r'article\s*(\d+)'
        ]
        
        for pattern in article_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                articles.append(f"Art. {match}")
        
        # Remove duplicates and sort
        return sorted(list(set(articles)), key=lambda x: int(x.split('.')[1]))
    
    def _extract_section_references(self, content: str) -> List[str]:
        """Extract section references from legal content."""
        import re
        sections = []
        
        # Pattern for sections: Section I, Section II - Des sociétés, etc.
        section_patterns = [
            r'Section\s+([IVX]+)\.?(?:\s*[-—]\s*([^\\n]+))?',
            r'§\s*(\d+)\.?(?:\s*[-—]\s*([^\\n]+))?'
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) > 1 and match[1]:
                        sections.append(f"Section {match[0]} - {match[1].strip()}")
                    else:
                        sections.append(f"Section {match[0]}")
                else:
                    sections.append(f"Section {match}")
        
        # Remove duplicates
        return list(set(sections))
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Enhanced chat with professional legal research workflow."""
        start_time = time.time()
        
        await self.initialize_tools()
        
        messages = [{"role": "user", "content": message}]
        tools_used = []
        max_iterations = 20  # Increased for comprehensive legal research
        iteration = 0
        
        print(f"\n🧠 CLAUDE RECHERCHE LÉGALE PROFESSIONNELLE")
        print(f"📝 Question: {message}")
        print(f"🔧 Outils disponibles: {len(self.available_tools)}")
        print(f"🤖 Model: {self.model}")
        print("=" * 80)
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Pure Anthropic format
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
                            print(f"📤 Résultat complet:")
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
                    
                    print(f"\n✅ CLAUDE RECHERCHE TERMINÉE")
                    print(f"🔧 Outils utilisés: {len(tools_used)}")
                    print(f"⏱️ Temps: {processing_time:.2f}s")
                    print("=" * 80)
                    
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "iterations": iteration,
                        "processing_time": processing_time,
                        "provider": f"anthropic_{self.model}"
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

async def test_claude_legal_system():
    """Test the Claude Luxembourg Legal Intelligence system."""
    client = ClaudeLegalIntelligenceClient()
    
    print("🧠 CLAUDE LUXEMBOURG LEGAL INTELLIGENCE - PROFESSIONAL EDITION")
    print("=" * 80)
    print("🎯 6 Specialized Professional Tools")
    print("⚡ Single-keyword precision strategy") 
    print("🔗 Proven JOLUX relationship intelligence")
    print("📊 75K+ citations, 26K+ amendments, 17K+ repeals")
    print(f"🤖 AI Model: ANTHROPIC - {client.model}")
    print("=" * 80)
    
    test_question = "Quelles sont les lois en vigueur pour créer une SARL au Luxembourg? Je veux les textes légaux complets, leur historique d'amendements, et toutes les références juridiques."
    
    print(f"\n🧪 TEST DE LA RECHERCHE LÉGALE CLAUDE")
    print(f"📝 Question: {test_question}")
    
    try:
        result = await client.chat(test_question)
        
        print(f"\n📋 RÉSULTATS CLAUDE:")
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
    asyncio.run(test_claude_legal_system())