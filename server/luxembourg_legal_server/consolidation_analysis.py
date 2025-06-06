"""
Luxembourg Legal Consolidation Analysis
MCP Tool for finding consolidated legal document versions using JOLUX ontology.
"""

import logging
from typing import Dict, List, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)


class ConsolidationAnalyzer:
    """Analyzes legal document consolidations using jolux:consolidates/language properties."""
    
    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def find_consolidated_versions(self, document_uri: str, limit: int = 50) -> Dict[str, Any]:
        """Find consolidated versions of a document.
        
        Args:
            document_uri: URI of the base document
            limit: Maximum number of consolidated versions to return
            
        Returns:
            Dictionary with consolidated versions
        """
        logger.info(f"📋 Finding consolidated versions for: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?consolidated_document ?title ?date ?type ?language WHERE {{
                ?consolidated_document jolux:consolidates <{document_uri}> ;
                                      jolux:dateDocument ?date ;
                                      a ?type ;
                                      jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
                OPTIONAL {{ ?consolidated_document jolux:language ?language }}
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            consolidated_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('consolidated_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                        'language': binding.get('language', {}).get('value', 'unknown'),
                    }
                    consolidated_docs.append(doc)
            
            logger.info(f"✅ Found {len(consolidated_docs)} consolidated versions")
            
            return {
                "base_document": document_uri,
                "consolidated_versions": consolidated_docs,
                "consolidation_count": len(consolidated_docs),
                "analysis_type": "consolidated_versions",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Consolidation analysis failed: {str(e)}")
            return {
                "base_document": document_uri,
                "consolidated_versions": [],
                "consolidation_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_consolidation_base(self, document_uri: str, limit: int = 50) -> Dict[str, Any]:
        """Find what base documents this consolidation is based on.
        
        Args:
            document_uri: URI of the consolidated document
            limit: Maximum number of base documents to return
            
        Returns:
            Dictionary with base documents for this consolidation
        """
        logger.info(f"📜 Finding consolidation base for: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?base_document ?title ?date ?type WHERE {{
                <{document_uri}> jolux:consolidates ?base_document .
                ?base_document jolux:dateDocument ?date ;
                              a ?type ;
                              jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            ORDER BY ?date
            LIMIT {limit}
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            base_docs = []
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('base_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    base_docs.append(doc)
            
            logger.info(f"✅ Found {len(base_docs)} base documents")
            
            return {
                "consolidated_document": document_uri,
                "base_documents": base_docs,
                "base_count": len(base_docs),
                "analysis_type": "consolidation_base",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Consolidation base analysis failed: {str(e)}")
            return {
                "consolidated_document": document_uri,
                "base_documents": [],
                "base_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def find_multilingual_versions(self, document_uri: str) -> Dict[str, Any]:
        """Find different language versions of a document.
        
        Args:
            document_uri: URI of the document
            
        Returns:
            Dictionary with multilingual versions
        """
        logger.info(f"🌍 Finding multilingual versions for: {document_uri}")
        
        try:
            # First, get the title of the main document to find related versions
            main_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT ?title WHERE {{
                <{document_uri}> jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
            }}
            LIMIT 1
            """
            
            self.sparql.setQuery(main_query)
            main_results = self.sparql.query().convert()
            
            if not main_results.get('results', {}).get('bindings'):
                return {
                    "document": document_uri,
                    "multilingual_versions": [],
                    "language_count": 0,
                    "error": "Could not find main document title",
                    "query_successful": False
                }
            
            main_title = main_results['results']['bindings'][0]['title']['value']
            
            # Find documents with similar titles in different languages
            multilingual_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            
            SELECT DISTINCT ?related_document ?title ?language ?date ?type WHERE {{
                ?related_document jolux:isRealizedBy ?expression ;
                                 jolux:language ?language ;
                                 jolux:dateDocument ?date ;
                                 a ?type .
                ?expression jolux:title ?title .
                FILTER(CONTAINS(?title, "{main_title.split()[0]}"))
            }}
            ORDER BY ?language
            LIMIT 20
            """
            
            self.sparql.setQuery(multilingual_query)
            results = self.sparql.query().convert()
            
            multilingual_docs = []
            languages = set()
            
            if 'results' in results and 'bindings' in results['results']:
                for binding in results['results']['bindings']:
                    doc = {
                        'uri': binding.get('related_document', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'language': binding.get('language', {}).get('value', 'unknown'),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    multilingual_docs.append(doc)
                    languages.add(doc['language'])
            
            logger.info(f"✅ Found {len(multilingual_docs)} versions in {len(languages)} languages")
            
            return {
                "document": document_uri,
                "multilingual_versions": multilingual_docs,
                "languages_available": list(languages),
                "language_count": len(languages),
                "version_count": len(multilingual_docs),
                "analysis_type": "multilingual_versions",
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Multilingual analysis failed: {str(e)}")
            return {
                "document": document_uri,
                "multilingual_versions": [],
                "language_count": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def get_current_effective_version(self, document_uri: str) -> Dict[str, Any]:
        """Get the most current effective version of a document.
        
        Args:
            document_uri: URI of the document
            
        Returns:
            Dictionary with current effective version information
        """
        logger.info(f"⚡ Finding current effective version for: {document_uri}")
        
        try:
            # Check for consolidated versions first
            consolidated_result = self.find_consolidated_versions(document_uri, limit=5)
            
            # Check for multilingual versions
            multilingual_result = self.find_multilingual_versions(document_uri)
            
            current_version = {
                "original_document": document_uri,
                "consolidated_versions": consolidated_result,
                "multilingual_versions": multilingual_result,
                "analysis_type": "current_effective_version",
                "query_successful": True
            }
            
            # Determine the most current version
            if consolidated_result["consolidation_count"] > 0:
                # Most recent consolidation is likely the current version
                most_recent_consolidation = consolidated_result["consolidated_versions"][0]
                current_version["recommended_version"] = most_recent_consolidation
                current_version["recommendation_reason"] = "Most recent consolidated version"
            else:
                # Original document is the current version
                current_version["recommended_version"] = {
                    "uri": document_uri,
                    "type": "original"
                }
                current_version["recommendation_reason"] = "No consolidations found, original document is current"
            
            logger.info(f"✅ Current version analysis complete")
            return current_version
            
        except Exception as e:
            logger.error(f"❌ Current version analysis failed: {str(e)}")
            return {
                "original_document": document_uri,
                "error": str(e),
                "query_successful": False
            }