"""
Luxembourg Legal Amendment Analysis
MCP Tool for tracking legal document amendment chains using JOLUX ontology.
"""

import logging
from typing import Dict, List, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

logger = logging.getLogger(__name__)


class AmendmentAnalyzer:
    """Analyzes legal amendment chains using jolux:modifies/modifiedBy relationships."""
    
    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def find_modification_history(self, document_uri: str, limit: int = 50) -> Dict[str, Any]:
        """Find complete modification history of a document.
        
        Args:
            document_uri: URI of the document to analyze
            limit: Maximum number of modifications to return
            
        Returns:
            Dictionary with chronological modification history
        """
        logger.info(f"📝 Finding modification history for: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?modifying_document ?title ?date ?type WHERE {{
                ?modifying_document jolux:modifies <{document_uri}> ;
                                   jolux:dateDocument ?date ;
                                   a ?type ;
                                   jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY ?date
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            modifications = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    mod = {
                        'uri': binding.get('modifying_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    modifications.append(mod)
            
            logger.info(f"✅ Found {len(modifications)} modifications")
            
            return {
                "target_document": document_uri,
                "modifications": modifications,
                "modification_count": len(modifications),
                "analysis_type": "modification_history",
                "chronological_order": True,
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Modification history analysis failed: {str(e)}")
            return {
                "target_document": document_uri,
                "modifications": [],
                "modification_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_what_this_modifies(self, document_uri: str, limit: int = 50) -> Dict[str, Any]:
        """Find what documents this document modifies.
        
        Args:
            document_uri: URI of the modifying document
            limit: Maximum number of modified documents to return
            
        Returns:
            Dictionary with documents modified by this document
        """
        logger.info(f"⚖️ Finding what is modified by: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?modified_document ?title ?date ?type WHERE {{
                <{document_uri}> jolux:modifies ?modified_document .
                ?modified_document jolux:dateDocument ?date ;
                                  a ?type ;
                                  jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY ?date
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            modified_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('modified_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    modified_docs.append(doc)
            
            logger.info(f"✅ Found {len(modified_docs)} modified documents")
            
            return {
                "modifying_document": document_uri,
                "modified_documents": modified_docs,
                "modification_count": len(modified_docs),
                "analysis_type": "outbound_modifications",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Modification analysis failed: {str(e)}")
            return {
                "modifying_document": document_uri,
                "modified_documents": [],
                "modification_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_latest_amendments(self, document_uri: str, limit: int = 10) -> Dict[str, Any]:
        """Find the most recent amendments to a document.
        
        Args:
            document_uri: URI of the document to analyze
            limit: Maximum number of recent amendments to return
            
        Returns:
            Dictionary with most recent amendments
        """
        logger.info(f"🕐 Finding latest amendments for: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?amending_document ?title ?date ?type WHERE {{
                ?amending_document jolux:modifies <{document_uri}> ;
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
            
            recent_amendments = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    amendment = {
                        'uri': binding.get('amending_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    recent_amendments.append(amendment)
            
            logger.info(f"✅ Found {len(recent_amendments)} recent amendments")
            
            return {
                "target_document": document_uri,
                "recent_amendments": recent_amendments,
                "amendment_count": len(recent_amendments),
                "analysis_type": "latest_amendments",
                "reverse_chronological": True,
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Latest amendments analysis failed: {str(e)}")
            return {
                "target_document": document_uri,
                "recent_amendments": [],
                "amendment_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def analyze_amendment_chain(self, document_uri: str) -> Dict[str, Any]:
        """Analyze complete amendment chain for a document.
        
        Args:
            document_uri: URI of the document to analyze
            
        Returns:
            Dictionary with complete amendment chain analysis
        """
        logger.info(f"🔗 Analyzing amendment chain for: {document_uri}")
        
        try:
            # Get modification history (what modifies this document)
            history_result = self.find_modification_history(document_uri)
            
            # Get what this document modifies
            modifies_result = self.find_what_this_modifies(document_uri)
            
            # Get latest amendments
            latest_result = self.find_latest_amendments(document_uri)
            
            chain_analysis = {
                "central_document": document_uri,
                "modification_history": history_result,
                "documents_modified": modifies_result,
                "latest_amendments": latest_result,
                "total_modifications": history_result["modification_count"],
                "total_documents_modified": modifies_result["modification_count"],
                "analysis_type": "complete_amendment_chain",
                "query_successful": True
            }
            
            # Calculate amendment activity level
            total_activity = (history_result["modification_count"] + 
                            modifies_result["modification_count"])
            
            if total_activity == 0:
                activity_level = "inactive"
            elif total_activity < 5:
                activity_level = "low"
            elif total_activity < 15:
                activity_level = "moderate"
            else:
                activity_level = "high"
            
            chain_analysis["amendment_activity_level"] = activity_level
            
            logger.info(f"✅ Amendment chain analysis complete: {total_activity} total modifications")
            return chain_analysis
            
        except Exception as e:
            logger.error(f"❌ Amendment chain analysis failed: {str(e)}")
            return {
                "central_document": document_uri,
                "error": str(e),
                "query_successful": False
            }