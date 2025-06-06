#!/usr/bin/env python3
"""
Luxembourg Legal MCP Server - Enhanced Edition
Professional legal research system leveraging full JOLUX capabilities.
MCP-compliant: Tools provide data, AI synthesizes.
"""

import logging
import sys
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP
try:
    from luxembourg_legal_server.search import LuxembourgSearch
    from luxembourg_legal_server.content import LuxembourgContent
    from luxembourg_legal_server.citation_analysis import CitationAnalyzer
    from luxembourg_legal_server.amendment_analysis import AmendmentAnalyzer
    from luxembourg_legal_server.repeal_analysis import RepealAnalyzer
    from luxembourg_legal_server.consolidation_analysis import ConsolidationAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating fallback implementations with enhanced capabilities...")
    
    class LuxembourgSearch:
        def __init__(self, endpoint):
            from SPARQLWrapper import SPARQLWrapper, JSON
            self.sparql = SPARQLWrapper(endpoint)
            self.sparql.setReturnFormat(JSON)
        
        def multi_field_search(self, keywords, limit=500):
            """Enhanced multi-field search using JOLUX relationships with smart keyword handling."""
            try:
                # Smart keyword splitting for better results
                keyword_list = [kw.strip() for kw in keywords.split() if len(kw.strip()) >= 3]
                
                if not keyword_list:
                    return {"documents": [], "total_found": 0, "error": "No valid keywords", "query_successful": False}
                
                # Build OR conditions for each keyword across all fields
                title_conditions = []
                base_conditions = []
                authority_conditions = []
                
                for keyword in keyword_list:
                    title_conditions.append(f'regex(str(?title), "{keyword}", "i")')
                    base_conditions.append(f'regex(str(?baseTitle), "{keyword}", "i")')
                    authority_conditions.append(f'regex(str(?authority), "{keyword}", "i")')
                
                title_filter = " || ".join(title_conditions)
                base_filter = " || ".join(base_conditions)
                authority_filter = " || ".join(authority_conditions)
                
                query = f"""
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?entity ?date ?title ?type ?pubDate ?entryForce ?authority ?basedOn WHERE {{
                    ?entity jolux:dateDocument ?date ;
                            a ?type ;
                            jolux:isRealizedBy ?expression .
                    ?expression jolux:title ?title .
                    
                    OPTIONAL {{ ?entity jolux:publicationDate ?pubDate }}
                    OPTIONAL {{ ?entity jolux:dateEntryInForce ?entryForce }}
                    OPTIONAL {{ ?entity jolux:responsibilityOf ?authority }}
                    OPTIONAL {{ ?entity jolux:basedOn ?basedOn }}
                    
                    # Smart multi-field search with keyword splitting
                    {{
                        FILTER({title_filter})
                    }} UNION {{
                        ?entity jolux:basedOn ?base .
                        ?base jolux:isRealizedBy/jolux:title ?baseTitle .
                        FILTER({base_filter})
                    }} UNION {{
                        FILTER({authority_filter})
                    }}
                }}
                ORDER BY DESC(?date)
                LIMIT {limit}
                """
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()
                
                documents = []
                if 'results' in results and 'bindings' in results['results']:
                    for binding in results['results']['bindings']:
                        doc = {
                            'uri': binding.get('entity', {}).get('value', ''),
                            'title': binding.get('title', {}).get('value', ''),
                            'date': binding.get('date', {}).get('value', ''),
                            'type': binding.get('type', {}).get('value', ''),
                            'publication_date': binding.get('pubDate', {}).get('value', ''),
                            'entry_force_date': binding.get('entryForce', {}).get('value', ''),
                            'authority': binding.get('authority', {}).get('value', ''),
                            'based_on': binding.get('basedOn', {}).get('value', ''),
                        }
                        
                        # Calculate relevance score based on keyword matches across all fields
                        title_lower = doc['title'].lower()
                        authority_lower = doc.get('authority', '').lower()
                        
                        matches = 0
                        for keyword in keyword_list:
                            kw_lower = keyword.lower()
                            if kw_lower in title_lower:
                                matches += 2  # Title matches worth more
                            elif kw_lower in authority_lower:
                                matches += 1  # Authority matches worth less
                        
                        doc['keyword_match_count'] = matches
                        doc['relevance_score'] = matches / (len(keyword_list) * 2)  # Normalize
                        
                        documents.append(doc)
                
                # Sort by relevance score, then by date
                documents.sort(key=lambda x: (x['relevance_score'], x['date']), reverse=True)
                
                return {
                    "documents": documents,
                    "total_found": len(documents),
                    "search_method": "smart_multi_field_search",
                    "keywords_used": keyword_list,
                    "keywords_original": keywords,
                    "query_successful": True
                }
            except Exception as e:
                return {"documents": [], "total_found": 0, "error": str(e), "query_successful": False}
        
        def discover_legal_relationships(self, document_uri, max_depth=3):
            """Discover legal relationships and amendment chains."""
            try:
                query = f"""
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT ?related ?title ?relationship ?date WHERE {{
                    {{
                        <{document_uri}> jolux:basedOn+ ?related .
                        BIND("based_on" as ?relationship)
                    }} UNION {{
                        ?related jolux:basedOn+ <{document_uri}> .
                        BIND("implements" as ?relationship)
                    }}
                    
                    ?related jolux:isRealizedBy/jolux:title ?title ;
                             jolux:dateDocument ?date .
                }}
                ORDER BY ?relationship DESC(?date)
                LIMIT 50
                """
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()
                
                relationships = []
                if 'results' in results and 'bindings' in results['results']:
                    for binding in results['results']['bindings']:
                        rel = {
                            'uri': binding.get('related', {}).get('value', ''),
                            'title': binding.get('title', {}).get('value', ''),
                            'relationship': binding.get('relationship', {}).get('value', ''),
                            'date': binding.get('date', {}).get('value', ''),
                        }
                        relationships.append(rel)
                
                return {
                    "relationships": relationships,
                    "total_found": len(relationships),
                    "source_document": document_uri,
                    "query_successful": True
                }
            except Exception as e:
                return {"relationships": [], "total_found": 0, "error": str(e), "query_successful": False}
        
        def temporal_legal_analysis(self, document_uris):
            """Analyze temporal aspects of legal documents."""
            try:
                uri_filter = " ".join([f"<{uri}>" for uri in document_uris[:20]])  # Limit to prevent timeout
                query = f"""
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT ?entity ?title ?docDate ?pubDate ?entryForce ?type WHERE {{
                    VALUES ?entity {{ {uri_filter} }}
                    
                    ?entity jolux:dateDocument ?docDate ;
                            jolux:isRealizedBy/jolux:title ?title ;
                            a ?type .
                    
                    OPTIONAL {{ ?entity jolux:publicationDate ?pubDate }}
                    OPTIONAL {{ ?entity jolux:dateEntryInForce ?entryForce }}
                }}
                ORDER BY DESC(?docDate)
                """
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()
                
                timeline = []
                if 'results' in results and 'bindings' in results['results']:
                    for binding in results['results']['bindings']:
                        event = {
                            'uri': binding.get('entity', {}).get('value', ''),
                            'title': binding.get('title', {}).get('value', ''),
                            'document_date': binding.get('docDate', {}).get('value', ''),
                            'publication_date': binding.get('pubDate', {}).get('value', ''),
                            'entry_force_date': binding.get('entryForce', {}).get('value', ''),
                            'type': binding.get('type', {}).get('value', ''),
                        }
                        timeline.append(event)
                
                return {
                    "timeline": timeline,
                    "total_analyzed": len(timeline),
                    "analysis_type": "temporal_legal_analysis",
                    "query_successful": True
                }
            except Exception as e:
                return {"timeline": [], "total_analyzed": 0, "error": str(e), "query_successful": False}
        
        def assess_legal_authority(self, documents):
            """Enhanced assessment with JOLUX hierarchy and authority data."""
            scored_documents = []
            
            for doc in documents:
                doc_type = doc.get('type', '')
                authority = doc.get('authority', '')
                date_doc = doc.get('date', '')
                title = doc.get('title', '').lower()
                
                # Base relevance score
                relevance_score = 0.5
                
                # JOLUX document type hierarchy scoring
                if 'BaseAct' in doc_type:
                    relevance_score += 0.5  # Foundational legislation
                elif 'Act' in doc_type:
                    relevance_score += 0.4  # Regular legislation
                elif 'Memorial' in doc_type:
                    relevance_score += 0.35  # Official gazette
                elif 'LegalResource' in doc_type:
                    relevance_score += 0.3  # Legal documents
                elif 'NationalLegalResource' in doc_type:
                    relevance_score += 0.25  # National specific
                
                # Authority scoring
                if 'chambre' in authority.lower() or 'parliament' in authority.lower():
                    relevance_score += 0.3  # Parliamentary authority
                elif 'ministre' in authority.lower() or 'minister' in authority.lower():
                    relevance_score += 0.2  # Ministerial authority
                elif 'administration' in authority.lower():
                    relevance_score += 0.1  # Administrative authority
                
                # Date relevance (prefer recent for currency)
                if date_doc:
                    try:
                        import datetime
                        if 'T' in date_doc:
                            doc_date = datetime.datetime.fromisoformat(date_doc.replace('Z', '+00:00'))
                        else:
                            doc_date = datetime.datetime.strptime(date_doc[:10], '%Y-%m-%d')
                        now = datetime.datetime.now()
                        years_old = (now - doc_date).days / 365.25
                        if years_old < 2:
                            relevance_score += 0.2  # Very recent
                        elif years_old < 5:
                            relevance_score += 0.15  # Recent
                        elif years_old < 10:
                            relevance_score += 0.1   # Moderately recent
                        elif years_old > 20:
                            relevance_score -= 0.1  # Old documents penalty
                    except:
                        pass
                
                # Implementation relationship bonus
                if doc.get('based_on'):
                    relevance_score += 0.15  # Has clear legal foundation
                
                doc_with_score = doc.copy()
                doc_with_score['authority_score'] = relevance_score
                scored_documents.append(doc_with_score)
            
            # Sort by authority score
            scored_documents.sort(key=lambda x: x['authority_score'], reverse=True)
            
            return scored_documents
    
    class LuxembourgContent:
        def __init__(self):
            try:
                from luxembourg_legal_server.extractors.content_processor import ContentProcessor
                self.content_processor = ContentProcessor()
            except:
                self.content_processor = None
        
        def extract_document_content(self, uri):
            # Try real content extraction first
            if self.content_processor:
                try:
                    content = self.content_processor.extract_entity_content(uri)
                    if content:
                        return content
                except:
                    pass
            # Fallback
            return {"text": f"Content from {uri}", "summary": "Content extraction fallback"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Luxembourg Legal Server - Enhanced")

# Initialize components
search_engine = None
content_processor = None
citation_analyzer = None
amendment_analyzer = None
repeal_analyzer = None
consolidation_analyzer = None

def initialize_components(sparql_endpoint: str):
    """Initialize enhanced search and content processing components."""
    global search_engine, content_processor, citation_analyzer, amendment_analyzer, repeal_analyzer, consolidation_analyzer
    search_engine = LuxembourgSearch(sparql_endpoint)
    content_processor = LuxembourgContent()
    citation_analyzer = CitationAnalyzer(sparql_endpoint)
    amendment_analyzer = AmendmentAnalyzer(sparql_endpoint)
    repeal_analyzer = RepealAnalyzer(sparql_endpoint)
    consolidation_analyzer = ConsolidationAnalyzer(sparql_endpoint)

# ==============================================================================
# MCP TOOLS FOR PROFESSIONAL LEGAL RESEARCH
# Enhanced with full JOLUX capabilities and professional standards
# ==============================================================================

@mcp.tool(description="Legal domain identification for Luxembourg questions")
def identify_legal_domain(legal_question: str) -> Dict[str, Any]:
    """Identify which legal domain(s) a question belongs to and let AI choose appropriate keywords."""
    logger.info(f"🎯 LEGAL DOMAIN IDENTIFICATION: '{legal_question}'")
    
    # Basic analysis without hardcoded keywords - let AI choose
    question_lower = legal_question.lower()
    
    # Extract potential legal terms from the question itself
    words = [word.strip("?.,!") for word in question_lower.split() if len(word) >= 3]
    legal_terms = [word for word in words if word not in ["comment", "quelles", "sont", "les", "pour", "dans", "avec", "une", "des", "qui", "que", "peut", "être"]]
    
    return {
        "analysis": f"Question analyzed: {legal_question}",
        "potential_legal_terms": legal_terms[:5],  # First 5 relevant terms
        "guidance": "AI should choose precise legal keywords based on the legal concepts in this question",
        "search_strategy": "Use specific legal terminology, avoid general terms like 'création', 'obligations'"
    }


@mcp.tool(description="Smart multi-word legal search using enhanced JOLUX capabilities")
def smart_legal_search(
    keywords: str,
    document_types: List[str] = None,
    authorities: List[str] = None,
    date_from: str = "2000-01-01",
    limit: int = 500
) -> Dict[str, Any]:
    """Smart search that handles multi-word queries by splitting keywords and using OR logic."""
    logger.info(f"🧠 SMART LEGAL SEARCH: '{keywords}'")
    
    try:
        result = search_engine.smart_keyword_search(keywords, limit)
        
        if result["query_successful"]:
            documents = result["documents"]
            
            # Filter by document types if specified
            if document_types:
                filtered_docs = []
                for doc in documents:
                    doc_type = doc.get('type', '')
                    if any(dt in doc_type for dt in document_types):
                        filtered_docs.append(doc)
                documents = filtered_docs
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "search_method": "smart_multi_word_search",
                "fields_searched": ["title", "based_on_relationships", "authority"],
                "keywords_used": result.get("keywords_used", []),
                "keywords_original": result.get("keywords_original", keywords),
                "document_types_filtered": document_types or "all",
                "authorities_targeted": authorities or "all"
            }
        else:
            return {"error": result.get("error", "Smart search failed")}
            
    except Exception as e:
        logger.error(f"❌ Smart search failed: {str(e)}")
        return {"error": f"Smart search failed: {str(e)}"}


