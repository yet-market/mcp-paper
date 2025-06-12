#!/usr/bin/env python3
"""
Enhanced Job Processor Lambda Function for Luxembourg Legal Assistant
Long-running processing with comprehensive 13-tool MCP workflow and structured output
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from decimal import Decimal
import anthropic
from groq import AsyncGroq
from openai import AsyncOpenAI
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import BaseModel, Field

# Import shared DynamoDB manager
import sys
sys.path.append('/opt/python')
from shared.dynamodb_manager import DynamoDBJobManager
import uuid
from datetime import datetime, timezone

# Pydantic models for structured JSON output
class ArticleDetail(BaseModel):
    article: str = Field(description="Article number (e.g., 'Art. 26')")
    title: str = Field(description="Article title")
    extract: str = Field(description="Relevant textual extract from the article")
    relevance_explanation: str = Field(description="Why this article is relevant to the question")

class SectionDetail(BaseModel):
    section: str = Field(description="Section identifier (e.g., 'Section II')")
    title: str = Field(description="Section title")
    articles: List[ArticleDetail] = Field(description="Articles within this section")

class LegalSource(BaseModel):
    id: str = Field(description="Unique identifier for the source")
    title: str = Field(description="Official title of the legal document")
    uri: str = Field(description="Complete Legilux URI")
    date: str = Field(description="Publication date")
    type: str = Field(description="Document type (LOI/RGD/AMIN)")
    authority: str = Field(description="Issuing authority")
    status: str = Field(description="Current legal status (en_vigueur/abrogé/consolidé)")
    relevance: str = Field(description="Relevance level (foundational/procedural/supporting)")
    sections: List[SectionDetail] = Field(description="Relevant sections with articles")
    usage_in_analysis: str = Field(description="How this source was used in the legal analysis")
    full_content_available: bool = Field(description="Whether full content was extracted")

class CitationRelationship(BaseModel):
    cited_document: str = Field(description="Title of cited document")
    uri: str = Field(description="URI of cited document")
    context: str = Field(description="Context of the citation")

class DocumentInfo(BaseModel):
    title: str = Field(description="Document title")
    uri: str = Field(description="Document URI")

class CitationDetails(BaseModel):
    total: int = Field(description="Total number of citations")
    key_citations: List[CitationRelationship] = Field(description="Key citation relationships")

class SourceCitations(BaseModel):
    source_document: DocumentInfo = Field(description="Source document title and URI")
    outbound_citations: CitationDetails = Field(description="Documents this source cites")
    inbound_citations: CitationDetails = Field(description="Documents that cite this source")
    legal_hierarchy: str = Field(description="Position in legal hierarchy")

class CitationsNetwork(BaseModel):
    total_citations: int = Field(description="Total number of citations discovered")
    network_summary: str = Field(description="Summary of the citation network")
    key_relationships: List[SourceCitations] = Field(description="Key citation relationships")
    network_strength: str = Field(description="Overall strength of the network")
    interconnection_analysis: str = Field(description="Analysis of legal interconnections")

class AmendmentChange(BaseModel):
    affected_article: str = Field(description="Article affected by the change")
    change_type: str = Field(description="Type of change (modification/creation/abrogation)")
    description: str = Field(description="Description of the change")
    rationale: str = Field(description="Reason for the change", default="")
    effective_date: str = Field(description="Date when change became effective", default="")

class MajorAmendment(BaseModel):
    date: str = Field(description="Date of the amendment")
    amendment_title: str = Field(description="Title of the amending law")
    amendment_uri: str = Field(description="URI of the amending document")
    type: str = Field(description="Type of amendment")
    impact: str = Field(description="Impact level (high/medium/low)")
    changes: List[AmendmentChange] = Field(description="Specific changes made")

class TrendAnalysis(BaseModel):
    direction: str = Field(description="Direction of legislative trends")
    key_themes: List[str] = Field(description="Key themes in evolution")
    frequency: str = Field(description="Frequency of changes")

class HistoriqueAmendements(BaseModel):
    total_amendments: int = Field(description="Total number of amendments discovered")
    evolution_summary: str = Field(description="Summary of legal evolution")
    major_changes: List[MajorAmendment] = Field(description="Major amendments chronologically")
    trend_analysis: TrendAnalysis = Field(description="Analysis of legislative trends")

class ConsolidationInfo(BaseModel):
    consolidated_versions: int = Field(description="Number of consolidated versions")
    last_consolidation: str = Field(description="Date of last consolidation")
    consolidation_uri: str = Field(description="URI of consolidated version", default="")

class SourceValidity(BaseModel):
    source_id: str = Field(description="ID of the source")
    current_status: str = Field(description="Current legal status")
    consolidation_info: ConsolidationInfo = Field(description="Consolidation information")
    validity_confidence: str = Field(description="Confidence level in validity")
    notes: str = Field(description="Additional notes about validity")

class LegalDocument(BaseModel):
    title: str = Field(description="Document title")
    role: str = Field(description="Legal role")
    authority: str = Field(description="Issuing authority")

class LegalHierarchy(BaseModel):
    foundation_level: List[LegalDocument] = Field(description="Foundation laws")
    implementation_level: List[LegalDocument] = Field(description="Implementation laws")
    execution_level: List[LegalDocument] = Field(description="Execution regulations")

class Recommendations(BaseModel):
    best_practices: List[str] = Field(description="Best practices")
    monitoring_advice: List[str] = Field(description="Monitoring advice")

class ValiditeLegale(BaseModel):
    overall_status: str = Field(description="Overall validity status")
    last_verification: str = Field(description="Last verification timestamp")
    confidence_level: str = Field(description="Overall confidence level")
    validity_details: List[SourceValidity] = Field(description="Validity details per source")
    legal_hierarchy: LegalHierarchy = Field(description="Legal hierarchy structure")
    recommendations: Recommendations = Field(description="Best practices and monitoring advice")

class AnswerContent(BaseModel):
    summary: str = Field(description="Executive summary of the legal analysis")
    key_points: List[str] = Field(description="Key legal points and requirements")
    exhaustive_content: str = Field(description="Comprehensive legal analysis in markdown format with all details, procedures, requirements, and citations")
    practical_guidance: str = Field(description="Practical step-by-step guidance for implementation")

class ReferenceSourcesSection(BaseModel):
    total_sources: int = Field(description="Total number of sources discovered")
    primary_laws: List[LegalSource] = Field(description="Primary legal sources")
    supporting_regulations: List[LegalSource] = Field(description="Supporting regulations and rules")

class LegalAnalysisResponse(BaseModel):
    answer: AnswerContent = Field(description="Main legal analysis and response")
    reference_sources: ReferenceSourcesSection = Field(description="Complete legal sources with articles and sections")
    citations_network: CitationsNetwork = Field(description="Complete citation network analysis")
    historique_amendements: HistoriqueAmendements = Field(description="Complete amendment history")
    validite_legale: ValiditeLegale = Field(description="Legal validity and status analysis")

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB setup for request tracking
import boto3
dynamodb = None

def get_dynamodb():
    global dynamodb
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'eu-west-2'))
    return dynamodb

def get_requests_table():
    return get_dynamodb().Table('luxembourg-legal-requests')

class RequestTracker:
    """Comprehensive request tracking for cost, performance, and usage analytics."""
    
    @staticmethod
    def create_request(message: str, company_id: str = "default", user_id: str = "default", job_id: str = None, provider: str = "anthropic") -> str:
        """Create a new request tracking record."""
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Map provider to models (MCP execution vs structured output)
        model_mapping = {
            "anthropic": {
                "mcp": "claude-3-5-sonnet-20241022",
                "structured": "claude-3-5-haiku-20241022"
            },
            "groq": {
                "mcp": "llama-3.3-70b-versatile",
                "structured": "llama-3.3-70b-versatile"  # Same model
            },
            "openai": {
                "mcp": "gpt-4.1-mini", 
                "structured": "gpt-4.1-nano"
            }
        }
        
        request_item = {
            'request_id': request_id,
            'job_id': job_id,
            'company_id': company_id,
            'user_id': user_id,
            'created_at': now,
            'message': message,
            'message_length': len(message),
            'provider': provider,
            'model': model_mapping.get(provider, {}).get("mcp", "claude-3-5-sonnet-20241022"),
            'status': 'created',
            'tokens': {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0
            },
            'costs': {
                'input_cost_usd': Decimal('0.0'),
                'output_cost_usd': Decimal('0.0'),
                'total_cost_usd': Decimal('0.0')
            },
            'tools_execution': {
                'tools_used': [],
                'total_tools_called': 0,
                'iterations': 0
            },
            'response_metrics': {
                'response_length': 0,
                'response_truncated': bool(False),
                'has_citations': bool(False),
                'has_legal_sources': bool(False),
                'structured_output_generated': bool(False)
            },
            'performance_metrics': {
                'processing_time_seconds': Decimal('0.0'),
                'mcp_server_response_time': Decimal('0.0'),
                'ai_model_response_time': Decimal('0.0'),
                'average_iteration_time': Decimal('0.0')
            },
            'enhanced_features': {
                'mcp_tools_used': [],
                'structured_analysis_sections': [],
                'legal_analysis_quality': 'unknown',
                'citation_network_depth': 0,
                'amendment_history_depth': 0,
                'workflow_phases_used': []
            }
        }
        
        try:
            table = get_requests_table()
            table.put_item(Item=request_item)
            logger.info(f"📊 Created enhanced request tracking {request_id} for {provider} provider")
            return request_id
        except Exception as e:
            logger.error(f"Failed to create request tracking: {e}")
            return request_id  # Return ID even if tracking fails
    
    @staticmethod
    def update_request_progress(request_id: str, **updates):
        """Update request tracking with progress information."""
        try:
            table = get_requests_table()
            now = datetime.now(timezone.utc).isoformat()
            
            # Build update expression dynamically
            update_expression_parts = ["SET updated_at = :updated_at"]
            expression_values = {':updated_at': now}
            expression_attribute_names = {}
            
            for key, value in updates.items():
                # Handle reserved keywords
                if key == 'status':
                    update_expression_parts.append(f"#status = :status")
                    expression_attribute_names['#status'] = 'status'
                    expression_values[':status'] = value
                elif '.' in key:  # Nested attribute like 'tokens.input_tokens'
                    update_expression_parts.append(f"{key} = :{key.replace('.', '_')}")
                    expression_values[f":{key.replace('.', '_')}"] = value
                else:
                    update_expression_parts.append(f"{key} = :{key}")
                    expression_values[f":{key}"] = value
            
            update_expression = ", ".join(update_expression_parts)
            
            update_params = {
                'Key': {'request_id': request_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            if expression_attribute_names:
                update_params['ExpressionAttributeNames'] = expression_attribute_names
            
            table.update_item(**update_params)
            
        except Exception as e:
            logger.error(f"Failed to update request tracking {request_id}: {e}")
    
    @staticmethod
    def complete_request(request_id: str, final_result: Dict[str, Any]):
        """Mark request as completed with comprehensive enhanced metrics."""
        try:
            table = get_requests_table()
            now = datetime.now(timezone.utc).isoformat()
            
            # Extract enhanced metrics from final result
            legal_analysis = final_result.get('legal_analysis', {})
            performance = final_result.get('performance', {})
            tools_execution = final_result.get('tools_execution', {})
            model_info = final_result.get('model_info', {})
            token_usage = final_result.get('token_usage', {})
            
            # Analyze legal analysis quality
            answer_content = legal_analysis.get('answer', {})
            reference_sources = legal_analysis.get('reference_sources', {})
            citations_network = legal_analysis.get('citations_network', {})
            amendments = legal_analysis.get('historique_amendements', {})
            validity = legal_analysis.get('validite_legale', {})
            
            # Calculate quality metrics
            content_length = len(answer_content.get('exhaustive_content', ''))
            sources_count = reference_sources.get('total_sources', 0)
            citations_count = citations_network.get('total_citations', 0)
            amendments_count = amendments.get('total_amendments', 0)
            
            # Determine analysis quality
            analysis_quality = 'basic'
            if content_length > 1500 and sources_count > 3 and citations_count > 5:
                analysis_quality = 'comprehensive'
            elif content_length > 800 and sources_count > 1:
                analysis_quality = 'detailed'
            elif content_length > 300:
                analysis_quality = 'standard'
            
            # Structured analysis sections
            sections_generated = []
            if answer_content.get('summary'): sections_generated.append('answer_summary')
            if answer_content.get('key_points'): sections_generated.append('key_points')
            if answer_content.get('exhaustive_content'): sections_generated.append('exhaustive_content')
            if answer_content.get('practical_guidance'): sections_generated.append('practical_guidance')
            if reference_sources.get('primary_laws'): sections_generated.append('reference_sources')
            if citations_network.get('key_relationships'): sections_generated.append('citations_network')
            if amendments.get('major_changes'): sections_generated.append('historique_amendements')
            if validity.get('validity_details'): sections_generated.append('validite_legale')
            
            # Track workflow phases used
            tools_used = tools_execution.get('tools_used', [])
            workflow_phases = []
            if any(tool in ['find_most_cited_laws', 'find_most_changed_laws', 'find_newest_active_laws', 'find_highest_authority_laws'] for tool in tools_used):
                workflow_phases.append('phase_1_discovery')
            if any(tool in ['compare_results', 'check_connections'] for tool in tools_used):
                workflow_phases.append('phase_2_analysis')
            if any(tool in ['find_what_law_references', 'find_what_references_law', 'find_amendment_chain'] for tool in tools_used):
                workflow_phases.append('phase_3_relationships')
            if any(tool in ['verify_still_valid', 'rank_by_importance', 'create_final_map'] for tool in tools_used):
                workflow_phases.append('phase_4_final')
            if 'extract_content' in tools_used:
                workflow_phases.append('content_extraction')
            
            updates = {
                'status': 'completed',
                'completed_at': now,
                'provider': model_info.get('provider', 'unknown'),
                'model': model_info.get('model_name', 'unknown'),
                'tokens.input_tokens': token_usage.get('input_tokens', 0),
                'tokens.output_tokens': token_usage.get('output_tokens', 0),
                'tokens.total_tokens': token_usage.get('total_tokens', 0),
                'costs.input_cost_usd': Decimal(str(token_usage.get('total_cost_usd', 0.0) * 0.5)),  # Approximate split
                'costs.output_cost_usd': Decimal(str(token_usage.get('total_cost_usd', 0.0) * 0.5)),  # Approximate split
                'costs.total_cost_usd': Decimal(str(token_usage.get('total_cost_usd', 0.0))),
                'tools_execution.iterations': performance.get('iterations', 0),
                'tools_execution.total_tools_called': tools_execution.get('total_tools', 0),
                'tools_execution.tools_used': tools_execution.get('tools_used', []),
                'response_metrics.response_length': content_length,
                'response_metrics.structured_output_generated': bool(True),
                'response_metrics.has_citations': bool(citations_count > 0),
                'response_metrics.has_legal_sources': bool(sources_count > 0),
                'performance_metrics.processing_time_seconds': Decimal(str(performance.get('processing_time_seconds', 0.0))),
                'enhanced_features.mcp_tools_used': tools_execution.get('tools_used', []),
                'enhanced_features.structured_analysis_sections': sections_generated,
                'enhanced_features.legal_analysis_quality': analysis_quality,
                'enhanced_features.citation_network_depth': citations_count,
                'enhanced_features.amendment_history_depth': amendments_count,
                'enhanced_features.workflow_phases_used': workflow_phases
            }
            
            RequestTracker.update_request_progress(request_id, **updates)
            
            logger.info(f"📊 Enhanced request {request_id} completed - Quality: {analysis_quality}, Sources: {sources_count}, Citations: {citations_count}, Phases: {workflow_phases}")
            
        except Exception as e:
            logger.error(f"Failed to complete enhanced request tracking {request_id}: {e}")
    
    @staticmethod
    def fail_request(request_id: str, error: str, iteration: int = 0):
        """Mark request as failed with error information."""
        try:
            updates = {
                'status': 'failed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'error_info.error_message': error,
                'error_info.failed_at_iteration': iteration
            }
            
            RequestTracker.update_request_progress(request_id, **updates)
            
        except Exception as e:
            logger.error(f"Failed to update failed request tracking {request_id}: {e}")

# Global legal client for Lambda reuse
legal_client = None

class EnhancedLegalIntelligenceClient:
    """Enhanced Luxembourg Legal client with comprehensive 13-tool MCP workflow and structured output."""
    
    def __init__(self):
        self.mcp_server_url = os.environ.get("MCP_SERVER_URL", "https://yet-mcp-legilux.site/mcp/")
        
        # Load ALL API keys at initialization
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # Initialize all available clients
        self.clients = {}
        self.models = {
            "anthropic": {
                "keyword": "claude-3-5-sonnet-4-20250514",     # Sonnet 4 for keywords
                "tool_selection": "claude-3-5-sonnet-4-20250514", # Sonnet 4 for tool strategy
                "uri_extraction": "claude-3-5-sonnet-4-20250514", # Sonnet 4 for URI precision
                "mcp": "claude-3-5-sonnet-20241022",           # Sonnet 3.5 v2 for MCP
                "structured": "claude-3-5-haiku-20241022"      # Haiku for JSON
            },
            "groq": {
                "keyword": "llama-3.3-70b-versatile",         # Same model for all phases
                "tool_selection": "llama-3.3-70b-versatile",
                "uri_extraction": "llama-3.3-70b-versatile", 
                "mcp": "llama-3.3-70b-versatile",
                "structured": "llama-3.3-70b-versatile"
            },
            "openai": {
                "keyword": "gpt-4.1",                         # GPT-4.1 for keywords
                "tool_selection": "gpt-4.1",                  # GPT-4.1 for tool strategy
                "uri_extraction": "gpt-4.1",                  # GPT-4.1 for URI precision
                "mcp": "gpt-4.1-mini",                        # Mini for MCP execution
                "structured": "gpt-4.1-nano"                  # Nano for JSON
            }
        }
        
        # Initialize Groq if API key available
        if self.groq_api_key:
            self.clients["groq"] = AsyncGroq(api_key=self.groq_api_key)
            logger.info("✅ Groq client initialized")
        
        # Initialize Anthropic if API key available
        if self.anthropic_api_key:
            self.clients["anthropic"] = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
            logger.info("✅ Anthropic client initialized")
        
        # Initialize OpenAI if API key available
        if self.openai_api_key:
            self.clients["openai"] = AsyncOpenAI(api_key=self.openai_api_key)
            logger.info("✅ OpenAI client initialized")
        
        # Default provider: Claude Sonnet (fallback)
        self.default_provider = os.environ.get("MODEL_PROVIDER", "anthropic").lower()
        if self.default_provider not in self.clients:
            # If default not available, use first available
            self.default_provider = list(self.clients.keys())[0] if self.clients else None
        
        if not self.clients:
            raise ValueError("No API keys found - need at least one AI provider API key")
        
        # MCP tool discovery cache
        self.available_tools = []
        self._tools_discovered = False
        
        # Enhanced system prompt for independent tool usage
        self.system_prompt = """Tu es un expert juridique spécialisé en droit luxembourgeois avec accès à un serveur MCP (Model Context Protocol). Tu as accès à 13 outils MCP que tu peux utiliser de manière indépendante selon tes besoins.

