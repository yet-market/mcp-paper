"""
MCP Tools for Luxembourg Legal Intelligence.
6 specialized tools leveraging proven JOLUX capabilities.
"""

import logging
from typing import Dict, List, Any
from SPARQLWrapper import SPARQLWrapper
from .content_processor import ContentProcessor
from .config import Config

logger = logging.getLogger(__name__)


class LuxembourgLegalTools:
    """Collection of specialized legal intelligence tools."""
    
    def __init__(self, sparql: SPARQLWrapper):
        """Initialize tools with SPARQL connection."""
        self.sparql = sparql
        self.content_processor = ContentProcessor(pdf_timeout=Config.PDF_TIMEOUT)
    
    def search_documents(self, keyword: str, limit: int = Config.DEFAULT_SEARCH_LIMIT) -> Dict[str, Any]:
        """
        Search Luxembourg legal documents using proven single-keyword strategy.
        
        Args:
            keyword: Single precise keyword (e.g., "SARL", "société", "règlement")
            limit: Maximum results (50-100 recommended for context safety)
        
        Returns:
            Documents with complete JOLUX metadata for AI analysis
        """
        logger.info(f"🔍 SEARCHING DOCUMENTS: '{keyword}' (limit: {limit})")
        
        try:
            # Proven single-keyword SPARQL query with complete metadata
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?entity ?title ?date ?type ?subject ?authority WHERE {{
                ?entity jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
                ?entity jolux:dateDocument ?date .
                OPTIONAL {{ ?entity jolux:typeDocument ?type }}
                OPTIONAL {{ ?entity jolux:subjectLevel1 ?subject }}
                OPTIONAL {{ ?entity jolux:responsibilityOf ?authority }}
                FILTER(regex(str(?title), "{keyword}", "i"))
            }}
            ORDER BY DESC(?date)
            LIMIT {min(limit, Config.MAX_SEARCH_LIMIT)}
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
                        'subject': binding.get('subject', {}).get('value', ''),
                        'authority': binding.get('authority', {}).get('value', '')
                    }
                    documents.append(doc)
            
            logger.info(f"✅ Found {len(documents)} documents")
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "keyword_used": keyword,
                "search_strategy": "single_keyword_precision",
                "metadata_included": ["title", "date", "type", "subject", "authority"]
            }
            
        except Exception as e:
            logger.error(f"❌ Document search failed: {str(e)}")
            return {"error": f"Document search failed: {str(e)}"}
    
    def get_citations(self, document_uri: str) -> Dict[str, Any]:
        """
        Get complete citation network using proven jolux:cites relationships.
        
        Args:
            document_uri: URI of document from search results
        
        Returns:
            Bidirectional citation network with metadata
        """
        logger.info(f"📚 GETTING CITATIONS: {document_uri}")
        
        try:
            # Get what this document cites (outbound)
            outbound_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?cited ?title ?date ?type WHERE {{
                <{document_uri}> jolux:cites ?cited .
                ?cited jolux:isRealizedBy/jolux:title ?title .
                ?cited jolux:dateDocument ?date .
                OPTIONAL {{ ?cited jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(outbound_query)
            outbound_results = self.sparql.query().convert()
            
            # Get what cites this document (inbound)
            inbound_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?citing ?title ?date ?type WHERE {{
                ?citing jolux:cites <{document_uri}> .
                ?citing jolux:isRealizedBy/jolux:title ?title .
                ?citing jolux:dateDocument ?date .
                OPTIONAL {{ ?citing jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(inbound_query)
            inbound_results = self.sparql.query().convert()
            
            # Process results
            outbound_citations = []
            if 'results' in outbound_results and 'bindings' in outbound_results['results']:
                for binding in outbound_results['results']['bindings']:
                    citation = {
                        'uri': binding.get('cited', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    outbound_citations.append(citation)
            
            inbound_citations = []
            if 'results' in inbound_results and 'bindings' in inbound_results['results']:
                for binding in inbound_results['results']['bindings']:
                    citation = {
                        'uri': binding.get('citing', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    inbound_citations.append(citation)
            
            logger.info(f"✅ Found {len(outbound_citations)} outbound, {len(inbound_citations)} inbound citations")
            
            return {
                "document_uri": document_uri,
                "outbound_citations": outbound_citations,
                "inbound_citations": inbound_citations,
                "outbound_count": len(outbound_citations),
                "inbound_count": len(inbound_citations),
                "total_network_size": len(outbound_citations) + len(inbound_citations)
            }
            
        except Exception as e:
            logger.error(f"❌ Citation analysis failed: {str(e)}")
            return {"error": f"Citation analysis failed: {str(e)}"}
    
    def get_amendments(self, document_uri: str) -> Dict[str, Any]:
        """
        Get complete amendment history using proven jolux:modifies relationships.
        
        Args:
            document_uri: URI of document from search results
        
        Returns:
            Complete modification timeline with metadata
        """
        logger.info(f"📝 GETTING AMENDMENTS: {document_uri}")
        
        try:
            # Get what this document modifies
            modifies_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?modified ?title ?date ?type WHERE {{
                <{document_uri}> jolux:modifies ?modified .
                ?modified jolux:isRealizedBy/jolux:title ?title .
                ?modified jolux:dateDocument ?date .
                OPTIONAL {{ ?modified jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(modifies_query)
            modifies_results = self.sparql.query().convert()
            
            # Get what modifies this document
            modified_by_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?modifier ?title ?date ?type WHERE {{
                ?modifier jolux:modifies <{document_uri}> .
                ?modifier jolux:isRealizedBy/jolux:title ?title .
                ?modifier jolux:dateDocument ?date .
                OPTIONAL {{ ?modifier jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(modified_by_query)
            modified_by_results = self.sparql.query().convert()
            
            # Process results
            modifications_made = []
            if 'results' in modifies_results and 'bindings' in modifies_results['results']:
                for binding in modifies_results['results']['bindings']:
                    modification = {
                        'uri': binding.get('modified', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    modifications_made.append(modification)
            
            modifications_received = []
            if 'results' in modified_by_results and 'bindings' in modified_by_results['results']:
                for binding in modified_by_results['results']['bindings']:
                    modification = {
                        'uri': binding.get('modifier', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    modifications_received.append(modification)
            
            logger.info(f"✅ Found {len(modifications_made)} made, {len(modifications_received)} received modifications")
            
            return {
                "document_uri": document_uri,
                "modifications_made": modifications_made,
                "modifications_received": modifications_received,
                "modifications_made_count": len(modifications_made),
                "modifications_received_count": len(modifications_received),
                "total_modification_activity": len(modifications_made) + len(modifications_received)
            }
            
        except Exception as e:
            logger.error(f"❌ Amendment analysis failed: {str(e)}")
            return {"error": f"Amendment analysis failed: {str(e)}"}
    
    def check_legal_status(self, document_uri: str) -> Dict[str, Any]:
        """
        Check current legal validity using proven jolux:repeals and jolux:consolidates.
        
        Args:
            document_uri: URI of document from search results
        
        Returns:
            Legal currency status with consolidation information
        """
        logger.info(f"⚖️ CHECKING LEGAL STATUS: {document_uri}")
        
        try:
            # Check if this document has been repealed
            repealed_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?repealer ?title ?date WHERE {{
                ?repealer jolux:repeals <{document_uri}> .
                ?repealer jolux:isRealizedBy/jolux:title ?title .
                ?repealer jolux:dateDocument ?date .
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(repealed_query)
            repealed_results = self.sparql.query().convert()
            
            # Check what this document repeals
            repeals_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?repealed ?title ?date WHERE {{
                <{document_uri}> jolux:repeals ?repealed .
                ?repealed jolux:isRealizedBy/jolux:title ?title .
                ?repealed jolux:dateDocument ?date .
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(repeals_query)
            repeals_results = self.sparql.query().convert()
            
            # Check consolidations
            consolidations_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?consolidated ?title ?date WHERE {{
                <{document_uri}> jolux:consolidates ?consolidated .
                ?consolidated jolux:isRealizedBy/jolux:title ?title .
                ?consolidated jolux:dateDocument ?date .
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(consolidations_query)
            consolidations_results = self.sparql.query().convert()
            
            # Process results
            repealed_by = []
            if 'results' in repealed_results and 'bindings' in repealed_results['results']:
                for binding in repealed_results['results']['bindings']:
                    repeal = {
                        'uri': binding.get('repealer', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', '')
                    }
                    repealed_by.append(repeal)
            
            repeals = []
            if 'results' in repeals_results and 'bindings' in repeals_results['results']:
                for binding in repeals_results['results']['bindings']:
                    repeal = {
                        'uri': binding.get('repealed', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', '')
                    }
                    repeals.append(repeal)
            
            consolidations = []
            if 'results' in consolidations_results and 'bindings' in consolidations_results['results']:
                for binding in consolidations_results['results']['bindings']:
                    consolidation = {
                        'uri': binding.get('consolidated', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', '')
                    }
                    consolidations.append(consolidation)
            
            # Determine legal status
            legal_status = "active"
            if repealed_by:
                legal_status = "repealed"
            elif consolidations:
                legal_status = "consolidated"
            
            logger.info(f"✅ Legal status: {legal_status}, {len(consolidations)} consolidations")
            
            return {
                "document_uri": document_uri,
                "legal_status": legal_status,
                "repealed_by": repealed_by,
                "repeals": repeals,
                "consolidations": consolidations,
                "repeal_count": len(repealed_by),
                "repeals_count": len(repeals),
                "consolidation_count": len(consolidations),
                "is_active": legal_status == "active"
            }
            
        except Exception as e:
            logger.error(f"❌ Legal status check failed: {str(e)}")
            return {"error": f"Legal status check failed: {str(e)}"}
    
    def get_relationships(self, document_uri: str) -> Dict[str, Any]:
        """
        Get legal foundations and implementing acts using proven JOLUX relationships.
        
        Args:
            document_uri: URI of document from search results
        
        Returns:
            Complete legal relationship network and hierarchy
        """
        logger.info(f"🔗 GETTING RELATIONSHIPS: {document_uri}")
        
        try:
            # Get what this document is based on (foundations)
            foundations_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?foundation ?title ?date ?type WHERE {{
                <{document_uri}> jolux:basedOn ?foundation .
                ?foundation jolux:isRealizedBy/jolux:title ?title .
                ?foundation jolux:dateDocument ?date .
                OPTIONAL {{ ?foundation jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(foundations_query)
            foundations_results = self.sparql.query().convert()
            
            # Get what is based on this document (implementations)
            implementations_query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?implementation ?title ?date ?type WHERE {{
                ?implementation jolux:basedOn <{document_uri}> .
                ?implementation jolux:isRealizedBy/jolux:title ?title .
                ?implementation jolux:dateDocument ?date .
                OPTIONAL {{ ?implementation jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            """
            
            self.sparql.setQuery(implementations_query)
            implementations_results = self.sparql.query().convert()
            
            # Process results
            foundations = []
            if 'results' in foundations_results and 'bindings' in foundations_results['results']:
                for binding in foundations_results['results']['bindings']:
                    foundation = {
                        'uri': binding.get('foundation', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    foundations.append(foundation)
            
            implementations = []
            if 'results' in implementations_results and 'bindings' in implementations_results['results']:
                for binding in implementations_results['results']['bindings']:
                    implementation = {
                        'uri': binding.get('implementation', {}).get('value', ''),
                        'title': binding.get('title', {}).get('value', ''),
                        'date': binding.get('date', {}).get('value', ''),
                        'type': binding.get('type', {}).get('value', '')
                    }
                    implementations.append(implementation)
            
            logger.info(f"✅ Found {len(foundations)} foundations, {len(implementations)} implementations")
            
            return {
                "document_uri": document_uri,
                "foundations": foundations,
                "implementations": implementations,
                "foundation_count": len(foundations),
                "implementation_count": len(implementations),
                "total_relationship_network": len(foundations) + len(implementations)
            }
            
        except Exception as e:
            logger.error(f"❌ Relationship analysis failed: {str(e)}")
            return {"error": f"Relationship analysis failed: {str(e)}"}
    
    def extract_content(self, document_uris: List[str], max_documents: int = Config.MAX_DOCUMENTS_PER_EXTRACTION, prefer_html: bool = Config.PREFER_HTML_EXTRACTION) -> Dict[str, Any]:
        """
        Extract real legal text from Luxembourg documents using proven HTML/PDF extraction.
        
        Args:
            document_uris: List of document URIs from search results
            max_documents: Maximum documents to extract (default 3 for context safety)
            prefer_html: Try HTML first (faster) then fallback to PDF
        
        Returns:
            Complete legal content with text, metadata, and document analysis
        """
        logger.info(f"📄 EXTRACTING CONTENT: {len(document_uris)} documents (max: {max_documents})")
        
        try:
            # Limit documents to avoid context explosion
            limited_uris = document_uris[:max_documents]
            
            extracted_documents = []
            success_count = 0
            failed_count = 0
            
            for i, uri in enumerate(limited_uris, 1):
                logger.info(f"📝 Processing document {i}/{len(limited_uris)}: {uri}")
                
                # Extract content using proven HTML/PDF fallback algorithm
                content = self.content_processor.extract_entity_content(uri, prefer_html=prefer_html)
                
                if content:
                    # Successfully extracted content
                    success_count += 1
                    
                    # Prepare extracted document info
                    doc_info = {
                        'uri': uri,
                        'title': content.get('title', 'Unknown Title'),
                        'content_type': content.get('content_type', 'unknown'),
                        'source_url': content.get('source_url', uri),
                        'text_length': len(content.get('text', '')),
                        'text_preview': content.get('text', '')[:500] + ('...' if len(content.get('text', '')) > 500 else ''),
                        'full_text': content.get('text', ''),  # Full text for AI analysis
                        'summary': content.get('summary', ''),
                        'document_type': content.get('document_type', 'unknown'),
                        'legal_concepts': content.get('legal_concepts', []),
                        'structure': content.get('structure', {}),
                        'metadata': content.get('metadata', {}),
                        'entity_uri': content.get('entity_uri', uri),
                        'extraction_status': 'success',
                        'extraction_method': f"{content.get('content_type', 'unknown')}_with_fallback"
                    }
                    
                    extracted_documents.append(doc_info)
                    logger.info(f"   ✅ Successfully extracted {doc_info['text_length']} characters from {doc_info['content_type'].upper()}")
                    
                else:
                    # Extraction failed, try to get basic metadata from SPARQL
                    failed_count += 1
                    logger.warning(f"   ❌ Content extraction failed, getting metadata only")
                    
                    # Get basic document information as fallback
                    doc_query = f"""
                    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                    SELECT ?title ?date ?type WHERE {{
                        <{uri}> jolux:isRealizedBy/jolux:title ?title .
                        <{uri}> jolux:dateDocument ?date .
                        OPTIONAL {{ <{uri}> jolux:typeDocument ?type }}
                    }}
                    """
                    
                    self.sparql.setQuery(doc_query)
                    results = self.sparql.query().convert()
                    
                    if 'results' in results and 'bindings' in results['results']:
                        binding = results['results']['bindings'][0] if results['results']['bindings'] else {}
                        doc_info = {
                            'uri': uri,
                            'title': binding.get('title', {}).get('value', 'Unknown Title'),
                            'date': binding.get('date', {}).get('value', ''),
                            'type': binding.get('type', {}).get('value', ''),
                            'content_url': uri,
                            'text_length': 0,
                            'extraction_status': 'failed',
                            'extraction_method': 'metadata_only_fallback',
                            'error': 'Both HTML and PDF extraction failed'
                        }
                        extracted_documents.append(doc_info)
            
            logger.info(f"✅ EXTRACTION COMPLETE: {success_count} successful, {failed_count} failed")
            
            return {
                "extracted_documents": extracted_documents,
                "total_requested": len(document_uris),
                "total_processed": len(extracted_documents),
                "success_count": success_count,
                "failed_count": failed_count,
                "extraction_strategy": f"{'HTML first' if prefer_html else 'PDF first'} with fallback",
                "content_available": success_count > 0,
                "summary": f"Successfully extracted content from {success_count}/{len(limited_uris)} documents"
            }
            
        except Exception as e:
            logger.error(f"❌ Content extraction failed: {str(e)}")
            return {"error": f"Content extraction failed: {str(e)}"}