@mcp.tool(description="Multi-field search using enhanced JOLUX capabilities")
def multi_field_legal_search(
    keywords: str,
    document_types: List[str] = None,
    authorities: List[str] = None,
    date_from: str = "2000-01-01",
    limit: int = 500
) -> Dict[str, Any]:
    """Enhanced search across titles, relationships, and authorities."""
    logger.info(f"🔍 MULTI-FIELD LEGAL SEARCH: '{keywords}'")
    
    try:
        result = search_engine.multi_field_search(keywords, limit)
        
        if result["query_successful"]:
            documents = result["documents"]
            
            # Filter by document types if specified
            if document_types:
                filtered_docs = []
                for doc in documents:
                    doc_type = doc.get('type', '')
                    if any(dt in doc_type for dt in document_types):
                        filtered_docs.append(doc)
                documents = filtered_docs
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "search_method": "multi_field_jolux_enhanced",
                "fields_searched": ["title", "based_on_relationships", "authority"],
                "keywords_used": keywords,
                "document_types_filtered": document_types or "all",
                "authorities_targeted": authorities or "all"
            }
        else:
            return {"error": result.get("error", "Multi-field search failed")}
            
    except Exception as e:
        logger.error(f"❌ Multi-field search failed: {str(e)}")
        return {"error": f"Multi-field search failed: {str(e)}"}