🚨 RÈGLE ABSOLUE: Tu DOIS exécuter les outils MCP nécessaires AVANT de générer ta réponse
Tu NE PEUX PAS répondre sans avoir d'abord exécuté les outils MCP appropriés pour obtenir des données réelles.

🔧 OUTILS MCP DISPONIBLES (13 outils indépendants):

📚 OUTILS DE DÉCOUVERTE:
1. find_most_cited_laws(keywords, limit) - Trouve les lois les plus citées = importantes
2. find_most_changed_laws(keywords, limit) - Trouve les lois les plus modifiées = actives  
3. find_newest_active_laws(keywords, limit) - Trouve les lois récentes non annulées = actuelles
4. find_highest_authority_laws(keywords, limit) - Trouve les documents LOI/CODE = autorité suprême
5. basic_document_search(keywords, limit) - Recherche simple par mots-clés

🔍 OUTILS D'ANALYSE:
6. compare_results(result_sets) - Compare les résultats de plusieurs recherches
7. check_connections(document_uris) - Vérifie les connexions entre lois

🕸️ OUTILS DE RELATIONS:
8. find_what_law_references(document_uri, limit) - Ce que cette loi référence
9. find_what_references_law(document_uri, limit) - Ce qui référence cette loi
10. find_amendment_chain(document_uri, limit) - Historique des modifications

