"""
Luxembourg Legal Repeal Analysis
MCP Tool for tracking legal document repeal relationships using JOLUX ontology.
"""

import logging
from typing import Dict, List, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)


class RepealAnalyzer:
    """Analyzes legal repeal relationships using jolux:repeals property."""
    
    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def find_repealed_laws(self, document_uri: str, limit: int = 100) -> Dict[str, Any]:
        """Find laws that this document repeals.
        
        Args:
            document_uri: URI of the repealing document
            limit: Maximum number of repealed laws to return
            
        Returns:
            Dictionary with laws repealed by this document
        """
        logger.info(f"🚫 Finding laws repealed by: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?repealed_document ?title ?date ?type WHERE {{
                <{document_uri}> jolux:repeals ?repealed_document .
                ?repealed_document jolux:dateDocument ?date ;
                                  a ?type ;
                                  jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY ?date
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            repealed_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('repealed_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    repealed_docs.append(doc)
            
            logger.info(f"✅ Found {len(repealed_docs)} repealed laws")
            
            return {
                "repealing_document": document_uri,
                "repealed_laws": repealed_docs,
                "repeal_count": len(repealed_docs),
                "analysis_type": "outbound_repeals",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Repeal analysis failed: {str(e)}")
            return {
                "repealing_document": document_uri,
                "repealed_laws": [],
                "repeal_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_superseding_laws(self, document_uri: str, limit: int = 50) -> Dict[str, Any]:
        """Find laws that repeal/supersede the given document.
        
        Args:
            document_uri: URI of the potentially repealed document
            limit: Maximum number of superseding laws to return
            
        Returns:
            Dictionary with laws that supersede this document
        """
        logger.info(f"⚖️ Finding laws that supersede: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?superseding_document ?title ?date ?type WHERE {{
                ?superseding_document jolux:repeals <{document_uri}> ;
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
            
            superseding_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('superseding_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    superseding_docs.append(doc)
            
            logger.info(f"✅ Found {len(superseding_docs)} superseding laws")
            
            return {
                "target_document": document_uri,
                "superseding_laws": superseding_docs,
                "superseding_count": len(superseding_docs),
                "analysis_type": "inbound_repeals",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Superseding laws analysis failed: {str(e)}")
            return {
                "target_document": document_uri,
                "superseding_laws": [],
                "superseding_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def check_legal_currency(self, document_uri: str) -> Dict[str, Any]:
        """Check if a document is still legally current (not repealed).
        
        Args:
            document_uri: URI of the document to check
            
        Returns:
            Dictionary with legal currency status
        """
        logger.info(f"💰 Checking legal currency for: {document_uri}")
        
        try:
            # Check if this document has been repealed
            superseding_result = self.find_superseding_laws(document_uri, limit=10)
            
            is_current = superseding_result["superseding_count"] == 0
            
            currency_status = {
                "document": document_uri,
                "is_legally_current": is_current,
                "superseding_laws": superseding_result,
                "analysis_type": "legal_currency_check",
                "query_successful": True
            }
            
            if is_current:
                currency_status["status"] = "CURRENT"
                currency_status["status_message"] = "Document appears to be legally current"
            else:
                currency_status["status"] = "REPEALED"
                currency_status["status_message"] = f"Document repealed by {superseding_result['superseding_count']} law(s)"
                # Get the most recent repealing law
                if superseding_result["superseding_laws"]:
                    most_recent = superseding_result["superseding_laws"][0]
                    currency_status["repealed_by"] = most_recent
            
            logger.info(f"✅ Currency check complete: {currency_status['status']}")
            return currency_status
            
        except Exception as e:
            logger.error(f"❌ Legal currency check failed: {str(e)}")
            return {
                "document": document_uri,
                "is_legally_current": None,
                "status": "ERROR",
                "error": str(e),
                "query_successful": False
            }
    
    def analyze_replacement_chain(self, document_uri: str) -> Dict[str, Any]:
        """Analyze the complete replacement chain for a document.
        
        Args:
            document_uri: URI of the document to analyze
            
        Returns:
            Dictionary with complete replacement chain analysis
        """
        logger.info(f"🔄 Analyzing replacement chain for: {document_uri}")
        
        try:
            # What this document repeals
            repealed_result = self.find_repealed_laws(document_uri)
            
            # What repeals this document
            superseding_result = self.find_superseding_laws(document_uri)
            
            # Legal currency check
            currency_result = self.check_legal_currency(document_uri)
            
            replacement_chain = {
                "central_document": document_uri,
                "laws_this_repeals": repealed_result,
                "laws_that_repeal_this": superseding_result,
                "legal_currency": currency_result,
                "total_repeals_made": repealed_result["repeal_count"],
                "total_repeals_received": superseding_result["superseding_count"],
                "analysis_type": "complete_replacement_chain",
                "query_successful": True
            }
            
            # Determine position in replacement chain
            if repealed_result["repeal_count"] > 0 and superseding_result["superseding_count"] == 0:
                chain_position = "active_repealer"
            elif repealed_result["repeal_count"] == 0 and superseding_result["superseding_count"] > 0:
                chain_position = "repealed_terminal"
            elif repealed_result["repeal_count"] > 0 and superseding_result["superseding_count"] > 0:
                chain_position = "intermediate_link"
            else:
                chain_position = "standalone"
            
            replacement_chain["chain_position"] = chain_position
            
            logger.info(f"✅ Replacement chain analysis complete: {chain_position}")
            return replacement_chain
            
        except Exception as e:
            logger.error(f"❌ Replacement chain analysis failed: {str(e)}")
            return {
                "central_document": document_uri,
                "error": str(e),
                "query_successful": False
            }