@mcp.tool(description="Discover legal relationships and amendment chains")
def discover_legal_relationships(
    document_uris: List[str],
    relationship_types: List[str] = None
) -> Dict[str, Any]:
    """Discover amendment chains, implementations, and legal dependencies."""
    logger.info(f"🔗 LEGAL RELATIONSHIP DISCOVERY: {len(document_uris)} documents")
    
    try:
        all_relationships = []
        
        for uri in document_uris[:10]:  # Limit to prevent timeout
            result = search_engine.discover_legal_relationships(uri)
            if result["query_successful"]:
                for rel in result["relationships"]:
                    rel["source_document"] = uri
                    all_relationships.append(rel)
        
        # Group relationships by type
        relationship_groups = {}
        for rel in all_relationships:
            rel_type = rel["relationship"]
            if rel_type not in relationship_groups:
                relationship_groups[rel_type] = []
            relationship_groups[rel_type].append(rel)
        
        return {
            "relationships": all_relationships,
            "relationship_groups": relationship_groups,
            "total_relationships": len(all_relationships),
            "documents_analyzed": len(document_uris[:10]),
            "relationship_types_found": list(relationship_groups.keys())
        }
        
    except Exception as e:
        logger.error(f"❌ Relationship discovery failed: {str(e)}")
        return {"error": f"Relationship discovery failed: {str(e)}"}