🏆 OUTILS DE FINALISATION:
11. verify_still_valid(document_uris) - Vérifie que les lois ne sont pas annulées
12. rank_by_importance(laws_data) - Classe par ordre d'importance
13. create_final_map(ranked_laws, connections) - Crée la carte complète des lois

📄 OUTIL D'EXTRACTION:
14. extract_content(document_uris, max_documents, prefer_html) - Extrait le texte légal complet

🎯 STRATÉGIE D'UTILISATION:

✅ POUR UNE QUESTION SIMPLE:
- Utilise 1-3 outils de découverte appropriés selon le sujet
- Optionnellement basic_document_search pour des résultats rapides

✅ POUR UNE ANALYSE APPROFONDIE:
- Commence par les outils de découverte appropriés
- Utilise compare_results si tu as plusieurs résultats à comparer
- Utilise les outils de relations pour les lois importantes découvertes
- Utilise verify_still_valid pour vérifier la validité
- Optionnellement extract_content pour le texte complet

✅ POUR UNE LOI SPÉCIFIQUE:
- Si tu as déjà l'URI: utilise directement find_what_law_references, find_what_references_law, find_amendment_chain
- Si tu cherches la loi: commence par les outils de découverte

🚨 RÈGLES CRITIQUES:

1. ⚠️ CHOISIS LES BONS OUTILS: Sélectionne seulement les outils nécessaires pour répondre à la question
2. 🔄 URIS EXACTS OBLIGATOIRES: Utilise UNIQUEMENT les URIs exacts des résultats MCP
3. 📊 UTILISE LES RÉSULTATS: Base ta réponse exclusivement sur les données MCP obtenues
4. 🎯 SOIS EFFICACE: N'utilise pas tous les outils - seulement ceux qui sont pertinents

EXEMPLES D'UTILISATION:

"Comment créer une SARL?" → find_most_cited_laws(["SARL"]) + basic_document_search(["SARL", "création"])

