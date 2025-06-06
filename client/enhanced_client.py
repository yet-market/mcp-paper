#!/usr/bin/env python3
"""
Luxembourg Legal Research Client - Enhanced Edition
Showcases professional legal research capabilities using the enhanced MCP server.
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


class EnhancedLegalClient:
    """Enhanced client showcasing professional Luxembourg legal research capabilities."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.model = "claude-3-5-sonnet-20241022"  # Use Sonnet for better analysis
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
        
        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Enhanced system prompt for professional legal research
        self.system_prompt = """Vous êtes un assistant juridique expert en droit luxembourgeois avec accès à un système avancé de recherche légale.

🎯 SYSTÈME ENHANCED MCP - CAPACITÉS PROFESSIONNELLES:

Vous disposez de 18 outils avancés pour la recherche légale professionnelle:

== OUTILS DE BASE ==

1. 🏛️ identify_legal_domain
   → Identifie le domaine juridique avec métadonnées enrichies
   → Retourne: domaine, mots-clés, types de documents, autorités compétentes

2. 🔍 smart_legal_search  
   → Recherche avec mots-clés juridiques PRÉCIS (éviter termes généraux)
   → Choisir des termes juridiques spécifiques selon le contexte légal
   → Exploite les relations JOLUX + score de pertinence JOLUX-optimisé

3. 🔍 multi_field_legal_search  
   → Recherche multi-champs simultanée (titre + relations + autorité)
   → Version optimisée pour mots-clés simples
   → Trouve 50-500 documents avec métadonnées complètes

4. 🔗 discover_legal_relationships
   → Découvre les chaînes d'amendements et relations juridiques
   → Suit les relations transitives (jolux:basedOn+)
   → Identifie: fondation légale, implémentations, amendements

4. 📅 temporal_legal_analysis
   → Analyse temporelle multi-dates pour validation de la validité légale
   → Utilise: dateDocument, publicationDate, dateEntryInForce
   → Évalue: documents actuels vs. historiques

5. ⚖️ assess_legal_authority
   → Classement par hiérarchie légale luxembourgeoise
   → BaseAct > Act > Memorial > LegalResource > NationalLegalResource
   → Intègre: autorité de publication + ancienneté

6. 📄 extract_document_content
   → Extraction de contenu réel (HTML/PDF luxembourgeois)
   → Analyse structure légale (articles, chapitres, sections)
   → Concepts juridiques détectés automatiquement

== NOUVEAUX OUTILS D'INTELLIGENCE JURIDIQUE ==

7. 🔗 analyze_citation_network
   → Analyse complète du réseau de citations (75K+ relations)
   → Découvre les précédents juridiques et références croisées
   → Profondeur d'analyse configurable (1-2 niveaux)

8. 📚 find_citing_documents
   → Trouve les documents qui citent une loi spécifique
   → Utilise jolux:cites (75,123 relations de citation)
   → Identifie l'influence juridique d'un texte

9. 📖 find_cited_documents
   → Trouve les documents cités par une loi spécifique
   → Découvre les fondements juridiques et autorités
   → Trace les sources légales

10. 📝 analyze_amendment_chain
    → Analyse complète de l'historique d'amendements
    → Utilise jolux:modifies/modifiedBy (26K+ modifications)
    → Timeline chronologique des modifications

11. 🕐 find_latest_amendments
    → Trouve les amendements les plus récents
    → Validation de la version actuelle d'une loi
    → Suivi des changements législatifs

12. 💰 check_legal_currency
    → Vérifie si un document est encore juridiquement valide
    → Utilise jolux:repeals (17,910 relations d'abrogation)
    → Statut: CURRENT ou REPEALED avec détails

13. 🔄 analyze_replacement_chain
    → Analyse les chaînes de remplacement/abrogation
    → Que cette loi abroge vs. ce qui l'abroge
    → Position dans la chaîne de remplacement

14. 📋 find_consolidated_versions
    → Trouve les versions consolidées officielles
    → Utilise jolux:consolidates (368 consolidations)
    → Textes officiels à jour

15. 🌍 find_multilingual_versions
    → Trouve les versions dans différentes langues
    → Utilise jolux:language (238K+ versions linguistiques)
    → Support français, allemand, anglais

16. ⚡ get_current_effective_version
    → Détermine la version effective actuelle recommandée
    → Combine consolidation + multilingue + validité
    → Recommandation pour la pratique juridique

17. 📋 get_enhanced_workflow_guidance
    → Guide des workflows professionnels optimaux
    → 3 workflows spécialisés disponibles

🔄 WORKFLOWS PROFESSIONNELS DISPONIBLES:

== WORKFLOW 1: RECHERCHE LÉGALE COMPLÈTE ==
1. identify_legal_domain → domaine + guidance
2. smart_legal_search → découverte intelligente multi-mots
3. discover_legal_relationships → relations de base
4. analyze_citation_network → réseau de précédents 
5. analyze_amendment_chain → historique des modifications
6. check_legal_currency → validation de validité
7. find_consolidated_versions → versions officielles
8. extract_document_content → contenu légal réel

== WORKFLOW 2: INTELLIGENCE RELATIONNELLE ==
1. smart_legal_search → documents de base
2. analyze_citation_network → réseau de citations complet
3. find_citing_documents → qui référence ces lois
4. find_cited_documents → fondements juridiques
5. analyze_amendment_chain → évolution législative
6. analyze_replacement_chain → chaînes d'abrogation

== WORKFLOW 3: VALIDITÉ ET VERSIONS ==
1. smart_legal_search → documents pertinents
2. check_legal_currency → validation de validité
3. find_latest_amendments → modifications récentes
4. find_consolidated_versions → versions consolidées
5. find_multilingual_versions → versions linguistiques
6. get_current_effective_version → recommandation finale

💡 NOUVELLES CAPACITÉS D'INTELLIGENCE JURIDIQUE:

- RÉSEAU DE CITATIONS: 75,123 relations de citation analysables
- CHAÎNES D'AMENDEMENTS: 26,826 modifications + 578 liens inverses
- VALIDATION DE VALIDITÉ: 17,910 relations d'abrogation
- VERSIONS CONSOLIDÉES: 368 consolidations officielles  
- SUPPORT MULTILINGUE: 238,518 versions linguistiques
- ANALYSE RELATIONNELLE: Réseaux de précédents juridiques
- VALIDITÉ JURIDIQUE: Vérification automatique du statut légal
- VERSIONS EFFECTIVES: Recommandations pour la pratique

⚖️ STANDARDS JURIDIQUES PROFESSIONNELS:

- Hiérarchie légale: Actes de base > Lois > Règlements > Décisions administratives
- Autorité: Parlement > Ministère > Administration
- Validité: Documents actuels > non-abrogés > versions consolidées
- Sources: Documents officiels avec URIs légaux complets + validation de validité
- Réseau: Citations bidirectionnelles + chaînes d'amendements complètes

🎯 EXEMPLES D'UTILISATION OPTIMALE:

== STRATÉGIE DE RECHERCHE JURIDIQUE ==
- identify_legal_domain → Analyse la question et extrait les termes juridiques
- Choisir des mots-clés PRÉCIS selon le domaine juridique identifié
- ÉVITER: termes généraux comme "création", "obligations", "procédures"
- PRIVILÉGIER: termes juridiques spécifiques selon le contexte (entités légales, concepts précis)
- analyze_citation_network → Réseau de lois SARL interconnectées
- analyze_amendment_chain → Évolution du droit SARL 2016-2025
- check_legal_currency → Confirmation validité actuelle
- find_consolidated_versions → Texte SARL consolidé officiel
- extract_document_content → Articles 175-218 + procédures actuelles

== Pour analyse de précédents juridiques ==
- smart_legal_search → Documents de jurisprudence
- find_citing_documents → Qui cite cette décision
- analyze_citation_network → Réseau de précédents (2 niveaux)
- find_cited_documents → Autorités juridiques invoquées

RÉPONDEZ TOUJOURS EN FRANÇAIS avec une analyse juridique professionnelle complète."""

        self.available_tools = []
        self._tools_initialized = False
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.query_count = 0
    
    async def initialize_tools(self):
        """Initialize enhanced MCP tools."""
        if self._tools_initialized:
            return
        
        logger.info("🔧 Initializing Enhanced MCP Tools...")
        try:
            # Always use HTTP transport for real MCP server connection
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
            logger.info(f"✅ Initialized {len(self.available_tools)} enhanced tools")
            
            # Display available tools
            print("\n🔧 ENHANCED MCP TOOLS AVAILABLE:")
            for tool in self.available_tools:
                print(f"   • {tool['name']}: {tool['description']}")
            print()
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP tools: {e}")
            self.available_tools = []
    
    async def call_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool and return result."""
        try:
            # Always use HTTP transport for real MCP server connection
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
        """Format tool execution result for Claude with enhanced display."""
        if not tool_result["success"]:
            return f"❌ Erreur lors de l'exécution de l'outil {tool_result['tool_name']}: {tool_result['error']}"
        
        result = tool_result["result"]
        tool_name = tool_result["tool_name"]
        
        # Enhanced formatting for each tool type
        if tool_name == "smart_legal_search":
            if isinstance(result, dict):
                doc_count = result.get("total_found", 0)
                keywords_used = result.get("keywords_used", [])
                keywords_original = result.get("keywords_original", "")
                return f"🧠 RECHERCHE INTELLIGENTE: {doc_count} documents trouvés\nMots-clés extraits: {keywords_used}\nRecherche originale: '{keywords_original}'\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "multi_field_legal_search":
            if isinstance(result, dict):
                doc_count = result.get("total_found", 0)
                search_method = result.get("search_method", "unknown")
                return f"🔍 RECHERCHE MULTI-CHAMPS: {doc_count} documents trouvés via {search_method}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "discover_legal_relationships":
            if isinstance(result, dict):
                rel_count = result.get("total_relationships", 0)
                rel_types = result.get("relationship_types_found", [])
                return f"🔗 RELATIONS JURIDIQUES: {rel_count} relations trouvées\nTypes: {', '.join(rel_types)}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "temporal_legal_analysis":
            if isinstance(result, dict) and "temporal_analysis" in result:
                analysis = result["temporal_analysis"]
                current = len(analysis.get("current_documents", []))
                recent = len(analysis.get("recent_documents", []))
                historical = len(analysis.get("historical_documents", []))
                return f"📅 ANALYSE TEMPORELLE: {current} actuels, {recent} récents, {historical} historiques\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "assess_legal_authority":
            if isinstance(result, dict):
                top_count = result.get("top_selected", 0)
                method = result.get("authority_analysis", {}).get("assessment_method", "unknown")
                return f"⚖️ AUTORITÉ LÉGALE: {top_count} documents classés par {method}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        # NEW LEGAL INTELLIGENCE TOOLS FORMATTING
        elif tool_name == "analyze_citation_network":
            if isinstance(result, dict):
                total_network = result.get("total_network_size", 0)
                inbound = result.get("inbound_citations", {}).get("citation_count", 0)
                outbound = result.get("outbound_citations", {}).get("citation_count", 0)
                return f"🔗 RÉSEAU DE CITATIONS: {total_network} connexions totales ({inbound} entrants, {outbound} sortants)\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "find_citing_documents":
            if isinstance(result, dict):
                count = result.get("citation_count", 0)
                return f"📚 DOCUMENTS CITANTS: {count} documents citent ce texte\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "find_cited_documents":
            if isinstance(result, dict):
                count = result.get("citation_count", 0)
                return f"📖 DOCUMENTS CITÉS: {count} documents cités par ce texte\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "analyze_amendment_chain":
            if isinstance(result, dict):
                total_mods = result.get("total_modifications", 0)
                total_docs_mod = result.get("total_documents_modified", 0)
                activity = result.get("amendment_activity_level", "unknown")
                return f"📝 CHAÎNE D'AMENDEMENTS: {total_mods} modifications reçues, {total_docs_mod} documents modifiés (activité: {activity})\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "find_latest_amendments":
            if isinstance(result, dict):
                count = result.get("amendment_count", 0)
                return f"🕐 AMENDEMENTS RÉCENTS: {count} amendements récents trouvés\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "check_legal_currency":
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                is_current = result.get("is_legally_current", None)
                status_msg = result.get("status_message", "")
                return f"💰 VALIDITÉ LÉGALE: {status} - {status_msg}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "analyze_replacement_chain":
            if isinstance(result, dict):
                repeals_made = result.get("total_repeals_made", 0)
                repeals_received = result.get("total_repeals_received", 0)
                position = result.get("chain_position", "unknown")
                return f"🔄 CHAÎNE DE REMPLACEMENT: {repeals_made} abrogations, {repeals_received} abrogé par (position: {position})\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "find_consolidated_versions":
            if isinstance(result, dict):
                count = result.get("consolidation_count", 0)
                return f"📋 VERSIONS CONSOLIDÉES: {count} versions consolidées trouvées\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "find_multilingual_versions":
            if isinstance(result, dict):
                lang_count = result.get("language_count", 0)
                languages = result.get("languages_available", [])
                return f"🌍 VERSIONS MULTILINGUES: {lang_count} langues ({', '.join(languages[:3])}{'...' if len(languages) > 3 else ''})\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        elif tool_name == "get_current_effective_version":
            if isinstance(result, dict):
                recommendation = result.get("recommendation_reason", "unknown")
                return f"⚡ VERSION EFFECTIVE: {recommendation}\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        
        # Default formatting
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
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            except (TypeError, AttributeError):
                return str(result)
    
    async def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Enhanced chat with professional legal research workflow."""
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
        
        # Track tool usage with enhanced metadata
        tools_used = []
        tool_results = []
        workflow_stage = "initialization"
        max_iterations = 20  # Allow for complete legal intelligence workflow with new tools
        iteration = 0
        
        print(f"\n🧠 DÉMARRAGE RECHERCHE LÉGALE PROFESSIONNELLE")
        print(f"📝 Question: {message}")
        print(f"🔧 Outils disponibles: {len(self.available_tools)}")
        print("=" * 80)
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Prepare request for Claude
                request_params = {
                    "model": self.model,
                    "max_tokens": 4000,  # Increased for complex legal analysis
                    "temperature": 0.3,  # Lower for more precise legal analysis
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
                    
                    # Execute tools with enhanced logging
                    tool_results_for_claude = []
                    
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_use_id = content_block.id
                            
                            print(f"\n🔧 EXÉCUTION OUTIL: {tool_name}")
                            print(f"📥 Paramètres: {json.dumps(tool_input, ensure_ascii=False)}")
                            
                            # Update workflow stage
                            if tool_name == "identify_legal_domain":
                                workflow_stage = "domain_identification"
                            elif tool_name in ["smart_legal_search", "multi_field_legal_search"]:
                                workflow_stage = "comprehensive_search"
                            elif tool_name == "discover_legal_relationships":
                                workflow_stage = "relationship_analysis"
                            elif tool_name == "temporal_legal_analysis":
                                workflow_stage = "currency_validation"
                            elif tool_name == "assess_legal_authority":
                                workflow_stage = "authority_ranking"
                            elif tool_name == "extract_document_content":
                                workflow_stage = "content_extraction"
                            # NEW LEGAL INTELLIGENCE WORKFLOW STAGES
                            elif tool_name == "analyze_citation_network":
                                workflow_stage = "citation_network_analysis"
                            elif tool_name in ["find_citing_documents", "find_cited_documents"]:
                                workflow_stage = "citation_discovery"
                            elif tool_name in ["analyze_amendment_chain", "find_latest_amendments"]:
                                workflow_stage = "amendment_analysis"
                            elif tool_name in ["check_legal_currency", "analyze_replacement_chain"]:
                                workflow_stage = "legal_currency_validation"
                            elif tool_name in ["find_consolidated_versions", "find_multilingual_versions", "get_current_effective_version"]:
                                workflow_stage = "version_analysis"
                            elif tool_name == "get_enhanced_workflow_guidance":
                                workflow_stage = "workflow_guidance"
                            
                            # Execute tool via MCP
                            tool_result = await self.call_mcp_tool(tool_name, tool_input)
                            
                            tools_used.append({
                                "name": tool_name,
                                "stage": workflow_stage,
                                "iteration": iteration
                            })
                            tool_results.append(tool_result)
                            
                            # Format result for Claude
                            formatted_result = self.format_tool_result(tool_result)
                            
                            print(f"📤 Résultat: {formatted_result[:200]}{'...' if len(formatted_result) > 200 else ''}")
                            
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
                    input_cost = (self.total_input_tokens / 1_000_000) * 3.0  # Sonnet pricing
                    output_cost = (self.total_output_tokens / 1_000_000) * 15.0
                    total_cost = input_cost + output_cost
                    
                    # Enhanced workflow summary
                    workflow_summary = {
                        "total_tools_used": len(tools_used),
                        "workflow_stages_completed": list(set([tool["stage"] for tool in tools_used])),
                        "research_depth": "professional" if len(tools_used) >= 4 else "basic",
                        "final_stage": workflow_stage
                    }
                    
                    print(f"\n✅ RECHERCHE LÉGALE TERMINÉE")
                    print(f"🔧 Outils utilisés: {len(tools_used)}")
                    print(f"🎯 Étapes: {', '.join(workflow_summary['workflow_stages_completed'])}")
                    print(f"⚖️ Niveau: {workflow_summary['research_depth']}")
                    print(f"💰 Coût estimé: ${total_cost:.4f}")
                    print("=" * 80)
                    
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "tool_results": tool_results,
                        "workflow_summary": workflow_summary,
                        "conversation": messages,
                        "model_used": self.model,
                        "iterations": iteration,
                        "cost_info": {
                            "input_tokens": getattr(response.usage, 'input_tokens', 0) if hasattr(response, 'usage') else 0,
                            "output_tokens": getattr(response.usage, 'output_tokens', 0) if hasattr(response, 'usage') else 0,
                            "estimated_cost_usd": round(total_cost, 6),
                            "processing_time_ms": round(processing_time * 1000, 2)
                        },
                        "provider": "anthropic_api_enhanced"
                    }
            
            except Exception as e:
                logger.error(f"❌ Anthropic API error: {e}")
                return {
                    "response": f"Erreur de service Anthropic: {str(e)}",
                    "tools_used": tools_used,
                    "tool_results": tool_results,
                    "error": str(e),
                    "provider": "anthropic_api_enhanced"
                }
        
        # Max iterations reached
        return {
            "response": "Recherche légale complexe interrompue (limite d'itérations atteinte).",
            "tools_used": tools_used,
            "tool_results": tool_results,
            "warning": "Max iterations reached",
            "provider": "anthropic_api_enhanced"
        }
    
    def display_enhanced_capabilities(self):
        """Display the enhanced system capabilities."""
        print("\n🚀 SYSTÈME DE RECHERCHE LÉGALE LUXEMBOURGEOISE - INTELLIGENCE JURIDIQUE")
        print("=" * 90)
        print("📊 CAPACITÉS D'INTELLIGENCE JURIDIQUE PROFESSIONNELLE:")
        print("   • Recherche multi-champs simultanée (titre + relations + autorité)")
        print("   • Analyse de réseaux de citations (75,123 relations)")
        print("   • Découverte automatique de chaînes d'amendements (26,826+ modifications)")
        print("   • Validation de validité légale en temps réel (17,910 abrogations)")
        print("   • Versions consolidées officielles (368 consolidations)")
        print("   • Support multilingue complet (238,518 versions linguistiques)")
        print("   • Classement par hiérarchie juridique luxembourgeoise")
        print("   • Extraction de contenu réel HTML/PDF")
        print("   • Intégration du droit européen (transposition)")
        print()
        print("⚖️ NOUVELLES CAPACITÉS D'INTELLIGENCE:")
        print("   • RÉSEAU DE CITATIONS: Précédents juridiques et références croisées")
        print("   • CHAÎNES D'AMENDEMENTS: Évolution législative complète")
        print("   • VALIDITÉ JURIDIQUE: Statut légal actuel automatique")
        print("   • VERSIONS EFFECTIVES: Recommandations pour la pratique")
        print("   • ANALYSE RELATIONNELLE: Interconnexions juridiques bidirectionnelles")
        print()
        print("⚖️ STANDARDS JURIDIQUES RENFORCÉS:")
        print("   • BaseAct > Act > Memorial > Regulation > Administrative")
        print("   • Parlement > Ministère > Administration")
        print("   • Documents actuels > non-abrogés > versions consolidées")
        print("   • Validation automatique de validité légale")
        print()
        print("🔍 PERFORMANCE PROFESSIONNELLE:")
        print("   • 17 outils spécialisés (vs. 6 auparavant)")
        print("   • 50-500 documents par recherche avec métadonnées complètes")
        print("   • Relations juridiques complètes découvertes automatiquement")
        print("   • Validité légale confirmée en temps réel")
        print("   • Réseaux de citations et précédents analysés")
        print("   • Versions consolidées et multilingues identifiées")
        print("   • 3 workflows professionnels spécialisés")
        print("=" * 90)