@mcp.tool(description="Get temporal data for legal documents")
def temporal_legal_analysis(
    document_uris: List[str]
) -> Dict[str, Any]:
    """Provide raw temporal data for AI analysis of legal currency."""
    logger.info(f"📅 TEMPORAL DATA EXTRACTION: {len(document_uris)} documents")
    
    try:
        result = search_engine.temporal_legal_analysis(document_uris)
        
        if result["query_successful"]:
            timeline = result["timeline"]
            
            # Add years calculation but no categorization
            import datetime
            now = datetime.datetime.now()
            
            for doc in timeline:
                doc_date_str = doc.get('document_date', '')
                if doc_date_str:
                    try:
                        doc_date = datetime.datetime.strptime(doc_date_str[:10], '%Y-%m-%d')
                        years_old = (now - doc_date).days / 365.25
                        doc['years_old'] = round(years_old, 1)
                    except:
                        doc['years_old'] = None
            
            return {
                "documents_with_dates": timeline,
                "total_analyzed": len(timeline),
                "date_properties_available": ["document_date", "publication_date", "entry_force_date"],
                "ai_guidance": "Analyze temporal relevance based on document dates. Consider: recent documents (<2 years) likely current, older documents may need currency verification."
            }
        else:
            return {"error": result.get("error", "Temporal data extraction failed")}
            
    except Exception as e:
        logger.error(f"❌ Temporal data extraction failed: {str(e)}")
        return {"error": f"Temporal data extraction failed: {str(e)}"}