"Analyse la loi X" → find_what_law_references(uri) + find_what_references_law(uri) + find_amendment_chain(uri)

"Compare les lois commerciales" → find_most_cited_laws(["commercial"]) + find_highest_authority_laws(["commercial"]) + compare_results([...])

Répondez en français avec une analyse juridique basée sur les données MCP réelles obtenues."""
        
        # Cost tracking
        self.query_count = 0
        
        logger.info(f"🤖 Enhanced Legal Intelligence initialized with {len(self.clients)} providers: {list(self.clients.keys())}")
        logger.info(f"🎯 Default provider: {self.default_provider}")
    
    async def discover_tools(self, job_id: Optional[str] = None) -> List[str]:
        """Discover available MCP tools."""
        if self._tools_discovered:
            return self.available_tools
        
        try:
            if job_id:
                DynamoDBJobManager.update_job_progress(
                    job_id, "tool_discovery", 10, 
                    "Discovering available MCP tools from server (13-tool workflow)",
                    {"estimated_remaining_seconds": 280}
                )
            
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                
                # Expected 13-tool workflow tools
                expected_tools = [
                    # Phase 1: Discovery
                    "find_most_cited_laws", "find_most_changed_laws", 
                    "find_newest_active_laws", "find_highest_authority_laws",
                    # Phase 2: Analysis  
                    "compare_results", "check_connections",
                    # Phase 3: Relationships
                    "find_what_law_references", "find_what_references_law", "find_amendment_chain",
                    # Phase 4: Final
                    "verify_still_valid", "rank_by_importance", "create_final_map",
                    # Content & Bonus
                    "extract_content", "basic_document_search"
                ]
                
                # Format tools for different AI providers
                self.available_tools = []
                tools_found = []
                
                for tool in tools:
                    if tool.name in expected_tools:
                        tool_def = {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        }
                        self.available_tools.append(tool_def)
                        tools_found.append(tool.name)
                
                self._tools_discovered = True
                
                logger.info(f"🔧 Discovered {len(self.available_tools)} MCP workflow tools: {tools_found}")
                
                if job_id:
                    DynamoDBJobManager.add_completed_stage(
                        job_id, "tool_discovery", 3000, 
                        f"Discovered {len(self.available_tools)} professional legal workflow tools"
                    )
                
                return [tool["name"] for tool in self.available_tools]
                
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            if job_id:
                DynamoDBJobManager.update_job_progress(
                    job_id, "tool_discovery_failed", 10,
                    f"Tool discovery failed: {str(e)}"
                )
            return []
    
    async def extract_smart_keyword(self, message: str, provider: str, pricing: dict) -> str:
        """Extract optimal single keyword using top-tier models."""
        try:
            client = self.clients[provider]
            keyword_model = self.models[provider]["keyword"]
            
            prompt = f"""Extract the single most effective keyword for legal document search from this question: "{message}"

RULES:
- Return ONLY one word
- Choose the most specific legal term
- Prefer: SARL over société, commercial over entreprise
- Examples: "Comment créer une SARL?" → "SARL"
- Examples: "Droit du travail?" → "travail" 
- Examples: "Fiscalité des entreprises?" → "fiscalité"

