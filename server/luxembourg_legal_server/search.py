"""
Luxembourg Legal Search Module
Simple working JOLUX search functions based on proven debug results.
"""

import logging
from typing import Dict, List, Any
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)


class LuxembourgSearch:
    """Simple working Luxembourg legal search using JOLUX ontology."""
    
    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
    
    def smart_keyword_search(self, keywords: str, limit: int = 500) -> Dict[str, Any]:
        """Smart keyword search that handles both single keywords and multi-word queries.
        
        Args:
            keywords: Can be single keyword ("SARL") or multi-word ("SARL société Luxembourg")
            limit: Maximum results
            
        Returns:
            Dictionary with documents found using smart keyword splitting and OR logic
        """
        logger.info(f"🧠 SMART KEYWORD SEARCH: '{keywords}' (limit: {limit})")
        
        try:
            # Clean and split keywords
            keyword_list = [kw.strip() for kw in keywords.split() if len(kw.strip()) >= 3]
            
            if not keyword_list:
                return {
                    "documents": [],
                    "total_found": 0,
                    "error": "No valid keywords (minimum 3 characters each)",
                    "query_successful": False
                }
            
            # Build OR conditions for each keyword
            filter_conditions = []
            for keyword in keyword_list:
                filter_conditions.append(f'regex(str(?title), "{keyword}", "i")')
            
            filter_clause = " || ".join(filter_conditions)
            
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            SELECT ?entity ?date ?title ?type WHERE {{
                ?entity jolux:dateDocument ?date ;
                        a ?type ;
                        jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
                FILTER({filter_clause})
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
                    }
                    
                    # Calculate relevance score based on keyword matches
                    title_lower = doc['title'].lower()
                    matches = sum(1 for kw in keyword_list if kw.lower() in title_lower)
                    doc['keyword_match_count'] = matches
                    doc['relevance_score'] = matches / len(keyword_list)
                    
                    documents.append(doc)
            
            # Sort by relevance (most keyword matches first), then by date
            documents.sort(key=lambda x: (x['relevance_score'], x['date']), reverse=True)
            
            logger.info(f"✅ Found {len(documents)} documents")
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "search_method": "smart_keyword_search",
                "keywords_used": keyword_list,
                "keywords_original": keywords,
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Smart search failed: {str(e)}")
            return {
                "documents": [],
                "total_found": 0,
                "error": str(e),
                "query_successful": False
            }

    def simple_title_search(self, keywords: str, limit: int = 500) -> Dict[str, Any]:
        """Legacy single keyword search - kept for compatibility.
        
        Args:
            keywords: Single precise legal keyword (e.g., "SARL", "fiscal")
            limit: Maximum results
            
        Returns:
            Dictionary with documents found using simple regex on jolux:title
        """
        logger.info(f"🔍 SIMPLE JOLUX SEARCH: '{keywords}' (limit: {limit})")
        
        try:
            # Proven working query pattern from debug tests
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            SELECT ?entity ?date ?title ?type WHERE {{
                ?entity jolux:dateDocument ?date ;
                        a ?type ;
                        jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
                FILTER(regex(str(?title), "{keywords}", "i"))
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
                    }
                    documents.append(doc)
            
            logger.info(f"✅ Found {len(documents)} documents")
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "search_method": "simple_jolux_title_search",
                "keywords_used": keywords,
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Simple search failed: {str(e)}")
            return {
                "documents": [],
                "total_found": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def identify_legal_domains(self, legal_question: str) -> List[Dict[str, Any]]:
        """Extract legal terms from questions without hardcoded mappings."""
        
        question_lower = legal_question.lower()
        
        # Extract meaningful words, filtering out common French words
        words = [word.strip("?.,!") for word in question_lower.split() if len(word) >= 3]
        legal_terms = [word for word in words if word not in ["comment", "quelles", "sont", "les", "pour", "dans", "avec", "une", "des", "qui", "que", "peut", "être", "aux", "sur", "par"]]
        
        return [{
            "analysis": f"Legal question: {legal_question}",
            "extracted_terms": legal_terms[:5],
            "guidance": "Choose precise legal keywords from these terms for JOLUX search"
        }]
    
    def progressive_search(self, initial_keywords: str, minimum_documents: int = 30) -> Dict[str, Any]:
        """Perform progressive search expansion until sufficient documents are found.
        
        Args:
            initial_keywords: Starting search keywords
            minimum_documents: Minimum number of documents required
            
        Returns:
            Combined search results from all expansions
        """
        logger.info(f"🔄 PROGRESSIVE SEARCH: '{initial_keywords}' (target: {minimum_documents} docs)")
        
        all_documents = []
        search_attempts = []
        
        # Search 1: Exact keywords
        result1 = self.simple_title_search(initial_keywords, limit=500)
        if result1["query_successful"]:
            all_documents.extend(result1["documents"])
            search_attempts.append({"keywords": initial_keywords, "found": len(result1["documents"])})
            logger.info(f"   🎯 Search 1 (exact): {len(result1['documents'])} documents")
        
        # If we have enough, return early
        if len(all_documents) >= minimum_documents:
            return self._combine_search_results(all_documents, search_attempts)
        
        # Search 2: Expanded keywords based on domain
        expanded_keywords = self._expand_keywords(initial_keywords)
        for expanded in expanded_keywords:
            result = self.simple_title_search(expanded, limit=500)
            if result["query_successful"]:
                new_docs = [doc for doc in result["documents"] 
                           if doc not in all_documents]  # Deduplicate
                all_documents.extend(new_docs)
                search_attempts.append({"keywords": expanded, "found": len(new_docs)})
                logger.info(f"   🔍 Search expansion '{expanded}': {len(new_docs)} new documents")
                
                if len(all_documents) >= minimum_documents:
                    break
        
        # Search 3: Broader terms if still insufficient
        if len(all_documents) < minimum_documents:
            broader_terms = self._get_broader_terms(initial_keywords)
            for broader in broader_terms:
                result = self.simple_title_search(broader, limit=500)
                if result["query_successful"]:
                    new_docs = [doc for doc in result["documents"] 
                               if doc not in all_documents]
                    all_documents.extend(new_docs)
                    search_attempts.append({"keywords": broader, "found": len(new_docs)})
                    logger.info(f"   🌐 Broader search '{broader}': {len(new_docs)} new documents")
                    
                    if len(all_documents) >= minimum_documents:
                        break
        
        logger.info(f"🎉 PROGRESSIVE SEARCH COMPLETE: {len(all_documents)} total documents found")
        return self._combine_search_results(all_documents, search_attempts)
    
    def _expand_keywords(self, keywords: str) -> List[str]:
        """Dynamic keyword expansion - let AI choose alternatives."""
        
        # No hardcoded expansions - return original keywords
        # AI should choose appropriate legal synonyms
        return [keywords]
    
    def _get_broader_terms(self, keywords: str) -> List[str]:
        """Dynamic broader terms - let AI choose broader concepts."""
        
        # No hardcoded broader terms - AI should choose
        # Return general legal terms only as last resort
        return ["droit", "loi"]
    
    def _combine_search_results(self, documents: List[Dict], attempts: List[Dict]) -> Dict[str, Any]:
        """Combine and deduplicate search results."""
        
        # Deduplicate by URI
        seen_uris = set()
        unique_documents = []
        for doc in documents:
            uri = doc.get('uri', '')
            if uri and uri not in seen_uris:
                seen_uris.add(uri)
                unique_documents.append(doc)
        
        return {
            "documents": unique_documents,
            "total_found": len(unique_documents),
            "search_attempts": attempts,
            "search_method": "progressive_expansion",
            "query_successful": True
        }
    
    def multi_field_search(self, keywords: str, limit: int = 500) -> Dict[str, Any]:
        """Enhanced multi-field search using JOLUX relationships and metadata.
        
        Args:
            keywords: Search keywords
            limit: Maximum results
            
        Returns:
            Dictionary with enhanced search results including relationships and metadata
        """
        logger.info(f"🔍 MULTI-FIELD JOLUX SEARCH: '{keywords}' (limit: {limit})")
        
        try:
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
                
                # Multi-field search strategy
                {{
                    FILTER(regex(str(?title), "{keywords}", "i"))
                }} UNION {{
                    ?entity jolux:basedOn ?base .
                    ?base jolux:isRealizedBy/jolux:title ?baseTitle .
                    FILTER(regex(str(?baseTitle), "{keywords}", "i"))
                }} UNION {{
                    FILTER(regex(str(?authority), "{keywords}", "i"))
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
                    documents.append(doc)
            
            logger.info(f"✅ Multi-field search found {len(documents)} documents")
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "search_method": "multi_field_jolux_enhanced",
                "fields_searched": ["title", "based_on_relationships", "authority"],
                "keywords_used": keywords,
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Multi-field search failed: {str(e)}")
            return {
                "documents": [],
                "total_found": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def discover_legal_relationships(self, document_uri: str, max_depth: int = 3) -> Dict[str, Any]:
        """Discover legal relationships and amendment chains for a document.
        
        Args:
            document_uri: URI of the document to analyze
            max_depth: Maximum relationship depth to explore
            
        Returns:
            Dictionary with discovered legal relationships
        """
        logger.info(f"🔗 LEGAL RELATIONSHIP DISCOVERY: {document_uri}")
        
        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?related ?title ?relationship ?date ?type WHERE {{
                {{
                    # Documents this one is based on (legal foundation)
                    <{document_uri}> jolux:basedOn+ ?related .
                    BIND("based_on" as ?relationship)
                }} UNION {{
                    # Documents that are based on this one (implementations)
                    ?related jolux:basedOn+ <{document_uri}> .
                    BIND("implements" as ?relationship)
                }} UNION {{
                    # Documents that are part of the same legal work
                    <{document_uri}> jolux:isMemberOf ?work .
                    ?related jolux:isMemberOf ?work .
                    FILTER(?related != <{document_uri}>)
                    BIND("same_work" as ?relationship)
                }}
                
                ?related jolux:isRealizedBy/jolux:title ?title ;
                         jolux:dateDocument ?date ;
                         a ?type .
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
                        'type': binding.get('type', {}).get('value', ''),
                    }
                    relationships.append(rel)
            
            logger.info(f"✅ Found {len(relationships)} legal relationships")
            
            return {
                "relationships": relationships,
                "total_found": len(relationships),
                "source_document": document_uri,
                "relationship_types": list(set([r["relationship"] for r in relationships])),
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Relationship discovery failed: {str(e)}")
            return {
                "relationships": [],
                "total_found": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def temporal_legal_analysis(self, document_uris: List[str]) -> Dict[str, Any]:
        """Analyze temporal aspects of legal documents.
        
        Args:
            document_uris: List of document URIs to analyze
            
        Returns:
            Dictionary with temporal analysis results
        """
        logger.info(f"📅 TEMPORAL LEGAL ANALYSIS: {len(document_uris)} documents")
        
        try:
            # Limit to prevent timeout
            uri_filter = " ".join([f"<{uri}>" for uri in document_uris[:20]])
            
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
            
            logger.info(f"✅ Temporal analysis complete: {len(timeline)} documents")
            
            return {
                "timeline": timeline,
                "total_analyzed": len(timeline),
                "analysis_type": "temporal_legal_analysis",
                "date_properties_used": ["document_date", "publication_date", "entry_force_date"],
                "query_successful": True
            }
            
        except Exception as e:
            logger.error(f"❌ Temporal analysis failed: {str(e)}")
            return {
                "timeline": [],
                "total_analyzed": 0,
                "error": str(e),
                "query_successful": False
            }
    
    def extract_authority_data(self, documents: List[Dict]) -> Dict[str, Any]:
        """Extract raw authority data without scoring or ranking.
        
        Args:
            documents: List of documents to extract authority data from
            
        Returns:
            Raw authority data for AI assessment
        """
        logger.info(f"⚖️ AUTHORITY DATA EXTRACTION: {len(documents)} documents")
        
        authority_data = []
        authority_types = {}
        document_types = {}
        
        for doc in documents:
            # Extract raw authority information without scoring
            authority = doc.get('authority', '')
            doc_type = doc.get('type', '')
            date_doc = doc.get('date', '')
            
            # Add years calculation without scoring
            years_old = None
            if date_doc:
                try:
                    import datetime
                    if 'T' in date_doc:
                        doc_date = datetime.datetime.fromisoformat(date_doc.replace('Z', '+00:00'))
                    else:
                        doc_date = datetime.datetime.strptime(date_doc[:10], '%Y-%m-%d')
                    now = datetime.datetime.now()
                    years_old = round((now - doc_date).days / 365.25, 1)
                except:
                    pass
            
            authority_info = {
                'uri': doc.get('uri', ''),
                'title': doc.get('title', ''),
                'authority': authority,
                'document_type': doc_type,
                'date': date_doc,
                'years_old': years_old,
                'publication_date': doc.get('publication_date', ''),
                'entry_force_date': doc.get('entry_force_date', ''),
                'based_on': doc.get('based_on', '')
            }
            authority_data.append(authority_info)
            
            # Count distributions for AI analysis
            auth_key = authority.split('/')[-1] if '/' in authority else authority
            authority_types[auth_key] = authority_types.get(auth_key, 0) + 1
            
            type_key = doc_type.split('#')[-1] if '#' in doc_type else doc_type
            document_types[type_key] = document_types.get(type_key, 0) + 1
        
        logger.info(f"✅ Authority data extraction complete: {len(authority_data)} documents")
        
        return {
            "documents_with_authority_data": authority_data,
            "authority_distribution": authority_types,
            "document_type_distribution": document_types,
            "total_documents": len(authority_data)
        }