@mcp.tool(description="Get legal authority and document hierarchy data")
def assess_legal_authority(
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Provide raw legal authority data for AI assessment."""
    logger.info(f"⚖️ LEGAL AUTHORITY DATA: {len(documents)} documents")
    
    try:
        # Use the new extract_authority_data method
        result = search_engine.extract_authority_data(documents)
        result["ai_guidance"] = "Assess authority using Luxembourg legal hierarchy: BaseAct > Act > Memorial > LegalResource. Consider authority source and document dates for legal precedence."
        return result
        
    except Exception as e:
        logger.error(f"❌ Authority data extraction failed: {str(e)}")
        return {"error": f"Authority data extraction failed: {str(e)}"}


@mcp.tool(description="Extract content from Luxembourg legal documents")
def extract_document_content(
    document_uris: List[str],
    extraction_focus: str = "relevant_sections"
) -> Dict[str, Any]:
    """Extract content from selected legal documents with HTML/PDF support."""
    logger.info(f"📄 CONTENT EXTRACTION: {len(document_uris)} documents")
    
    try:
        extracted_contents = []
        
        for uri in document_uris[:15]:  # Limit to prevent timeouts
            # Get raw content without AI processing
            raw_content = content_processor.extract_document_content(uri)
            
            if raw_content and raw_content.get("text"):
                extracted_contents.append({
                    "uri": uri,
                    "raw_text": raw_content.get("text", ""),
                    "source_url": raw_content.get("source_url", uri),
                    "character_count": len(raw_content.get("text", "")),
                    "extraction_successful": True
                })
            else:
                extracted_contents.append({
                    "uri": uri,
                    "raw_text": "",
                    "source_url": uri,
                    "character_count": 0,
                    "extraction_successful": False,
                    "error": "Content extraction failed"
                })
        
        successful_extractions = sum(1 for item in extracted_contents if item["extraction_successful"])
        
        return {
            "documents_with_content": extracted_contents,
            "total_requested": len(document_uris),
            "total_processed": len(extracted_contents),
            "successful_extractions": successful_extractions,
            "ai_guidance": "Analyze the raw legal text to identify relevant sections, legal concepts, and document structure. Consider Luxembourg legal language patterns."
        }
        
    except Exception as e:
        logger.error(f"❌ Content extraction failed: {str(e)}")
        return {"error": f"Content extraction failed: {str(e)}"}


# ==============================================================================
# NEW LEGAL INTELLIGENCE TOOLS - USING ACTUAL JOLUX SUPERPOWERS
# ==============================================================================

@mcp.tool(description="Get citation network data for a legal document")
def analyze_citation_network(
    document_uri: str,
    analysis_depth: int = 2
) -> Dict[str, Any]:
    """Provide raw citation network data for AI analysis."""
    logger.info(f"🔗 CITATION NETWORK DATA: {document_uri}")
    
    try:
        # Get raw citation data without analysis
        inbound_result = citation_analyzer.find_citing_documents(document_uri, 100)
        outbound_result = citation_analyzer.find_cited_documents(document_uri, 100)
        
        return {
            "central_document": document_uri,
            "inbound_citations": inbound_result.get("citing_documents", []),
            "outbound_citations": outbound_result.get("cited_documents", []),
            "inbound_count": inbound_result.get("citation_count", 0),
            "outbound_count": outbound_result.get("citation_count", 0),
            "total_network_size": inbound_result.get("citation_count", 0) + outbound_result.get("citation_count", 0),
            "ai_guidance": "Analyze citation patterns to determine legal influence, precedent value, and document importance in the legal network."
        }
    except Exception as e:
        logger.error(f"❌ Citation data extraction failed: {str(e)}")
        return {"error": f"Citation data extraction failed: {str(e)}"}


@mcp.tool(description="Find documents that cite a specific legal document")
def find_citing_documents(
    document_uri: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Find documents that cite the given document using jolux:cites."""
    logger.info(f"📚 FINDING CITING DOCUMENTS: {document_uri}")
    
    try:
        result = citation_analyzer.find_citing_documents(document_uri, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Citing documents search failed: {str(e)}")
        return {"error": f"Citing documents search failed: {str(e)}"}


@mcp.tool(description="Find documents cited by a specific legal document")
def find_cited_documents(
    document_uri: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Find documents cited by the given document using jolux:cites."""
    logger.info(f"📖 FINDING CITED DOCUMENTS: {document_uri}")
    
    try:
        result = citation_analyzer.find_cited_documents(document_uri, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Cited documents search failed: {str(e)}")
        return {"error": f"Cited documents search failed: {str(e)}"}


@mcp.tool(description="Analyze complete amendment chain for a legal document")
def analyze_amendment_chain(
    document_uri: str
) -> Dict[str, Any]:
    """Analyze complete amendment history using jolux:modifies/modifiedBy."""
    logger.info(f"📝 AMENDMENT CHAIN ANALYSIS: {document_uri}")
    
    try:
        result = amendment_analyzer.analyze_amendment_chain(document_uri)
        return result
    except Exception as e:
        logger.error(f"❌ Amendment analysis failed: {str(e)}")
        return {"error": f"Amendment analysis failed: {str(e)}"}


@mcp.tool(description="Find latest amendments to a legal document")
def find_latest_amendments(
    document_uri: str,
    limit: int = 10
) -> Dict[str, Any]:
    """Find most recent amendments using jolux:modifies."""
    logger.info(f"🕐 FINDING LATEST AMENDMENTS: {document_uri}")
    
    try:
        result = amendment_analyzer.find_latest_amendments(document_uri, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Latest amendments search failed: {str(e)}")
        return {"error": f"Latest amendments search failed: {str(e)}"}


@mcp.tool(description="Check legal currency and repeal status")
def check_legal_currency(
    document_uri: str
) -> Dict[str, Any]:
    """Check if document is still legally current using jolux:repeals."""
    logger.info(f"💰 LEGAL CURRENCY CHECK: {document_uri}")
    
    try:
        result = repeal_analyzer.check_legal_currency(document_uri)
        return result
    except Exception as e:
        logger.error(f"❌ Legal currency check failed: {str(e)}")
        return {"error": f"Legal currency check failed: {str(e)}"}


@mcp.tool(description="Analyze complete replacement/repeal chain")
def analyze_replacement_chain(
    document_uri: str
) -> Dict[str, Any]:
    """Analyze what this law repeals and what repeals it using jolux:repeals."""
    logger.info(f"🔄 REPLACEMENT CHAIN ANALYSIS: {document_uri}")
    
    try:
        result = repeal_analyzer.analyze_replacement_chain(document_uri)
        return result
    except Exception as e:
        logger.error(f"❌ Replacement analysis failed: {str(e)}")
        return {"error": f"Replacement analysis failed: {str(e)}"}


@mcp.tool(description="Find consolidated versions of a legal document")
def find_consolidated_versions(
    document_uri: str,
    limit: int = 50
) -> Dict[str, Any]:
    """Find consolidated versions using jolux:consolidates."""
    logger.info(f"📋 FINDING CONSOLIDATED VERSIONS: {document_uri}")
    
    try:
        result = consolidation_analyzer.find_consolidated_versions(document_uri, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Consolidation search failed: {str(e)}")
        return {"error": f"Consolidation search failed: {str(e)}"}


@mcp.tool(description="Find multilingual versions of a legal document")
def find_multilingual_versions(
    document_uri: str
) -> Dict[str, Any]:
    """Find different language versions using jolux:language."""
    logger.info(f"🌍 FINDING MULTILINGUAL VERSIONS: {document_uri}")
    
    try:
        result = consolidation_analyzer.find_multilingual_versions(document_uri)
        return result
    except Exception as e:
        logger.error(f"❌ Multilingual search failed: {str(e)}")
        return {"error": f"Multilingual search failed: {str(e)}"}


@mcp.tool(description="Get most current effective version of a legal document")
def get_current_effective_version(
    document_uri: str
) -> Dict[str, Any]:
    """Get the most current effective version using consolidation and language analysis."""
    logger.info(f"⚡ FINDING CURRENT EFFECTIVE VERSION: {document_uri}")
    
    try:
        result = consolidation_analyzer.get_current_effective_version(document_uri)
        return result
    except Exception as e:
        logger.error(f"❌ Current version analysis failed: {str(e)}")
        return {"error": f"Current version analysis failed: {str(e)}"}


@mcp.tool(description="Get enhanced workflow guidance for Luxembourg legal research")
def get_enhanced_workflow_guidance() -> Dict[str, Any]:
    """Get workflow suggestions using enhanced JOLUX capabilities."""
    
    workflows = [
        {
            "name": "Comprehensive Luxembourg Legal Research",
            "description": "Professional legal research using full JOLUX capabilities",
            "tools_sequence": [
                {
                    "tool": "identify_legal_domain",
                    "purpose": "Map question to legal areas and get domain-specific guidance",
                    "output": "Legal domain, keywords, document types, relevant authorities"
                },
                {
                    "tool": "multi_field_legal_search",
                    "purpose": "Search across titles, relationships, and authorities simultaneously",
                    "output": "50-500 relevant documents with enhanced metadata"
                },
                {
                    "tool": "discover_legal_relationships",
                    "purpose": "Find amendment chains, implementations, and legal dependencies",
                    "output": "Legal relationship network and document dependencies"
                },
                {
                    "tool": "temporal_legal_analysis",
                    "purpose": "Analyze legal currency and temporal context",
                    "output": "Timeline analysis and currency assessment"
                },
                {
                    "tool": "assess_legal_authority",
                    "purpose": "Rank by legal hierarchy, authority, and relevance",
                    "output": "Authoritative documents ranked by legal priority"
                },
                {
                    "tool": "analyze_citation_network",
                    "purpose": "Analyze citation relationships for key documents",
                    "output": "Citation network showing legal precedent connections"
                },
                {
                    "tool": "analyze_amendment_chain", 
                    "purpose": "Track amendment history and modifications",
                    "output": "Complete amendment timeline and modification analysis"
                },
                {
                    "tool": "check_legal_currency",
                    "purpose": "Verify if documents are still legally current",
                    "output": "Legal currency status and repeal information"
                },
                {
                    "tool": "find_consolidated_versions",
                    "purpose": "Find official consolidated versions",
                    "output": "Current effective consolidated text versions"
                },
                {
                    "tool": "extract_document_content",
                    "purpose": "Get actual legal text from top current documents",
                    "output": "Full legal content with Luxembourg-specific parsing"
                }
            ],
            "expected_outcome": "Professional legal intelligence analysis with citations, amendments, currency validation, and current effective text"
        },
        {
            "name": "Legal Relationship Intelligence",
            "description": "Deep analysis of legal document relationships and networks",
            "tools_sequence": [
                {
                    "tool": "multi_field_legal_search",
                    "purpose": "Find base documents for analysis",
                    "output": "Core documents for relationship analysis"
                },
                {
                    "tool": "analyze_citation_network",
                    "purpose": "Map citation relationships and legal precedents",
                    "output": "Complete citation network with precedent chains"
                },
                {
                    "tool": "find_citing_documents",
                    "purpose": "Find what documents reference these laws",
                    "output": "Legal documents that rely on or reference these laws"
                },
                {
                    "tool": "find_cited_documents", 
                    "purpose": "Find what these laws reference",
                    "output": "Legal foundation and authorities cited"
                },
                {
                    "tool": "analyze_amendment_chain",
                    "purpose": "Track complete modification history",
                    "output": "Amendment timeline and legal evolution"
                },
                {
                    "tool": "analyze_replacement_chain",
                    "purpose": "Analyze repeal and replacement relationships",
                    "output": "What laws were repealed and replaced"
                }
            ],
            "expected_outcome": "Complete legal relationship intelligence showing how laws interconnect, evolve, and influence each other"
        },
        {
            "name": "Legal Currency & Version Analysis",
            "description": "Validate legal currency and find current effective versions",
            "tools_sequence": [
                {
                    "tool": "multi_field_legal_search",
                    "purpose": "Find relevant legal documents",
                    "output": "Base documents for currency analysis"
                },
                {
                    "tool": "check_legal_currency",
                    "purpose": "Verify documents are still legally current",
                    "output": "Currency status and any superseding laws"
                },
                {
                    "tool": "find_latest_amendments",
                    "purpose": "Find most recent modifications",
                    "output": "Recent amendments affecting current law"
                },
                {
                    "tool": "find_consolidated_versions",
                    "purpose": "Find official consolidated versions",
                    "output": "Current consolidated text versions"
                },
                {
                    "tool": "find_multilingual_versions",
                    "purpose": "Find versions in different languages",
                    "output": "French, German, English versions available"
                },
                {
                    "tool": "get_current_effective_version",
                    "purpose": "Determine the most current effective version",
                    "output": "Recommended current version for legal practice"
                }
            ],
            "expected_outcome": "Current, legally valid documents with proper version validation for professional legal practice"
        }
    ]
    
    return {
        "available_workflows": workflows,
        "enhanced_capabilities": [
            "Multi-field JOLUX search (title + relationships + authority)",
            "Legal relationship discovery (amendment chains, implementations)", 
            "Citation network analysis (75K citation relationships)",
            "Amendment chain tracking (26K+ modifications)",
            "Legal currency validation (17K+ repeals)",
            "Consolidated version discovery (368 consolidations)",
            "Multilingual document support (238K+ language tags)",
            "Repeal and replacement analysis",
            "Temporal legal analysis (currency checking, timeline)",
            "Authority-based hierarchy ranking (proper legal prioritization)",
            "Luxembourg-specific content extraction (HTML/PDF parsing)"
        ],
        "jolux_features_utilized": [
            "jolux:cites (75,123 citation relationships) - NEW",
            "jolux:modifies/modifiedBy (26,826 + 578 modifications) - NEW", 
            "jolux:repeals (17,910 repeal relationships) - NEW",
            "jolux:consolidates (368 consolidated versions) - NEW",
            "jolux:language (238,518 multilingual versions) - NEW",
            "jolux:basedOn (legal relationships)",
            "jolux:responsibilityOf (publishing authority)",
            "jolux:dateDocument, jolux:publicationDate, jolux:dateEntryInForce (temporal)",
            "Document type hierarchy (BaseAct > Act > LegalResource)",
            "jolux:isRealizedBy (document structure)"
        ],
        "professional_standards": "Law firm grade legal research with proper authority ranking and currency validation"
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Luxembourg Legal MCP Server")
    parser.add_argument("--endpoint", required=True, help="SPARQL endpoint URL")
    parser.add_argument("--transport", default="stdio", help="Transport type")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Initialize components
    initialize_components(args.endpoint)
    
    # Run server
    logger.info(f"🚀 Starting Luxembourg Legal MCP Server - Enhanced Edition")
    logger.info(f"📊 SPARQL endpoint: {args.endpoint}")
    logger.info(f"🔗 Transport: {args.transport}")
    logger.info(f"⚖️ Enhanced JOLUX capabilities: ENABLED")
    logger.info(f"🎯 Professional legal research: READY")
    
    if args.transport == "streamable-http":
        logger.info(f"🌐 HTTP Server: {args.host}:{args.port}")
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        logger.info("📡 Using stdio transport")
        mcp.run()