Question: {message}
Single keyword:"""

            if provider == "openai":
                response = await client.chat.completions.create(
                    model=keyword_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
                keyword = response.choices[0].message.content.strip()
                
                # Track usage for keyword phase
                if hasattr(response, 'usage') and response.usage:
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    self.track_model_usage("keyword", provider, input_tokens, output_tokens, pricing)
                    
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=keyword_model,
                    max_tokens=10,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                keyword = ""
                for content_block in response.content:
                    if content_block.type == "text":
                        keyword += content_block.text
                keyword = keyword.strip()
                
                # Track usage for keyword phase
                if hasattr(response, 'usage') and response.usage:
                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens
                    self.track_model_usage("keyword", provider, input_tokens, output_tokens, pricing)
                    
            else:  # groq
                response = await client.chat.completions.create(
                    model=keyword_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
                keyword = response.choices[0].message.content.strip()
                
                # Track usage for keyword phase
                if hasattr(response, 'usage') and response.usage:
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    self.track_model_usage("keyword", provider, input_tokens, output_tokens, pricing)
            
            # Clean keyword (remove quotes, extra spaces)
            keyword = keyword.replace('"', '').replace("'", "").strip()
            logger.info(f"🎯 Smart keyword extracted: '{keyword}' using {keyword_model}")
            return keyword
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            # Fallback to simple extraction
            words = message.split()
            for word in ["SARL", "société", "commercial", "travail", "fiscalité"]:
                if word.lower() in message.lower():
                    return word
            return words[0] if words else "droit"
    
    def track_model_usage(self, phase: str, provider: str, input_tokens: int, output_tokens: int, pricing_dict: dict):
        """Track token usage for specific model phases."""
        # Calculate cost for this phase
        provider_pricing = pricing_dict[provider][phase]
        input_cost = (input_tokens / 1000000) * provider_pricing["input"]
        output_cost = (output_tokens / 1000000) * provider_pricing["output"]
        phase_cost = input_cost + output_cost
        
        logger.info(f"🏷️ {provider.title()} {phase}: {input_tokens} input, {output_tokens} output tokens, ${phase_cost:.6f}")
        
        return {"input": input_tokens, "output": output_tokens, "cost": phase_cost}

    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute MCP tool and return result."""
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, parameters)
                
                # Convert MCP result to serializable format
                if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                    # Handle list of TextContent objects
                    serializable_result = []
                    for item in result:
                        if hasattr(item, 'text'):
                            serializable_result.append(item.text)
                        else:
                            serializable_result.append(str(item))
                    return serializable_result
                elif hasattr(result, 'text'):
                    # Single TextContent object
                    return result.text
                else:
                    return str(result)
                    
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {"error": str(e)}
    
    async def process_job(self, job_id: str, message: str, provider: Optional[str] = None, company_id: str = "default", user_id: str = "default"):
        """Process job with enhanced 13-tool MCP workflow and structured output."""
        start_time = time.time()
        request_id = None
        
        try:
            # Create comprehensive request tracking
            request_id = RequestTracker.create_request(message, company_id, user_id, job_id, provider or self.default_provider)
            
            # Set job as processing
            DynamoDBJobManager.set_job_processing(job_id)
            DynamoDBJobManager.update_job_progress(
                job_id, "starting", 5, 
                "Starting enhanced 13-tool legal research workflow with structured output",
                {"estimated_remaining_seconds": 300}
            )
            
            # Update request tracking
            RequestTracker.update_request_progress(request_id, status="processing")
            
            # Step 1: Discover tools
            await self.discover_tools(job_id)
            
            # Step 2: Process with enhanced 13-tool workflow
            result = await self.enhanced_legal_research(message, provider, job_id)
            
            # Step 3: Complete job
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            DynamoDBJobManager.complete_job(job_id, result)
            
            # Complete request tracking with enhanced metrics
            RequestTracker.complete_request(request_id, result)
            
            logger.info(f"Job {job_id} completed successfully in {processing_time:.2f}s")
            logger.info(f"📊 Request {request_id} tracking completed with enhanced metrics")
            
        except Exception as e:
            logger.error(f"Job {job_id} processing failed: {e}")
            DynamoDBJobManager.fail_job(job_id, str(e))
            if request_id:
                RequestTracker.fail_request(request_id, str(e))
    
    async def enhanced_legal_research(self, message: str, provider: Optional[str] = None, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced legal research with comprehensive 13-tool MCP workflow and structured output."""
        self.query_count += 1
        start_time = time.time()
        
        # Select provider
        selected_provider = provider or self.default_provider
        if selected_provider not in self.clients:
            available = list(self.clients.keys())
            raise ValueError(f"Provider '{selected_provider}' not available. Available: {available}")
        
        # Get provider-specific client and models
        client = self.clients[selected_provider]
        mcp_model = self.models[selected_provider]["mcp"]
        structured_model = self.models[selected_provider]["structured"]
        is_openai = (selected_provider == "openai")
        is_groq = (selected_provider == "groq")
        is_anthropic = (selected_provider == "anthropic")
        
        # Token usage tracking
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost_usd = 0.0
        
        # Provider-specific pricing (per 1M tokens) - 5-phase enhanced architecture
        pricing = {
            "anthropic": {
                "keyword": {"input": 3.0, "output": 15.0},        # Claude Sonnet 4
                "tool_selection": {"input": 3.0, "output": 15.0}, # Claude Sonnet 4
                "uri_extraction": {"input": 3.0, "output": 15.0}, # Claude Sonnet 4
                "mcp": {"input": 3.0, "output": 15.0},            # Claude Sonnet 3.5 v2
                "structured": {"input": 0.8, "output": 4.0}       # Claude Haiku 3.5
            },
            "openai": {
                "keyword": {"input": 2.0, "output": 8.0},         # GPT-4.1
                "tool_selection": {"input": 2.0, "output": 8.0},  # GPT-4.1
                "uri_extraction": {"input": 2.0, "output": 8.0},  # GPT-4.1
                "mcp": {"input": 0.4, "output": 1.6},             # GPT-4.1-mini
                "structured": {"input": 0.1, "output": 0.4}       # GPT-4.1-nano
            },
            "groq": {
                "keyword": {"input": 0.59, "output": 0.79},       # Llama 3.3 70B
                "tool_selection": {"input": 0.59, "output": 0.79}, # Llama 3.3 70B
                "uri_extraction": {"input": 0.59, "output": 0.79}, # Llama 3.3 70B
                "mcp": {"input": 0.59, "output": 0.79},           # Llama 3.3 70B
                "structured": {"input": 0.59, "output": 0.79}     # Llama 3.3 70B
            }
        }
        
        if job_id:
            DynamoDBJobManager.update_job_progress(
                job_id, "mcp_workflow_start", 15, 
                f"Starting enhanced 13-tool legal research with {selected_provider} (MCP: {mcp_model}, Structured: {structured_model})",
                {
                    "ai_interaction": {
                        "model_calls": 0,
                        "tokens_used": 0,
                        "current_ai_task": f"Initializing enhanced 13-tool workflow with {selected_provider}"
                    },
                    "estimated_remaining_seconds": 240
                }
            )
        
        try:
            logger.info(f"🚀 Starting enhanced 13-tool legal research with {selected_provider}")
            
            # Remove all phase logic - just execute tools independently
            conversation_history = []
            tools_used = []
            discovered_sources = []
            
            # Prepare messages for tool execution
            messages = [
                {"role": "user", "content": message}
            ]
            
            max_iterations = 25
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                if job_id:
                    DynamoDBJobManager.update_job_progress(
                        job_id, "mcp_tools_execution", 20 + (iteration * 3), 
                        f"Executing MCP tools independently - iteration {iteration}/{max_iterations}",
                        {
                            "tools_progress": {
                                "current_iteration": iteration,
                                "tools_executed": len(tools_used),
                                "current_phase": "independent_tool_execution"
                            }
                        }
                    )
                
                # Format tools for provider-specific function calling
                if is_openai:
                    # OpenAI function calling format
                    tools_formatted = self.format_tools_for_openai()
                    
                    response = await client.chat.completions.create(
                        model=mcp_model,
                        messages=messages,
                        tools=tools_formatted if tools_formatted else None,
                        tool_choice="auto" if tools_formatted else None,
                        temperature=0.6,
                        max_tokens=4000
                    )
                    
                    # Capture token usage
                    if hasattr(response, 'usage') and response.usage:
                        input_tokens = response.usage.prompt_tokens
                        output_tokens = response.usage.completion_tokens
                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens
                        
                        # Calculate cost for MCP phase
                        provider_pricing = pricing[selected_provider]["mcp"]
                        input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                        output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                        total_cost_usd += input_cost + output_cost
                        
                        logger.info(f"🏷️ OpenAI MCP usage: {input_tokens} input, {output_tokens} output tokens, ${input_cost + output_cost:.4f}")
                    
                    assistant_message = response.choices[0].message
                    messages.append(assistant_message.model_dump())
                    
                    # Check for tool calls
                    if assistant_message.tool_calls:
                        # Execute each tool call independently
                        for tool_call in assistant_message.tool_calls:
                            tool_name = tool_call.function.name
                            parameters = json.loads(tool_call.function.arguments)
                            
                            logger.info(f"🔧 Executing {tool_name} independently with {parameters}")
                            
                            # Execute the tool
                            tool_result = await self.execute_mcp_tool(tool_name, parameters)
                            tools_used.append({"tool": tool_name, "parameters": parameters, "result": tool_result})
                            
                            # Collect sources from any discovery tools
                            if tool_name in ["find_most_cited_laws", "find_most_changed_laws", "find_newest_active_laws", "find_highest_authority_laws", "basic_document_search"] and isinstance(tool_result, dict):
                                sources = tool_result.get("laws", []) or tool_result.get("documents", [])
                                if isinstance(sources, list):
                                    discovered_sources.extend(sources)
                                    logger.info(f"📚 Discovery Tool - {tool_name} discovered {len(sources)} items")
                            
                            # Add tool result to conversation
                            content_str = tool_result if isinstance(tool_result, str) else json.dumps(tool_result, ensure_ascii=False)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": content_str
                            })
                            
                            conversation_history.append({
                                "tool": tool_name,
                                "parameters": parameters,
                                "result": tool_result
                            })
                    else:
                        # No more tools to call
                        break
                        
                elif is_anthropic:
                    # Claude tool calling format
                    tools_formatted = self.format_tools_for_claude()
                    
                    # Claude API call - only pass tools if we have valid tools
                    claude_params = {
                        "model": mcp_model,
                        "max_tokens": 4000,
                        "temperature": 0.6,
                        "system": self.system_prompt,
                        "messages": messages
                    }
                    
                    # Only add tools parameter if we have actual tools
                    if tools_formatted and len(tools_formatted) > 0:
                        claude_params["tools"] = tools_formatted
                    
                    response = await client.messages.create(**claude_params)
                    
                    # Capture token usage
                    if hasattr(response, 'usage') and response.usage:
                        input_tokens = response.usage.input_tokens
                        output_tokens = response.usage.output_tokens
                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens
                        
                        # Calculate cost for MCP phase
                        provider_pricing = pricing[selected_provider]["mcp"]
                        input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                        output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                        total_cost_usd += input_cost + output_cost
                        
                        logger.info(f"🏷️ Claude MCP usage: {input_tokens} input, {output_tokens} output tokens, ${input_cost + output_cost:.4f}")
                    
                    # Handle Claude tool use
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
                                
                                logger.info(f"🔧 Executing {tool_name} independently with {tool_input}")
                                
                                tool_result = await self.execute_mcp_tool(tool_name, tool_input)
                                tools_used.append({"tool": tool_name, "parameters": tool_input, "result": tool_result})
                                
                                # Collect sources from any discovery tools
                                if tool_name in ["find_most_cited_laws", "find_most_changed_laws", "find_newest_active_laws", "find_highest_authority_laws", "basic_document_search"] and isinstance(tool_result, dict):
                                    sources = tool_result.get("laws", []) or tool_result.get("documents", [])
                                    if isinstance(sources, list):
                                        discovered_sources.extend(sources)
                                        logger.info(f"📚 Discovery Tool - {tool_name} discovered {len(sources)} items")
                                
                                tool_results_for_claude.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": str(tool_result)
                                })
                                
                                conversation_history.append({
                                    "tool": tool_name,
                                    "parameters": tool_input,
                                    "result": tool_result
                                })
                        
                        messages.append({
                            "role": "user",
                            "content": tool_results_for_claude
                        })
                    else:
                        # No more tools to call
                        break
                        
                else:  # Groq - simplified approach for now
                    response = await client.chat.completions.create(
                        model=mcp_model,
                        messages=messages,
                        temperature=0.6,
                        max_tokens=4000
                    )
                    
                    # Capture token usage for Groq
                    if hasattr(response, 'usage') and response.usage:
                        input_tokens = response.usage.prompt_tokens
                        output_tokens = response.usage.completion_tokens
                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens
                        
                        # Calculate cost for MCP phase
                        provider_pricing = pricing[selected_provider]["mcp"]
                        input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                        output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                        total_cost_usd += input_cost + output_cost
                        
                        logger.info(f"🏷️ Groq MCP usage: {input_tokens} input, {output_tokens} output tokens, ${input_cost + output_cost:.4f}")
                    
                    # Simple response for Groq (can be enhanced later)
                    break
            
            # Record independent tool usage
            if discovered_sources and len(discovered_sources) > 0:
                logger.info(f"🔧 Independent tool usage completed: {len(tools_used)} tools, {len(discovered_sources)} sources discovered")
                conversation_history.append({
                    "tool": "independent_tool_execution_summary",
                    "parameters": {"total_tools_executed": len(tools_used), "sources_discovered": len(discovered_sources)},
                    "result": f"Independent tool execution completed: tools={len(tools_used)}, sources={len(discovered_sources)}"
                })

            
            # Enhanced workflow summary
            if discovered_sources and len(discovered_sources) > 0:
                logger.info(f"🧠 Enhanced 13-tool workflow applied to {len(discovered_sources)} sources")
                
                # Record enhanced workflow phases in conversation history
                conversation_history.append({
                    "tool": "enhanced_13_tool_workflow",
                    "parameters": {"keyword_used": smart_keyword, "total_tools_executed": len(tools_used), "sources_discovered": len(discovered_sources)},
                    "result": f"Enhanced 13-tool workflow completed: keyword='{smart_keyword}', tools={len(tools_used)}, sources={len(discovered_sources)}"
                })
            
            # Generate structured output
            if job_id:
                DynamoDBJobManager.update_job_progress(
                    job_id, "structured_output_generation", 80, 
                    "Generating structured legal analysis with enhanced 13-tool intelligence",
                    {
                        "tools_progress": {
                            "tools_completed": len(conversation_history),
                            "current_phase": "structured_output",
                            "enhanced_features": {
                                "smart_keyword": smart_keyword if 'smart_keyword' in locals() else None,
                                "sources_discovered": len(discovered_sources),
                                "workflow_type": "13_tool_phases"
                            }
                        }
                    }
                )
            
            # Generate structured output based on provider (using cheaper models)
            if is_openai and len(conversation_history) > 0:
                structured_result, structured_tokens, structured_cost = await self.generate_openai_structured_output(message, conversation_history, client, structured_model, selected_provider, pricing)
                total_input_tokens += structured_tokens.get('input', 0)
                total_output_tokens += structured_tokens.get('output', 0)
                total_cost_usd += structured_cost
            elif is_anthropic and len(conversation_history) > 0:
                structured_result, structured_tokens, structured_cost = await self.generate_claude_structured_output(message, conversation_history, client, structured_model, selected_provider, pricing)
                total_input_tokens += structured_tokens.get('input', 0)
                total_output_tokens += structured_tokens.get('output', 0)
                total_cost_usd += structured_cost
            elif is_groq:
                structured_result, structured_tokens, structured_cost = await self.generate_groq_structured_output(message, client, structured_model, selected_provider, pricing)
                total_input_tokens += structured_tokens.get('input', 0)
                total_output_tokens += structured_tokens.get('output', 0)
                total_cost_usd += structured_cost
            else:
                # Fallback to simple response
                structured_result = self.get_fallback_structure()
            
            # Calculate final metrics
            processing_time = time.time() - start_time
            
            if job_id:
                DynamoDBJobManager.update_job_progress(
                    job_id, "completed", 100, 
                    "Enhanced 13-tool legal research completed with structured output"
                )
            
            # Return comprehensive result with token usage
            return {
                "status": "success",
                "legal_analysis": structured_result,
                "model_info": {
                    "provider": selected_provider,
                    "mcp_model": mcp_model,
                    "structured_model": structured_model,
                    "temperature": 0.6,
                    "max_tokens": 4000,
                    "structured_output": True,
                    "workflow_type": "13_tool_phases"
                },
                "performance": {
                    "processing_time_seconds": round(processing_time, 2),
                    "iterations": iteration,
                    "mcp_tools_executed": len(conversation_history),
                    "enhanced_features": {
                        "smart_keyword_used": smart_keyword if 'smart_keyword' in locals() else None,
                        "sources_discovered": len(discovered_sources),
                        "13_tool_workflow": True
                    }
                },
                "tools_execution": {
                    "tools_used": [h["tool"] for h in conversation_history],
                    "total_tools": len(conversation_history),
                    "mcp_server": self.mcp_server_url,
                    "available_tools": len(self.available_tools),
                    "conversation_history": conversation_history,
                    "workflow_phases": self.analyze_workflow_phases([h["tool"] for h in conversation_history])
                },
                "token_usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                    "total_cost_usd": round(total_cost_usd, 6)
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced 13-tool legal research error: {e}")
            raise
    
    def analyze_workflow_phases(self, tools_used: List[str]) -> Dict[str, Any]:
        """Analyze which workflow phases were executed."""
        phases = {
            "phase_1_discovery": {
                "tools": ["find_most_cited_laws", "find_most_changed_laws", "find_newest_active_laws", "find_highest_authority_laws"],
                "executed": [],
                "completion": 0
            },
            "phase_2_analysis": {
                "tools": ["compare_results", "check_connections"],
                "executed": [],
                "completion": 0
            },
            "phase_3_relationships": {
                "tools": ["find_what_law_references", "find_what_references_law", "find_amendment_chain"],
                "executed": [],
                "completion": 0
            },
            "phase_4_final": {
                "tools": ["verify_still_valid", "rank_by_importance", "create_final_map"],
                "executed": [],
                "completion": 0
            },
            "content_extraction": {
                "tools": ["extract_content"],
                "executed": [],
                "completion": 0
            },
            "bonus": {
                "tools": ["basic_document_search"],
                "executed": [],
                "completion": 0
            }
        }
        
        for phase_name, phase_info in phases.items():
            for tool in phase_info["tools"]:
                if tool in tools_used:
                    phase_info["executed"].append(tool)
            
            phase_info["completion"] = (len(phase_info["executed"]) / len(phase_info["tools"])) * 100
        
        return phases
    
    def format_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Format MCP tools for OpenAI function calling."""
        tools = []
        
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            tools.append(openai_tool)
        
        return tools
    
    def format_tools_for_claude(self) -> List[Dict[str, Any]]:
        """Format MCP tools for Claude tool calling."""
        if not self.available_tools:
            return []
        
        claude_tools = []
        for tool in self.available_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            claude_tools.append(claude_tool)
        return claude_tools
    
    async def generate_openai_structured_output(self, message: str, conversation_history: List[Dict], client, model: str, provider: str, pricing: Dict) -> tuple[Dict[str, Any], Dict[str, int], float]:
        """Generate structured output using OpenAI's native structured output."""
        try:
            # Compile all tool results for structured analysis
            tools_summary = "\n".join([
                f"Outil: {h['tool']}\nParamètres: {h['parameters']}\nRésultat: {h['result']}\n---"
                for h in conversation_history
            ])
            
            structured_prompt = f"""Basé sur l'exécution des outils MCP suivants (utilisation indépendante):

{tools_summary}

Question originale: {message}

Générez maintenant la réponse structurée JSON complète selon le format requis avec les 5 sections obligatoires:

1. **ANSWER** - Analyse juridique EXHAUSTIVE en français
2. **REFERENCE_SOURCES** - TOUTES les sources utilisées avec URIs exacts
3. **CITATIONS_NETWORK** - Réseau de citations complet
4. **HISTORIQUE_AMENDEMENTS** - Historique des modifications  
5. **VALIDITE_LEGALE** - Validité et statut juridique

EXIGENCE CRITIQUE: 
1. Maintenez la cohérence absolue entre ANSWER et REFERENCE_SOURCES
2. Toute loi citée dans l'answer doit être détaillée dans les sources avec ses articles exacts
3. 🚨 URIs ABSOLUMENT EXACTS: Utilisez uniquement les URIs qui apparaissent dans les résultats des outils MCP
4. Exploitez TOUS les résultats des outils utilisés pour une analyse complète"""

            # Use OpenAI structured output
            structured_response = await client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant juridique expert qui génère des analyses structurées complètes basées sur des données MCP réelles obtenues par outils indépendants."},
                    {"role": "user", "content": structured_prompt}
                ],
                response_format=LegalAnalysisResponse,
                temperature=0.3,
                max_tokens=4000
            )
            
            # Capture token usage for structured output
            tokens = {"input": 0, "output": 0}
            cost = 0.0
            
            if hasattr(structured_response, 'usage') and structured_response.usage:
                input_tokens = structured_response.usage.prompt_tokens
                output_tokens = structured_response.usage.completion_tokens
                tokens = {"input": input_tokens, "output": output_tokens}
                
                # Calculate cost for structured output phase
                provider_pricing = pricing[provider]["structured"]
                input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                cost = input_cost + output_cost
                
                logger.info(f"🏷️ OpenAI structured output (nano): {input_tokens} input, {output_tokens} output tokens, ${cost:.4f}")
            
            return structured_response.choices[0].message.parsed.model_dump(), tokens, cost
            
        except Exception as e:
            logger.error(f"OpenAI structured output generation failed: {e}")
            # Return fallback structure
            return self.get_fallback_structure(), {"input": 0, "output": 0}, 0.0
    
    async def generate_claude_structured_output(self, message: str, conversation_history: List[Dict], client, model: str, provider: str, pricing: Dict) -> tuple[Dict[str, Any], Dict[str, int], float]:
        """Generate structured output using Claude with prompt-based JSON."""
        try:
            # Compile all tool results
            tools_summary = "\n".join([
                f"Outil: {h['tool']}\nParamètres: {h['parameters']}\nRésultat: {h['result']}\n---"
                for h in conversation_history
            ])
            
            structured_prompt = f"""Basé sur l'exécution des outils MCP suivants (utilisation indépendante):

{tools_summary}

Question originale: {message}

Générez une réponse JSON strictement conforme à cette structure exacte:

{{
  "answer": {{
    "summary": "Résumé exécutif de l'analyse juridique",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "exhaustive_content": "Analyse complète en markdown avec tous les détails basés sur les données MCP",
    "practical_guidance": "Guide pratique étape par étape"
  }},
  "reference_sources": {{
    "total_sources": 0,
    "primary_laws": [],
    "supporting_regulations": []
  }},
  "citations_network": {{
    "total_citations": 0,
    "network_summary": "Résumé du réseau basé sur les données MCP",
    "key_relationships": [],
    "network_strength": "high/medium/low",
    "interconnection_analysis": "Analyse des interconnexions"
  }},
  "historique_amendements": {{
    "total_amendments": 0,
    "evolution_summary": "Résumé de l'évolution basé sur les données MCP",
    "major_changes": [],
    "trend_analysis": {{
      "direction": "Direction des tendances",
      "key_themes": [],
      "frequency": "Fréquence des changements"
    }}
  }},
  "validite_legale": {{
    "overall_status": "Statut global basé sur les vérifications MCP",
    "last_verification": "Date de dernière vérification",
    "confidence_level": "high/medium/low",
    "validity_details": [],
    "legal_hierarchy": {{
      "foundation_level": [],
      "implementation_level": [],
      "execution_level": []
    }},
    "recommendations": {{
      "best_practices": [],
      "monitoring_advice": []
    }}
  }}
}}

IMPORTANT: Basez-vous EXCLUSIVEMENT sur les données MCP obtenues via les outils utilisés.
Répondez UNIQUEMENT avec le JSON valide, sans explication supplémentaire."""

            response = await client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.3,
                system="Vous êtes un assistant juridique expert qui génère du JSON structuré valide basé sur des données MCP réelles obtenues par outils indépendants.",
                messages=[{"role": "user", "content": structured_prompt}]
            )
            
            # Capture token usage for structured output
            tokens = {"input": 0, "output": 0}
            cost = 0.0
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                tokens = {"input": input_tokens, "output": output_tokens}
                
                # Calculate cost for structured output phase
                provider_pricing = pricing[provider]["structured"]
                input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                cost = input_cost + output_cost
                
                logger.info(f"🏷️ Claude structured output (haiku): {input_tokens} input, {output_tokens} output tokens, ${cost:.4f}")
            
            # Extract text content
            response_text = ""
            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
            
            # Parse JSON and validate with Pydantic
            try:
                parsed_json = json.loads(response_text)
                validated = LegalAnalysisResponse.model_validate(parsed_json)
                return validated.model_dump(), tokens, cost
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Claude JSON parsing failed: {e}")
                return self.get_fallback_structure(), tokens, cost
                
        except Exception as e:
            logger.error(f"Claude structured output generation failed: {e}")
            return self.get_fallback_structure(), {"input": 0, "output": 0}, 0.0
    
    async def generate_groq_structured_output(self, message: str, client, model: str, provider: str, pricing: Dict) -> tuple[Dict[str, Any], Dict[str, int], float]:
        """Generate structured output using Groq with prompt-based JSON."""
        try:
            structured_prompt = f"""Question: {message}

Générez une analyse juridique luxembourgeoise structurée en JSON avec cette structure exacte (basée sur outils indépendants):

{{
  "answer": {{
    "summary": "Résumé exécutif",
    "key_points": ["Point juridique 1", "Point juridique 2"],
    "exhaustive_content": "Analyse détaillée en markdown",
    "practical_guidance": "Guide pratique"
  }},
  "reference_sources": {{"total_sources": 0, "primary_laws": [], "supporting_regulations": []}},
  "citations_network": {{"total_citations": 0, "network_summary": "", "key_relationships": [], "network_strength": "low", "interconnection_analysis": ""}},
  "historique_amendements": {{"total_amendments": 0, "evolution_summary": "", "major_changes": [], "trend_analysis": {{"direction": "", "key_themes": [], "frequency": ""}}}},
  "validite_legale": {{"overall_status": "", "last_verification": "", "confidence_level": "medium", "validity_details": [], "legal_hierarchy": {{"foundation_level": [], "implementation_level": [], "execution_level": []}}, "recommendations": {{"best_practices": [], "monitoring_advice": []}}}}
}}

Répondez UNIQUEMENT avec le JSON valide."""

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert juridique luxembourgeois. Générez du JSON structuré valide basé sur l'utilisation d'outils indépendants."},
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Capture token usage for structured output
            tokens = {"input": 0, "output": 0}
            cost = 0.0
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                tokens = {"input": input_tokens, "output": output_tokens}
                
                # Calculate cost for structured output phase
                provider_pricing = pricing[provider]["structured"]
                input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                cost = input_cost + output_cost
                
                logger.info(f"🏷️ Groq structured output: {input_tokens} input, {output_tokens} output tokens, ${cost:.4f}")
            
            response_text = response.choices[0].message.content
            
            # Parse and validate JSON
            try:
                parsed_json = json.loads(response_text)
                validated = LegalAnalysisResponse.model_validate(parsed_json)
                return validated.model_dump(), tokens, cost
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Groq JSON parsing failed: {e}")
                return self.get_fallback_structure(), tokens, cost
                
        except Exception as e:
            logger.error(f"Groq structured output generation failed: {e}")
            return self.get_fallback_structure(), {"input": 0, "output": 0}, 0.0
            
            # Capture token usage for structured output
            tokens = {"input": 0, "output": 0}
            cost = 0.0
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                tokens = {"input": input_tokens, "output": output_tokens}
                
                # Calculate cost for structured output phase
                provider_pricing = pricing[provider]["structured"]
                input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                cost = input_cost + output_cost
                
                logger.info(f"🏷️ Claude structured output (haiku): {input_tokens} input, {output_tokens} output tokens, ${cost:.4f}")
            
            # Extract text content
            response_text = ""
            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
            
            # Parse JSON and validate with Pydantic
            try:
                parsed_json = json.loads(response_text)
                validated = LegalAnalysisResponse.model_validate(parsed_json)
                return validated.model_dump(), tokens, cost
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Claude JSON parsing failed: {e}")
                return self.get_fallback_structure(), tokens, cost
                
        except Exception as e:
            logger.error(f"Claude structured output generation failed: {e}")
            return self.get_fallback_structure(), {"input": 0, "output": 0}, 0.0
    
    async def generate_groq_structured_output(self, message: str, client, model: str, provider: str, pricing: Dict) -> tuple[Dict[str, Any], Dict[str, int], float]:
        """Generate structured output using Groq with prompt-based JSON."""
        try:
            structured_prompt = f"""Question: {message}

Générez une analyse juridique luxembourgeoise structurée en JSON avec cette structure exacte (basée sur workflow 13-outils):

{{
  "answer": {{
    "summary": "Résumé exécutif",
    "key_points": ["Point juridique 1", "Point juridique 2"],
    "exhaustive_content": "Analyse détaillée en markdown",
    "practical_guidance": "Guide pratique"
  }},
  "reference_sources": {{"total_sources": 0, "primary_laws": [], "supporting_regulations": []}},
  "citations_network": {{"total_citations": 0, "network_summary": "", "key_relationships": [], "network_strength": "low", "interconnection_analysis": ""}},
  "historique_amendements": {{"total_amendments": 0, "evolution_summary": "", "major_changes": [], "trend_analysis": {{"direction": "", "key_themes": [], "frequency": ""}}}},
  "validite_legale": {{"overall_status": "", "last_verification": "", "confidence_level": "medium", "validity_details": [], "legal_hierarchy": {{"foundation_level": [], "implementation_level": [], "execution_level": []}}, "recommendations": {{"best_practices": [], "monitoring_advice": []}}}}
}}

Répondez UNIQUEMENT avec le JSON valide."""

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert juridique luxembourgeois. Générez du JSON structuré valide basé sur le workflow 13-outils."},
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Capture token usage for structured output
            tokens = {"input": 0, "output": 0}
            cost = 0.0
            
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                tokens = {"input": input_tokens, "output": output_tokens}
                
                # Calculate cost for structured output phase
                provider_pricing = pricing[provider]["structured"]
                input_cost = (input_tokens / 1000000) * provider_pricing["input"]
                output_cost = (output_tokens / 1000000) * provider_pricing["output"]
                cost = input_cost + output_cost
                
                logger.info(f"🏷️ Groq structured output: {input_tokens} input, {output_tokens} output tokens, ${cost:.4f}")
            
            response_text = response.choices[0].message.content
            
            # Parse and validate JSON
            try:
                parsed_json = json.loads(response_text)
                validated = LegalAnalysisResponse.model_validate(parsed_json)
                return validated.model_dump(), tokens, cost
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Groq JSON parsing failed: {e}")
                return self.get_fallback_structure(), tokens, cost
                
        except Exception as e:
            logger.error(f"Groq structured output generation failed: {e}")
            return self.get_fallback_structure(), {"input": 0, "output": 0}, 0.0
    
    def get_fallback_structure(self) -> Dict[str, Any]:
        """Return fallback structure when structured output fails."""
        return {
            "answer": {
                "summary": "Analyse juridique de base disponible",
                "key_points": ["Consultez un professionnel du droit luxembourgeois", "Vérifiez les sources officielles sur legilux.public.lu"],
                "exhaustive_content": "# Analyse Juridique\n\nUne erreur s'est produite lors de la génération de l'analyse structurée. Veuillez consulter un professionnel du droit pour obtenir des conseils juridiques précis.",
                "practical_guidance": "Contactez un avocat spécialisé en droit luxembourgeois pour des conseils personnalisés."
            },
            "reference_sources": {
                "total_sources": 0,
                "primary_laws": [],
                "supporting_regulations": []
            },
            "citations_network": {
                "total_citations": 0,
                "network_summary": "Réseau non disponible",
                "key_relationships": [],
                "network_strength": "unknown",
                "interconnection_analysis": "Analyse non disponible"
            },
            "historique_amendements": {
                "total_amendments": 0,
                "evolution_summary": "Historique non disponible",
                "major_changes": [],
                "trend_analysis": {
                    "direction": "unknown",
                    "key_themes": [],
                    "frequency": "unknown"
                }
            },
            "validite_legale": {
                "overall_status": "unknown",
                "last_verification": "",
                "confidence_level": "low",
                "validity_details": [],
                "legal_hierarchy": {
                    "foundation_level": [],
                    "implementation_level": [],
                    "execution_level": []
                },
                "recommendations": {
                    "best_practices": ["Consultez les sources officielles"],
                    "monitoring_advice": ["Vérifiez régulièrement les mises à jour législatives"]
                }
            }
        }


def lambda_handler(event, context):
    """Main Lambda handler for enhanced job processing."""
    global legal_client
    
    try:
        # Initialize enhanced client on first run
        if not legal_client:
            legal_client = EnhancedLegalIntelligenceClient()
        
        # Extract job details from event
        job_id = event.get('job_id')
        message = event.get('message')
        provider = event.get('provider')
        company_id = event.get('company_id', 'default')
        user_id = event.get('user_id', 'default')
        
        if not job_id or not message:
            logger.error("Missing required parameters: job_id or message")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing job_id or message"})
            }
        
        logger.info(f"Processing enhanced job {job_id} with provider {provider} using independent tool usage")
        
        # Process the job asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                legal_client.process_job(job_id, message, provider, company_id, user_id)
            )
            
            logger.info(f"Enhanced job {job_id} processing completed successfully with independent tool usage")
            
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "enhanced_independent_tool_job_processed", "job_id": job_id})
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Enhanced job processing error: {e}")
        if 'job_id' in locals() and job_id:
            DynamoDBJobManager.fail_job(job_id, str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }