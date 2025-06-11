#!/usr/bin/env python3
"""
Foundation Discovery OpenAI Client for Luxembourg Legal Intelligence MCP Server v2
Uses the new foundation discovery server with enhanced foundation law detection
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
import time
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import BaseModel, Field

load_dotenv()
logger = logging.getLogger(__name__)

# Pydantic models for structured JSON output (reusing from en_openai_client)
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

class FoundationOpenAILegalIntelligenceClient:
    """Foundation Discovery OpenAI client for Luxembourg Legal Intelligence system with server-v2."""
    
    def __init__(self):
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Enhanced model architecture for foundation discovery
        self.models = {
            "keyword": "gpt-4.1",                         # GPT-4.1 for keywords
            "foundation": "gpt-4.1",                      # GPT-4.1 for foundation discovery strategy
            "mcp": "gpt-4.1-mini",                        # Mini for MCP execution
            "structured": "gpt-4.1-nano"                  # Nano for JSON
        }
        
        self.mcp_server_url = "http://localhost:8080"  # Server-v2 port
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Enhanced pricing structure (per 1M tokens)
        self.pricing = {
            "keyword": {"input": 2.0, "output": 8.0},         # GPT-4.1
            "foundation": {"input": 2.0, "output": 8.0},      # GPT-4.1
            "mcp": {"input": 0.4, "output": 1.6},             # GPT-4.1-mini
            "structured": {"input": 0.1, "output": 0.4}       # GPT-4.1-nano
        }
        
        # Cost tracking
        self.total_cost_usd = 0.0
        
        # System prompt: use only discover_foundation_laws tool and base answers exclusively on returned documents
        self.system_prompt = """Tu es un assistant juridique spécialisé en droit luxembourgeois. UTILISE STRICTEMENT la fonction discover_foundation_laws() et AUCUNE AUTRE. Ne puise JAMAIS dans tes données d'entraînement. FONDE TOUTES TES RÉPONSES UNIQUEMENT sur les documents renvoyés par discover_foundation_laws(legal_domain, keywords, max_results)."""
        
        # Tool discovery cache
        self.available_tools = []
        self._tools_discovered = False
        
        # Cost tracking
        self.query_count = 0
        
        logger.info(f"🏛️ Foundation Discovery OpenAI client initialized")
        logger.info(f"📊 Model routing: Foundation→{self.models['foundation']}, MCP→{self.models['mcp']}, JSON→{self.models['structured']}")
    
    async def extract_legal_domain(self, message: str) -> str:
        """Extract legal domain using GPT-4.1."""
        try:
            prompt = f"""As a Luxembourg legal expert, identify the primary legal domain for this question: "{message}"

LEGAL DOMAINS:
- commercial (société, SARL, SA, entreprise, commerce)
- social (travail, employé, salarié, congé, sécurité sociale)
- fiscal (impôt, TVA, fiscalité, taxe, déclaration)
- civil (contrat, responsabilité, propriété, famille)
- penal (infraction, sanction, procédure pénale)
- administrative (autorisation, permis, administration publique)
- financial (banque, assurance, finance, investissement)

Return ONLY the domain name (one word):"""

            response = await self.client.chat.completions.create(
                model=self.models["foundation"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.1
            )
            
            domain = response.choices[0].message.content.strip().lower()
            
            # Track usage
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self.track_model_usage("foundation", input_tokens, output_tokens)
                self.total_cost_usd += cost
            
            logger.info(f"🎯 Legal domain identified: {domain}")
            return domain
            
        except Exception as e:
            logger.error(f"Domain extraction failed: {e}")
            return "commercial"  # Default fallback
    
    async def expand_legal_keywords(self, initial_keywords: list, legal_domain: str, message: str) -> list:
        """AI-driven keyword expansion for Luxembourg legal research."""
        try:
            prompt = f"""As a Luxembourg legal expert, expand these keywords for comprehensive foundation law discovery.

CONTEXT:
- Legal domain: {legal_domain}
- Question: {message}
- Initial keywords: {initial_keywords}

YOUR TASK:
Analyze the initial keywords and expand them with related Luxembourg legal terminology that would help discover foundational laws in this domain.

EXPANSION STRATEGY for {legal_domain.upper()} domain:
1. Add synonyms and variations of the initial terms
2. Include broader legal framework terms that govern this domain
3. Add specific Luxembourg legal terminology 
4. Include document type terms (loi, code, règlement, etc.)
5. Add process-related terms for this legal domain

LUXEMBOURG LEGAL KNOWLEDGE:
- For SARL questions: need "société", "commercial", "entreprise", "responsabilité", "limitée"
- For commercial law: need foundational terms like "1915", "sociétés commerciales"
- For any domain: include "loi", "code" for finding foundation laws
- Use French legal terminology as Luxembourg law is in French

EXAMPLES:
Initial: ["SARL"] → Expanded: ["SARL", "société", "sociétés", "commercial", "commerciales", "entreprise", "responsabilité", "limitée", "loi", "code"]
Initial: ["travail"] → Expanded: ["travail", "employé", "salarié", "contrat", "social", "code", "loi"]

Return a JSON array of 8-12 expanded keywords that will maximize foundation law discovery.
Question: {message}
Expanded keywords JSON:"""

            response = await self.client.chat.completions.create(
                model=self.models["keyword"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            keywords_text = response.choices[0].message.content.strip()
            
            # Track usage
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self.track_model_usage("keyword", input_tokens, output_tokens)
                self.total_cost_usd += cost
            
            # Parse expanded keywords JSON
            try:
                expanded_keywords = json.loads(keywords_text)
                if isinstance(expanded_keywords, list) and len(expanded_keywords) >= 5:
                    clean_keywords = [kw.replace('"', '').replace("'", "").strip() for kw in expanded_keywords[:12]]
                    logger.info(f"🎯 AI-expanded keywords: {initial_keywords} → {clean_keywords}")
                    return clean_keywords
            except:
                logger.warning(f"AI keyword expansion failed, using intelligent fallback")
            
            # Intelligent fallback expansion based on domain knowledge
            expanded = list(initial_keywords)
            
            if legal_domain == "commercial":
                for keyword in initial_keywords:
                    if keyword.lower() == "sarl":
                        expanded.extend(["société", "sociétés", "commercial", "commerciales", "entreprise", "responsabilité", "limitée", "loi", "code"])
                    elif "société" in keyword.lower():
                        expanded.extend(["SARL", "commercial", "entreprise", "code", "loi"])
                    elif "commercial" in keyword.lower():
                        expanded.extend(["société", "entreprise", "SARL", "code", "loi"])
                
                # Always add foundation law terms for commercial domain
                expanded.extend(["1915", "sociétés", "commercial", "code", "loi"])
                
            elif legal_domain == "social":
                expanded.extend(["travail", "employé", "salarié", "contrat", "social", "code", "loi"])
                
            elif legal_domain == "fiscal":
                expanded.extend(["impôt", "fiscal", "fiscalité", "taxe", "TVA", "code", "loi"])
                
            else:
                # General expansion
                expanded.extend(["loi", "code", "règlement"])
            
            # Remove duplicates while preserving order
            unique_expanded = []
            seen = set()
            for kw in expanded:
                if kw.lower() not in seen:
                    unique_expanded.append(kw)
                    seen.add(kw.lower())
            
            logger.info(f"🎯 Intelligent fallback expansion: {initial_keywords} → {unique_expanded}")
            return unique_expanded[:12]  # Limit to 12 keywords
            
        except Exception as e:
            logger.error(f"Keyword expansion failed: {e}")
            # Return original keywords as last resort
            return initial_keywords

    async def extract_strategic_keywords(self, message: str) -> list:
        """Extract initial strategic keywords using GPT-4.1."""
        try:
            prompt = f"""As an experienced Luxembourg legal expert, identify 3-5 initial strategic keywords for this question: "{message}"

Focus on the most specific and important legal terms first:

EXAMPLES:
"Creating a SARL?" → ["SARL", "création", "société"]
"Employment contract?" → ["travail", "contrat", "employé"]
"Tax obligations?" → ["fiscalité", "impôt", "obligations"]

Return JSON array of 3-5 core keywords:"""

            response = await self.client.chat.completions.create(
                model=self.models["keyword"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.2
            )
            
            keywords_text = response.choices[0].message.content.strip()
            
            # Track usage
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self.track_model_usage("keyword", input_tokens, output_tokens)
                self.total_cost_usd += cost
            
            # Parse keywords JSON
            try:
                keywords = json.loads(keywords_text)
                if isinstance(keywords, list) and len(keywords) >= 2:
                    clean_keywords = [kw.replace('"', '').replace("'", "").strip() for kw in keywords[:5]]
                    logger.info(f"🎯 Initial strategic keywords: {clean_keywords}")
                    return clean_keywords
            except:
                logger.warning(f"Keywords JSON parsing failed, using fallback")
            
            # Fallback: simple keyword detection
            message_lower = message.lower()
            
            if "sarl" in message_lower:
                return ["SARL", "société", "commercial"]
            elif "employ" in message_lower or "travail" in message_lower:
                return ["travail", "employé", "contrat"]
            elif "tax" in message_lower or "fiscal" in message_lower:
                return ["fiscalité", "impôt", "entreprise"]
            elif "company" in message_lower or "société" in message_lower:
                return ["société", "commercial", "entreprise"]
            else:
                return ["droit", "loi"]
                
        except Exception as e:
            logger.error(f"Strategic keyword extraction failed: {e}")
            return ["SARL", "société"]
    
    def track_model_usage(self, phase: str, input_tokens: int, output_tokens: int) -> float:
        """Track token usage for specific model phases."""
        phase_pricing = self.pricing[phase]
        input_cost = (input_tokens / 1000000) * phase_pricing["input"]
        output_cost = (output_tokens / 1000000) * phase_pricing["output"]
        phase_cost = input_cost + output_cost
        
        logger.info(f"🏷️ OpenAI {phase}: {input_tokens} input, {output_tokens} output tokens, ${phase_cost:.6f}")
        
        return phase_cost
        
    async def discover_tools(self) -> List[str]:
        """Discover available MCP tools."""
        if self._tools_discovered:
            return self.available_tools
        
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url + "/mcp/")
            async with Client(transport) as client:
                tools = await client.list_tools()
                self.available_tools = [tool.name for tool in tools]
                self._tools_discovered = True
                print(f"🔧 Discovered {len(self.available_tools)} MCP tools")
                return self.available_tools
        except Exception as e:
            print(f"❌ Tool discovery failed: {e}")
            return []
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool via MCP."""
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url + "/mcp/")
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, parameters)
                
                # Convert MCP result to serializable format
                if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                    serializable_result = []
                    for item in result:
                        if hasattr(item, 'text'):
                            serializable_result.append(item.text)
                        else:
                            serializable_result.append(str(item))
                    return serializable_result
                elif hasattr(result, 'text'):
                    return result.text
                else:
                    return str(result)
                    
        except Exception as e:
            print(f"❌ Tool execution failed for {tool_name}: {e}")
            return {"error": str(e)}
    
    def format_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Format MCP tools for OpenAI function calling."""
        tools = []
        
        # discover_foundation_laws - SUPER TOOL
        tools.append({
            "type": "function",
            "function": {
                "name": "discover_foundation_laws",
                "description": "🏛️ SUPER TOOL: Execute this function to discover foundational laws for any legal domain. Base all analysis exclusively on its results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "legal_domain": {"type": "string", "description": "Domaine juridique principal"},
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "Mots-clés stratégiques (3-5 mots)"},
                        "max_results": {"type": "integer", "description": "Nombre maximum de lois fondatrices à retourner"}
                    },
                    "required": ["legal_domain", "keywords"]
                }
            }
        })
        return tools
        
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Foundation discovery chat with enhanced workflow."""
        self.query_count += 1
        start_time = time.time()
        self.total_cost_usd = 0.0
        
        print(f"\n🏛️ FOUNDATION DISCOVERY OPENAI LEGAL RESEARCH - SERVER V2")
        print(f"📝 Question: {message}")
        print(f"🔧 Server: {self.mcp_server_url}")
        print("=" * 80)
        
        # Discover tools if not done yet
        if not self._tools_discovered:
            await self.discover_tools()
        
        # Phase 1: Extract legal domain and keywords
        print(f"\n🎯 Phase 1: Legal domain & keyword extraction")
        legal_domain = await self.extract_legal_domain(message)
        initial_keywords = await self.extract_strategic_keywords(message)
        print(f"✅ Legal domain: {legal_domain}")
        print(f"✅ Initial keywords: {initial_keywords}")
        
        # Phase 1.5: AI-driven keyword expansion
        print(f"\n🤖 Phase 1.5: AI-driven keyword expansion")
        strategic_keywords = await self.expand_legal_keywords(initial_keywords, legal_domain, message)
        print(f"✅ Expanded keywords: {strategic_keywords}")
        print(f"🎯 Expansion: {initial_keywords} → {strategic_keywords}")
        
        # Prepare tools for OpenAI
        tools = self.format_tools_for_openai()
        
        # Phase 2: MCP tool execution with foundation discovery priority
        print(f"\n🔧 Phase 2: Foundation discovery & MCP tool execution")
        
        # Start conversation with OpenAI
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""Question: {message}

PHASE 1 RESULTS:
- Legal domain: {legal_domain}
- Initial keywords: {initial_keywords}
- AI-expanded keywords: {strategic_keywords}

EXECUTE THIS WORKFLOW:
Appelle UNIQUEMENT discover_foundation_laws(legal_domain=\"{legal_domain}\", keywords={strategic_keywords}), et fonde toute ton analyse sur ses résultats. AUCUN autre appel d'outil n'est permis.

Commence immédiatement par discover_foundation_laws."""}
        ]
        
        conversation_history = []
        discovered_sources = []
        max_iterations = 15
        iteration = 0
        valid_uris_registry = set()
        
        try:
            # Tool execution phase
            while iteration < max_iterations:
                iteration += 1
                
                response = await self.client.chat.completions.create(
                    model=self.models["mcp"],
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.4,
                )
                
                # Track MCP model usage
                if hasattr(response, 'usage') and response.usage:
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    mcp_cost = self.track_model_usage("mcp", input_tokens, output_tokens)
                    self.total_cost_usd += mcp_cost
                
                assistant_message = response.choices[0].message
                messages.append(assistant_message.model_dump())
                
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        parameters = json.loads(tool_call.function.arguments)
                        
                        print(f"\n🔧 EXECUTING: {tool_name}")
                        print(f"📥 Parameters: {parameters}")
                        
                        # Execute the tool
                        tool_result = await self.execute_tool(tool_name, parameters)
                        
                        # Collect sources and URIs
                        if tool_name in ["discover_foundation_laws", "search_documents"] and isinstance(tool_result, str):
                            try:
                                parsed_result = json.loads(tool_result)
                                if isinstance(parsed_result, dict):
                                    # Handle different result structures
                                    sources = []
                                    if "foundations" in parsed_result:
                                        sources = parsed_result["foundations"]
                                    elif "documents" in parsed_result:
                                        sources = parsed_result["documents"]
                                    
                                    if isinstance(sources, list):
                                        discovered_sources.extend(sources)
                                        for source in sources:
                                            if isinstance(source, dict) and "uri" in source:
                                                real_uri = source["uri"]
                                                if real_uri and 'eli/' in real_uri:
                                                    valid_uris_registry.add(real_uri)
                                        print(f"📚 Discovered {len(sources)} sources, {len(valid_uris_registry)} total valid URIs")
                            except:
                                pass
                        
                        print(f"📤 Result: {tool_result}")
                        
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
                    break
            
            # Phase 3: Structured output generation
            print(f"\n📋 Phase 3: Structured JSON generation")
            
            tools_summary = "\n".join([
                f"Tool: {h['tool']}\nParameters: {h['parameters']}\nResult: {h['result']}\n---"
                for h in conversation_history
            ])
            
            valid_uris = list(valid_uris_registry)
            document_titles = {}
            
            for source in discovered_sources:
                if isinstance(source, dict) and source.get('uri') in valid_uris_registry:
                    uri = source.get('uri')
                    title = source.get('title', 'Sans titre')
                    document_titles[uri] = title
            
            structured_prompt = f"""Basé sur les exécutions d'outils MCP Foundation Discovery v2:

{tools_summary}

🏛️ FOUNDATION DISCOVERY RESULTS:
- Legal domain: {legal_domain}
- Initial keywords: {initial_keywords}
- AI-expanded keywords: {strategic_keywords}
- Keyword expansion: {', '.join(initial_keywords)} → {', '.join(strategic_keywords)}
- Foundation laws discovered: {len([h for h in conversation_history if h['tool'] == 'discover_foundation_laws'])}
- Total valid URIs: {len(valid_uris)}

📋 LISTE DES URIs VALIDES:
{chr(10).join([f"✅ {uri} → {document_titles.get(uri, 'Sans titre')}" for uri in valid_uris[:20]])}

Question originale: {message}

Génère maintenant la réponse JSON structurée complète avec les 5 sections obligatoires, en utilisant les données réelles découvertes par les outils MCP Foundation Discovery."""

            # Generate structured response
            structured_response = await self.client.beta.chat.completions.parse(
                model=self.models["structured"],
                messages=[
                    {"role": "system", "content": "Tu es un assistant expert juridique qui génère des analyses structurées complètes. Réponds en français pour tout le contenu."},
                    {"role": "user", "content": structured_prompt}
                ],
                response_format=LegalAnalysisResponse,
                temperature=0.2
            )
            
            # Track structured output model usage
            if hasattr(structured_response, 'usage') and structured_response.usage:
                input_tokens = structured_response.usage.prompt_tokens
                output_tokens = structured_response.usage.completion_tokens
                structured_cost = self.track_model_usage("structured", input_tokens, output_tokens)
                self.total_cost_usd += structured_cost
            
            legal_analysis = structured_response.choices[0].message.parsed
            
            # Calculate metrics
            processing_time = time.time() - start_time
            estimated_tokens = sum(len(str(msg)) for msg in messages) // 4
            
            print(f"\n🎯 FOUNDATION DISCOVERY RESULTS:")
            print("=" * 80)
            print(f"✅ Answer: {len(legal_analysis.answer.exhaustive_content)} characters")
            print(f"✅ Sources: {legal_analysis.reference_sources.total_sources} sources")
            print(f"✅ Citations: {legal_analysis.citations_network.total_citations} citations")
            print(f"✅ Amendments: {legal_analysis.historique_amendements.total_amendments} amendments")
            print(f"✅ Validity: {legal_analysis.validite_legale.overall_status}")
            print("=" * 80)
            print(f"⏱️  Processing time: {processing_time:.2f}s")
            print(f"🔧 Tools used: {len(conversation_history)}")
            print(f"💰 Total cost: ${self.total_cost_usd:.6f}")
            
            return {
                "status": "success",
                "query": {
                    "question": message,
                    "legal_domain": legal_domain,
                    "initial_keywords": initial_keywords,
                    "expanded_keywords": strategic_keywords,
                    "keyword_expansion": f"{', '.join(initial_keywords)} → {', '.join(strategic_keywords)}",
                    "processing_time": f"{processing_time:.1f}s",
                    "provider": "openai-foundation-discovery"
                },
                "legal_analysis": legal_analysis.model_dump(),
                "model_info": {
                    "provider": "openai",
                    "architecture": "foundation-discovery",
                    "models": self.models,
                    "server_version": "v2",
                    "server_url": self.mcp_server_url,
                    "structured_output": True,
                    "language": "french_responses"
                },
                "performance": {
                    "processing_time_seconds": round(processing_time, 2),
                    "estimated_tokens": estimated_tokens,
                    "cost_usd": round(self.total_cost_usd, 6),
                    "iterations": iteration,
                    "max_iterations": max_iterations
                },
                "tools_execution": {
                    "tools_used": [h["tool"] for h in conversation_history],
                    "total_tools": len(conversation_history),
                    "foundation_discoveries": len([h for h in conversation_history if h['tool'] == 'discover_foundation_laws']),
                    "mcp_server": self.mcp_server_url,
                    "available_tools": len(self.available_tools)
                },
                "conversation_history": conversation_history,
                "validation": {
                    "valid_uris_found": len(valid_uris),
                    "server_version": "foundation-discovery-v2"
                }
            }
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model_info": {"provider": "openai", "architecture": "foundation-discovery", "server_version": "v2"},
                "debug_info": {
                    "iteration": iteration,
                    "tools_executed": len(conversation_history)
                }
            }

class FoundationLuxembourgLegalAssistant:
    """Main class for Luxembourg Legal Intelligence - Foundation Discovery Edition."""
    
    def __init__(self):
        self.client = FoundationOpenAILegalIntelligenceClient()
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process legal query with foundation discovery."""
        return await self.client.chat(message)

async def main():
    """Interactive mode."""
    print("🏛️ FOUNDATION DISCOVERY OPENAI LUXEMBOURG LEGAL INTELLIGENCE - SERVER V2")
    print("=" * 80)
    print("🚀 Revolutionary Foundation Discovery with 6 intelligent methods")
    print("🔧 discover_foundation_laws - Automatic foundation law detection")
    print("📊 Enhanced legal analysis with true foundation discovery")
    print("🤖 AI Models: OpenAI Foundation Discovery Architecture")
    print("🇫🇷 Expert French Legal Responses")
    print("=" * 80)
    
    print("\n🧪 TESTING FOUNDATION DISCOVERY")
    test_question = "What are the current laws for creating a SARL in Luxembourg?"
    print(f"📝 Question: {test_question}")
    
    assistant = FoundationLuxembourgLegalAssistant()
    result = await assistant.chat(test_question)
    
    if result["status"] == "success":
        print(f"\n✅ Foundation discovery completed successfully!")
        print(f"🏛️ Foundation discoveries: {result['tools_execution']['foundation_discoveries']}")
        print(f"🔧 Total tools used: {result['tools_execution']['total_tools']}")
        print(f"⏱️  Total time: {result['performance']['processing_time_seconds']}s")
        print(f"💰 Estimated cost: ${result['performance']['cost_usd']}")
        print(f"🔍 Valid URIs found: {result['validation']['valid_uris_found']}")
        
        print(f"\n📋 Generated JSON structure:")
        print(f"   ✅ Answer: {len(result['legal_analysis']['answer']['exhaustive_content'])} characters")
        print(f"   ✅ Sources: {result['legal_analysis']['reference_sources']['total_sources']} sources")
        print(f"   ✅ Citations: {result['legal_analysis']['citations_network']['total_citations']} citations")
        print(f"   ✅ Amendments: {result['legal_analysis']['historique_amendements']['total_amendments']} amendments")
        
        print(f"\n🎯 COMPLETE STRUCTURED JSON RESPONSE:")
        print("=" * 80)
        print(json.dumps(result['legal_analysis'], indent=2, ensure_ascii=False))
        print("=" * 80)
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())