# Test function for enhanced capabilities
async def test_enhanced_system():
    """Test the enhanced legal research system."""
    client = EnhancedLegalClient()
    
    # Display capabilities
    client.display_enhanced_capabilities()
    
    # Test with a complex legal question
    test_question = "Comment créer une SARL au Luxembourg? Quelles sont les obligations légales et procédures actuelles? Analysez aussi l'évolution législative et les versions consolidées."
    
    print(f"\n🧪 TEST DU SYSTÈME D'INTELLIGENCE JURIDIQUE")
    print(f"📝 Question test: {test_question}")
    print(f"🎯 Test des nouvelles capacités: citations, amendements, validité, consolidation")
    
    try:
        result = await client.chat(test_question)
        
        print(f"\n📋 RÉSULTATS DU TEST:")
        print(f"✅ Réponse générée: {len(result['response'])} caractères")
        print(f"🔧 Outils utilisés: {len(result.get('tools_used', []))}")
        print(f"🎯 Étapes workflow: {result.get('workflow_summary', {}).get('workflow_stages_completed', [])}")
        print(f"💰 Coût: ${result.get('cost_info', {}).get('estimated_cost_usd', 0):.4f}")
        
        # Display partial response
        response_preview = result['response'][:500] + "..." if len(result['response']) > 500 else result['response']
        print(f"\n📄 APERÇU DE LA RÉPONSE:")
        print(response_preview)
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")


if __name__ == "__main__":
    asyncio.run(test_enhanced_system())