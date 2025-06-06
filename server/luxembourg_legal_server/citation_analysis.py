"""
Luxembourg Legal Citation Analysis
MCP Tool for analyzing legal document citation networks using JOLUX ontology.
"""

import logging
from typing import Dict, List, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)


class CitationAnalyzer:
    """Analyzes legal citation networks using jolux:cites relationships."""
    
    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def find_citing_documents(self, document_uri: str, limit: int = 100) -> Dict[str, Any]:
        """Find documents that cite the given document.
        
        Args:
            document_uri: URI of the document to analyze
            limit: Maximum number of citing documents to return
            
        Returns:
            Dictionary with citing documents and citation analysis
        """
        logger.info(f"🔗 Finding documents citing: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?citing_document ?title ?date ?type WHERE {{
                ?citing_document jolux:cites <{document_uri}> ;
                                 jolux:dateDocument ?date ;
                                 a ?type ;
                                 jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            citing_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('citing_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    citing_docs.append(doc)
            
            logger.info(f"✅ Found {len(citing_docs)} citing documents")
            
            return {
                "target_document": document_uri,
                "citing_documents": citing_docs,
                "citation_count": len(citing_docs),
                "analysis_type": "inbound_citations",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Citation analysis failed: {str(e)}")
            return {
                "target_document": document_uri,
                "citing_documents": [],
                "citation_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_cited_documents(self, document_uri: str, limit: int = 100) -> Dict[str, Any]:
        """Find documents cited by the given document.
        
        Args:
            document_uri: URI of the document to analyze
            limit: Maximum number of cited documents to return
            
        Returns:
            Dictionary with cited documents and citation analysis
        """
        logger.info(f"📚 Finding documents cited by: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?cited_document ?title ?date ?type WHERE {{
                <{document_uri}> jolux:cites ?cited_document .
                ?cited_document jolux:dateDocument ?date ;
                                a ?type ;
                                jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            cited_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('cited_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    cited_docs.append(doc)
            
            logger.info(f"✅ Found {len(cited_docs)} cited documents")
            
            return {
                "source_document": document_uri,
                "cited_documents": cited_docs,
                "citation_count": len(cited_docs),
                "analysis_type": "outbound_citations",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Citation analysis failed: {str(e)}")
            return {
                "source_document": document_uri,
                "cited_documents": [],
                "citation_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def analyze_citation_network(self, document_uri: str, depth: int = 2) -> Dict[str, Any]:
        """Analyze full citation network around a document.
        
        Args:
            document_uri: URI of the central document
            depth: How many levels deep to analyze (1=direct, 2=second-degree)
            
        Returns:
            Dictionary with complete citation network analysis
        """
        logger.info(f"🕸️ Analyzing citation network for: {document_uri} (depth: {depth})")
        
        try:
            # Get both inbound and outbound citations
            citing_result = self.find_citing_documents(document_uri)
            cited_result = self.find_cited_documents(document_uri)
            
            network = {
                "central_document": document_uri,
                "inbound_citations": citing_result,
                "outbound_citations": cited_result,
                "total_network_size": citing_result["citation_count"] + cited_result["citation_count"],
                "analysis_depth": depth,
                "network_type": "citation_analysis"
            }
            
            # If depth > 1, analyze second-degree connections
            if depth > 1:
                second_degree = []
                
                # Analyze what the citing documents cite (shared authorities)
                for citing_doc in citing_result["citing_documents"][:5]:  # Limit to avoid explosion
                    sub_cited = self.find_cited_documents(citing_doc["uri"], limit=10)
                    if sub_cited["citation_count"] > 0:
                        second_degree.append({
                            "document": citing_doc,
                            "also_cites": sub_cited["cited_documents"]
                        })
                
                network["second_degree_analysis"] = second_degree
            
            logger.info(f"✅ Network analysis complete: {network['total_network_size']} total connections")
            return network
            
        except Exception as e:
            logger.error(f"❌ Network analysis failed: {str(e)}")
            return {
                "central_document": document_uri,
                "error": str(e),
                "query_successful": False
            }