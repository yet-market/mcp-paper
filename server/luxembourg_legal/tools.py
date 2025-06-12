"""
MCP Tools for Luxembourg Legal Intelligence - Streamlined Workflow.
Simple, focused tools following the proven foundation discovery workflow.
Updated to return data matching Pydantic model field names for structured JSON output.
"""

import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache
from SPARQLWrapper import SPARQLWrapper
from .config import Config

logger = logging.getLogger(__name__)


class LuxembourgLegalTools:
    """Streamlined legal discovery workflow tools with structured JSON responses."""

    def __init__(self, sparql: SPARQLWrapper):
        """Initialize tools with SPARQL connection."""
        self.sparql = sparql
        # Initialize content processor for extraction
        try:
            from .content_processor import ContentProcessor
            self.content_processor = ContentProcessor()
            logger.info("✅ Content processor initialized for document extraction")
        except ImportError as e:
            logger.warning(f"⚠️ Content processor not available: {e}")
            self.content_processor = None

    def find_most_cited_laws(self, keywords: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        STEP 1A: Find laws that other laws reference a lot = important foundational laws.
        Returns data matching CitedLawItem model.
        """
        logger.info(f"📚 FINDING MOST CITED LAWS: {keywords}")

        try:
            # Build keyword filter
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(f'CONTAINS(LCASE(?title), "{keyword.lower()}")')
            filter_clause = " || ".join(keyword_filters) if keyword_filters else "true"

            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {{
                ?citing_doc jolux:cites ?cited_doc .
                ?cited_doc jolux:isRealizedBy ?expr .
                ?expr jolux:title ?title .
                ?cited_doc jolux:dateDocument ?date .
                FILTER({filter_clause})
            }}
            GROUP BY ?cited_doc ?title ?date
            ORDER BY DESC(?citation_count)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            laws = []
            for b in results.get("results", {}).get("bindings", []):
                # Return data exactly matching the SPARQL query field names
                laws.append({
                    "cited_doc": b["cited_doc"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "citation_count": int(b["citation_count"]["value"])
                })

            logger.info(f"✅ Found {len(laws)} most cited laws")
            return {
                "laws": laws,
                "total_found": len(laws),
                "keywords": keywords,
                "method": "citation_analysis",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Citation analysis failed: {e}")
            return {"error": f"Citation analysis failed: {e}", "success": False, "laws": [], "keywords": keywords, "method": "citation_analysis", "total_found": 0}

    def find_most_changed_laws(self, keywords: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        STEP 1B: Find laws that get updated frequently = active/important laws.
        Returns data matching ModifiedLawItem model.
        """
        logger.info(f"🔄 FINDING MOST CHANGED LAWS: {keywords}")

        try:
            # Build keyword filter
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(f'CONTAINS(LCASE(?title), "{keyword.lower()}")')
            filter_clause = " || ".join(keyword_filters) if keyword_filters else "true"

            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?modified_doc ?title ?date (COUNT(?modifier) as ?modification_count) WHERE {{
                ?modifier jolux:modifies ?modified_doc .
                ?modified_doc jolux:isRealizedBy ?expr .
                ?expr jolux:title ?title .
                ?modified_doc jolux:dateDocument ?date .
                FILTER({filter_clause})
            }}
            GROUP BY ?modified_doc ?title ?date
            ORDER BY DESC(?modification_count)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            laws = []
            for b in results.get("results", {}).get("bindings", []):
                # Return data exactly matching the SPARQL query field names
                laws.append({
                    "modified_doc": b["modified_doc"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "modification_count": int(b["modification_count"]["value"])
                })

            logger.info(f"✅ Found {len(laws)} most changed laws")
            return {
                "laws": laws,
                "total_found": len(laws),
                "keywords": keywords,
                "method": "modification_analysis",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Modification analysis failed: {e}")
            return {"error": f"Modification analysis failed: {e}", "success": False, "laws": [], "keywords": keywords, "method": "modification_analysis", "total_found": 0}

    def find_newest_active_laws(self, keywords: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        STEP 1C: Find recent laws that haven't been canceled = current legal framework.
        Returns data matching ActiveLawItem model.
        """
        logger.info(f"📅 FINDING NEWEST ACTIVE LAWS: {keywords}")

        try:
            # Build keyword filter
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(f'CONTAINS(LCASE(?title), "{keyword.lower()}")')
            filter_clause = " || ".join(keyword_filters) if keyword_filters else "true"

            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?doc ?title ?date ?type_doc WHERE {{
                ?doc jolux:isRealizedBy ?expr .
                ?expr jolux:title ?title .
                ?doc jolux:dateDocument ?date .
                OPTIONAL {{ ?doc jolux:typeDocument ?type_doc }}
                FILTER({filter_clause})
                FILTER NOT EXISTS {{ ?repealer jolux:repeals ?doc }}
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            laws = []
            for b in results.get("results", {}).get("bindings", []):
                # Return data exactly matching the SPARQL query field names
                laws.append({
                    "doc": b["doc"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type_doc": b.get("type_doc", {}).get("value", None)
                })

            logger.info(f"✅ Found {len(laws)} newest active laws")
            return {
                "laws": laws,
                "total_found": len(laws),
                "keywords": keywords,
                "method": "recency_analysis",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Active laws analysis failed: {e}")
            return {"error": f"Active laws analysis failed: {e}", "success": False, "laws": [], "keywords": keywords, "method": "recency_analysis", "total_found": 0}

    def find_highest_authority_laws(self, keywords: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        STEP 1D: Find LOI and CODE documents = most powerful legal authority.
        Returns data matching HighestAuthorityLawItem model.
        """
        logger.info(f"⚖️ FINDING HIGHEST AUTHORITY LAWS: {keywords}")

        try:
            # Build keyword filter
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(f'CONTAINS(LCASE(?title), "{keyword.lower()}")')
            filter_clause = " || ".join(keyword_filters) if keyword_filters else "true"

            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?doc ?title ?date ?type_doc WHERE {{
                ?doc jolux:isRealizedBy ?expr .
                ?expr jolux:title ?title .
                ?doc jolux:dateDocument ?date .
                ?doc jolux:typeDocument ?type_doc .
                FILTER({filter_clause})
                FILTER(CONTAINS(STR(?type_doc), "LOI") || CONTAINS(STR(?type_doc), "CODE"))
            }}
            ORDER BY ?date
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            laws = []
            for b in results.get("results", {}).get("bindings", []):
                # Return data exactly matching the SPARQL query field names
                laws.append({
                    "doc": b["doc"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type_doc": b["type_doc"]["value"]
                })

            logger.info(f"✅ Found {len(laws)} highest authority laws")
            return {
                "laws": laws,
                "total_found": len(laws),
                "keywords": keywords,
                "method": "authority_analysis",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Authority analysis failed: {e}")
            return {"error": f"Authority analysis failed: {e}", "success": False, "laws": [], "keywords": keywords, "method": "authority_analysis", "total_found": 0}

    def compare_results(self, result_sets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        STEP 2: Compare results from multiple discovery methods to find overlaps and rank importance.
        Returns data matching CompareResultsResponse model.
        """
        logger.info(f"🔍 COMPARING RESULTS from {len(result_sets)} methods")

        try:
            # Collect all laws with their discovery methods
            all_laws = {}
            method_names = []

            for result_set in result_sets:
                if not result_set.get("success", False):
                    continue

                method = result_set.get("method", "unknown")
                method_names.append(method)

                for law in result_set.get("laws", []):
                    # Extract URI from different field names based on the method
                    uri = None
                    if "cited_doc" in law:
                        uri = law["cited_doc"]
                    elif "modified_doc" in law:
                        uri = law["modified_doc"]
                    elif "doc" in law:
                        uri = law["doc"]
                    elif "uri" in law:
                        uri = law["uri"]
                    
                    if not uri:
                        continue

                    if uri not in all_laws:
                        all_laws[uri] = {
                            "uri": uri,
                            "title": law["title"],
                            "date": law["date"],
                            "discovery_methods": [],
                            "importance_scores": [],
                            "total_score": 0,
                            "method_count": 0
                        }

                    # Add this discovery method
                    all_laws[uri]["discovery_methods"].append(method)
                    
                    # Calculate importance score based on the method
                    if "citation_count" in law:
                        score = law["citation_count"] * 10
                    elif "modification_count" in law:
                        score = law["modification_count"] * 5
                    else:
                        score = 10  # Base score for other methods
                    
                    all_laws[uri]["importance_scores"].append(score)
                    all_laws[uri]["method_count"] = len(all_laws[uri]["discovery_methods"])

            # Calculate consolidated scores
            for law in all_laws.values():
                # Base score from importance scores
                law["total_score"] = sum(law["importance_scores"])

                # Bonus for appearing in multiple methods (very important!)
                if law["method_count"] >= 3:
                    law["total_score"] += 200  # Appears in 3+ methods = super important
                elif law["method_count"] >= 2:
                    law["total_score"] += 100  # Appears in 2+ methods = very important

                # Determine confidence level
                if law["method_count"] >= 3:
                    law["confidence"] = "very_high"
                elif law["method_count"] >= 2:
                    law["confidence"] = "high"
                else:
                    law["confidence"] = "medium"

            # Sort by total score
            ranked_laws = sorted(all_laws.values(), key=lambda x: x["total_score"], reverse=True)

            # Statistics
            multi_method_laws = [law for law in ranked_laws if law["method_count"] >= 2]
            high_confidence_laws = [law for law in ranked_laws if law["confidence"] in ["high", "very_high"]]

            logger.info(f"✅ Comparison complete: {len(ranked_laws)} total laws, {len(multi_method_laws)} found by multiple methods")

            return {
                "ranked_laws": ranked_laws,
                "multi_method_laws": multi_method_laws,
                "high_confidence_laws": high_confidence_laws,
                "statistics": {
                    "total_laws": len(ranked_laws),
                    "multi_method_count": len(multi_method_laws),
                    "high_confidence_count": len(high_confidence_laws),
                    "methods_used": method_names,
                    "method_count": len(method_names)
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Results comparison failed: {e}")
            return {
                "error": f"Results comparison failed: {e}", 
                "success": False,
                "ranked_laws": [],
                "multi_method_laws": [],
                "high_confidence_laws": [],
                "statistics": {
                    "total_laws": 0,
                    "multi_method_count": 0,
                    "high_confidence_count": 0,
                    "methods_used": [],
                    "method_count": 0
                }
            }

    def check_connections(self, document_uris: List[str]) -> Dict[str, Any]:
        """
        STEP 2B: Check how important laws connect to each other through citations.
        Returns data matching CheckConnectionsResponse model.
        """
        logger.info(f"🔗 CHECKING CONNECTIONS between {len(document_uris)} laws")

        try:
            connections = []
            connection_matrix = {}

            for uri in document_uris:
                # Find outbound citations (what this law references)
                outbound_query = f"""
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT ?cited ?title ?date ?type WHERE {{
                    <{uri}> jolux:cites ?cited .
                    ?cited jolux:isRealizedBy/jolux:title ?title .
                    ?cited jolux:dateDocument ?date .
                    OPTIONAL {{ ?cited jolux:typeDocument ?type }}
                }}
                ORDER BY DESC(?date)
                """

                self.sparql.setQuery(outbound_query)
                results = self.sparql.query().convert()

                for b in results.get("results", {}).get("bindings", []):
                    cited_uri = b["cited"]["value"]

                    # Check if this citation is to another law in our important list
                    if cited_uri in document_uris:
                        connection = {
                            "from_uri": uri,
                            "to_uri": cited_uri,
                            "to_title": b["title"]["value"],
                            "to_date": b["date"]["value"],
                            "to_type": b.get("type", {}).get("value", ""),
                            "relationship": "cites",
                            "direction": "outbound"
                        }
                        connections.append(connection)

                        # Build connection matrix for analysis
                        if uri not in connection_matrix:
                            connection_matrix[uri] = {"outbound": [], "inbound": []}
                        connection_matrix[uri]["outbound"].append(cited_uri)

            # Find most connected laws
            connection_counts = []
            for uri in document_uris:
                outbound_count = len(connection_matrix.get(uri, {}).get("outbound", []))
                inbound_count = len([c for c in connections if c["to_uri"] == uri])
                total_connections = outbound_count + inbound_count

                connection_counts.append({
                    "uri": uri,
                    "outbound_count": outbound_count,
                    "inbound_count": inbound_count,
                    "total_connections": total_connections
                })

            # Sort by total connections
            most_connected = sorted(connection_counts, 
                                    key=lambda x: x["total_connections"], 
                                    reverse=True)

            logger.info(f"✅ Found {len(connections)} connections between important laws")

            return {
                "connections": connections,
                "connection_matrix": connection_matrix,
                "most_connected_laws": most_connected,
                "statistics": {
                    "total_connections": len(connections),
                    "laws_analyzed": len(document_uris),
                    "connected_laws": len([uri for uri in document_uris if any(c.get("uri") == uri and c.get("total_connections", 0) > 0 for c in connection_counts)])
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Connection analysis failed: {e}")
            return {
                "error": f"Connection analysis failed: {e}", 
                "success": False,
                "connections": [],
                "connection_matrix": {},
                "most_connected_laws": [],
                "statistics": {
                    "total_connections": 0,
                    "laws_analyzed": len(document_uris),
                    "connected_laws": 0
                }
            }

    def find_what_law_references(self, document_uri: str, limit: int = 20) -> Dict[str, Any]:
        """
        STEP 3A: Find what this important law points to (its legal foundations).
        Returns data matching FindWhatLawReferencesResponse model.
        """
        logger.info(f"📚 FINDING WHAT LAW REFERENCES: {document_uri}")

        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?cited ?title ?date ?type WHERE {{
                <{document_uri}> jolux:cites ?cited .
                ?cited jolux:isRealizedBy/jolux:title ?title .
                ?cited jolux:dateDocument ?date .
                OPTIONAL {{ ?cited jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            references = []
            for b in results.get("results", {}).get("bindings", []):
                # Map cited -> uri and add relationship field for model compatibility
                references.append({
                    "uri": b["cited"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type": b.get("type", {}).get("value", ""),
                    "relationship": "cites"
                })

            logger.info(f"✅ Found {len(references)} outbound references")

            return {
                "source_document": document_uri,
                "references": references,
                "total_found": len(references),
                "relationship_type": "outbound_citations",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Outbound reference analysis failed: {e}")
            return {
                "error": f"Outbound reference analysis failed: {e}", 
                "success": False,
                "source_document": document_uri,
                "references": [],
                "total_found": 0,
                "relationship_type": "outbound_citations"
            }

    def find_what_references_law(self, document_uri: str, limit: int = 20) -> Dict[str, Any]:
        """
        STEP 3B: Find what other laws point to this one (its legal impact).
        Returns data matching FindWhatReferencesLawResponse model.
        """
        logger.info(f"🎯 FINDING WHAT REFERENCES LAW: {document_uri}")

        try:
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?citing ?title ?date ?type WHERE {{
                ?citing jolux:cites <{document_uri}> .
                ?citing jolux:isRealizedBy/jolux:title ?title .
                ?citing jolux:dateDocument ?date .
                OPTIONAL {{ ?citing jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            citing_laws = []
            for b in results.get("results", {}).get("bindings", []):
                # Map citing -> uri and add relationship field for model compatibility
                citing_laws.append({
                    "uri": b["citing"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type": b.get("type", {}).get("value", ""),
                    "relationship": "cited_by"
                })

            logger.info(f"✅ Found {len(citing_laws)} inbound citations")

            return {
                "target_document": document_uri,
                "citing_laws": citing_laws,
                "total_found": len(citing_laws),
                "relationship_type": "inbound_citations",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Inbound citation analysis failed: {e}")
            return {
                "error": f"Inbound citation analysis failed: {e}", 
                "success": False,
                "target_document": document_uri,
                "citing_laws": [],
                "total_found": 0,
                "relationship_type": "inbound_citations"
            }

    def find_amendment_chain(self, document_uri: str, limit: int = 20) -> Dict[str, Any]:
        """
        STEP 3C: Find how this law has changed over time (amendment history).
        Returns data matching FindAmendmentChainResponse model.
        """
        logger.info(f"📝 FINDING AMENDMENT CHAIN: {document_uri}")

        try:
            # Get both incoming and outgoing modifications
            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?neighbor ?title ?date ?type ?direction WHERE {{
              {{ 
                <{document_uri}> jolux:modifies ?neighbor .
                BIND("outgoing" AS ?direction)
              }}
              UNION
              {{ 
                ?neighbor jolux:modifies <{document_uri}> .
                BIND("incoming" AS ?direction)
              }}
              ?neighbor jolux:isRealizedBy/jolux:title ?title .
              ?neighbor jolux:dateDocument ?date .
              OPTIONAL {{ ?neighbor jolux:typeDocument ?type }}
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            amendments = []
            incoming_amendments = []
            outgoing_amendments = []

            for b in results.get("results", {}).get("bindings", []):
                # Map neighbor -> uri for model compatibility
                amendment = {
                    "uri": b["neighbor"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type": b.get("type", {}).get("value", ""),
                    "direction": b["direction"]["value"]
                }

                amendments.append(amendment)

                if amendment["direction"] == "incoming":
                    incoming_amendments.append(amendment)
                else:
                    outgoing_amendments.append(amendment)

            # Calculate amendment activity score
            activity_score = len(incoming_amendments) * 10 + len(outgoing_amendments) * 5

            logger.info(f"✅ Found {len(amendments)} amendments ({len(incoming_amendments)} incoming, {len(outgoing_amendments)} outgoing)")

            return {
                "document_uri": document_uri,
                "amendments": amendments,
                "incoming_amendments": incoming_amendments,
                "outgoing_amendments": outgoing_amendments,
                "activity_score": activity_score,
                "total_amendments": len(amendments),
                "is_actively_modified": len(incoming_amendments) > 5,
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Amendment chain analysis failed: {e}")
            return {
                "error": f"Amendment chain analysis failed: {e}", 
                "success": False,
                "document_uri": document_uri,
                "amendments": [],
                "incoming_amendments": [],
                "outgoing_amendments": [],
                "activity_score": 0,
                "total_amendments": 0,
                "is_actively_modified": False
            }

    def verify_still_valid(self, document_uris: List[str]) -> Dict[str, Any]:
        """
        STEP 4A: Make sure the laws aren't canceled/repealed.
        Returns data matching VerifyStillValidResponse model.
        """
        logger.info(f"⚖️ VERIFYING LEGAL STATUS of {len(document_uris)} laws")

        try:
            law_statuses = []

            for uri in document_uris:
                query = f"""
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT ?related ?title ?date ?relType ?entryDate ?expiryDate WHERE {{
                  OPTIONAL {{ <{uri}> jolux:entryIntoForceDate ?entryDate }}
                  OPTIONAL {{ <{uri}> jolux:eventEndDate ?expiryDate }}
                  {{ 
                    <{uri}> jolux:repeals ?related .
                    BIND("repeals" AS ?relType)
                  }}
                  UNION
                  {{ 
                    ?related jolux:repeals <{uri}> .
                    BIND("repealedBy" AS ?relType)
                  }}
                  UNION
                  {{ 
                    <{uri}> jolux:consolidates ?related .
                    BIND("consolidates" AS ?relType)
                  }}
                  ?related jolux:isRealizedBy/jolux:title ?title .
                  ?related jolux:dateDocument ?date .
                }}
                ORDER BY DESC(?date)
                """

                self.sparql.setQuery(query)
                results = self.sparql.query().convert()

                events = []
                entry_date = None
                expiry_date = None

                for b in results.get("results", {}).get("bindings", []):
                    if not entry_date and b.get("entryDate"):
                        entry_date = b["entryDate"]["value"]
                    if not expiry_date and b.get("expiryDate"):
                        expiry_date = b["expiryDate"]["value"]

                    if b.get("relType"):
                        events.append({
                            "uri": b["related"]["value"],
                            "title": b["title"]["value"],
                            "date": b["date"]["value"],
                            "type": b["relType"]["value"]
                        })

                # Determine status
                status = "active"
                if any(e["type"] == "repealedBy" for e in events):
                    status = "repealed"
                elif any(e["type"] == "consolidates" for e in events):
                    status = "consolidated"
                elif expiry_date:
                    status = "expired"

                law_statuses.append({
                    "uri": uri,
                    "legal_status": status,
                    "entry_date": entry_date,
                    "expiry_date": expiry_date,
                    "events": events,
                    "is_valid": status in ["active", "consolidated"]
                })

            # Summary statistics
            valid_laws = [law for law in law_statuses if law["is_valid"]]
            invalid_laws = [law for law in law_statuses if not law["is_valid"]]

            logger.info(f"✅ Status verification complete: {len(valid_laws)} valid, {len(invalid_laws)} invalid")

            return {
                "law_statuses": law_statuses,
                "valid_laws": valid_laws,
                "invalid_laws": invalid_laws,
                "statistics": {
                    "total_checked": len(law_statuses),
                    "valid_count": len(valid_laws),
                    "invalid_count": len(invalid_laws),
                    "validity_rate": len(valid_laws) / len(law_statuses) if law_statuses else 0
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Legal status verification failed: {e}")
            return {
                "error": f"Legal status verification failed: {e}", 
                "success": False,
                "law_statuses": [],
                "valid_laws": [],
                "invalid_laws": [],
                "statistics": {
                    "total_checked": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "validity_rate": 0
                }
            }

    def rank_by_importance(self, laws_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 4B: Put all discovered laws in order of importance using multiple factors.
        Returns data matching RankByImportanceResponse model.
        """
        logger.info("🏆 RANKING LAWS BY IMPORTANCE")

        try:
            # Extract laws from various data sources
            all_laws = {}

            # Process laws from comparison results
            if "ranked_laws" in laws_data:
                for law in laws_data["ranked_laws"]:
                    uri = law["uri"]
                    all_laws[uri] = law.copy()

            # Add status information
            if "law_statuses" in laws_data:
                for status in laws_data["law_statuses"]:
                    uri = status["uri"]
                    if uri in all_laws:
                        all_laws[uri].update({
                            "legal_status": status["legal_status"],
                            "is_valid": status["is_valid"],
                            "entry_date": status["entry_date"],
                            "events": status["events"]
                        })

            # Calculate final importance scores
            for uri, law in all_laws.items():
                final_score = 0

                # Base score from discovery methods
                base_score = law.get("total_score", 0)
                final_score += base_score

                # Legal validity bonus (critical factor)
                if law.get("is_valid", True):
                    final_score += 300  # Major bonus for valid laws
                else:
                    final_score -= 200  # Penalty for invalid laws

                # Multi-method discovery bonus
                method_count = law.get("method_count", 1)
                if method_count >= 3:
                    final_score += 150  # Found by 3+ methods
                elif method_count >= 2:
                    final_score += 100  # Found by 2 methods

                # Legal status specific adjustments
                status = law.get("legal_status", "active")
                if status == "repealed":
                    final_score -= 500  # Heavy penalty for repealed laws
                elif status == "consolidated":
                    final_score += 50   # Slight bonus for consolidated laws
                elif status == "active":
                    final_score += 100  # Bonus for clearly active laws

                law["final_importance_score"] = final_score

                # Determine importance tier
                if final_score >= 800:
                    law["importance_tier"] = "critical"
                elif final_score >= 600:
                    law["importance_tier"] = "very_high"
                elif final_score >= 400:
                    law["importance_tier"] = "high"
                elif final_score >= 200:
                    law["importance_tier"] = "medium"
                else:
                    law["importance_tier"] = "low"

            # Sort by final importance score
            ranked_laws = sorted(all_laws.values(),
                                 key=lambda x: x["final_importance_score"],
                                 reverse=True)

            # Create tier groups
            tiers = {
                "critical": [law for law in ranked_laws if law["importance_tier"] == "critical"],
                "very_high": [law for law in ranked_laws if law["importance_tier"] == "very_high"],
                "high": [law for law in ranked_laws if law["importance_tier"] == "high"],
                "medium": [law for law in ranked_laws if law["importance_tier"] == "medium"],
                "low": [law for law in ranked_laws if law["importance_tier"] == "low"]
            }

            # Calculate statistics
            total_laws = len(ranked_laws)
            valid_laws = len([law for law in ranked_laws if law.get("is_valid", True)])
            average_score = sum(law["final_importance_score"] for law in ranked_laws) / max(total_laws, 1)

            logger.info(f"✅ Final ranking complete: {total_laws} laws ranked, avg score: {average_score:.1f}")

            return {
                "ranked_laws": ranked_laws,
                "tiers": tiers,
                "top_10_laws": ranked_laws[:10],
                "critical_laws": tiers["critical"],
                "statistics": {
                    "total_laws": total_laws,
                    "valid_laws": valid_laws,
                    "average_score": round(average_score, 1),
                    "tier_distribution": {
                        "critical": len(tiers["critical"]),
                        "very_high": len(tiers["very_high"]),
                        "high": len(tiers["high"]),
                        "medium": len(tiers["medium"]),
                        "low": len(tiers["low"])
                    },
                    "score_range": {
                        "highest": ranked_laws[0]["final_importance_score"] if ranked_laws else 0,
                        "lowest": ranked_laws[-1]["final_importance_score"] if ranked_laws else 0
                    }
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Final ranking failed: {e}")
            return {
                "error": f"Final ranking failed: {e}", 
                "success": False,
                "ranked_laws": [],
                "tiers": {"critical": [], "very_high": [], "high": [], "medium": [], "low": []},
                "top_10_laws": [],
                "critical_laws": [],
                "statistics": {
                    "total_laws": 0,
                    "valid_laws": 0,
                    "average_score": 0,
                    "tier_distribution": {"critical": 0, "very_high": 0, "high": 0, "medium": 0, "low": 0},
                    "score_range": {"highest": 0, "lowest": 0}
                }
            }

    def create_final_map(self, ranked_laws: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        STEP 4C: Create complete map showing all laws and how they connect.
        Returns data matching CreateFinalMapResponse model.
        """
        logger.info(f"🗺️ CREATING FINAL LEGAL MAP: {len(ranked_laws)} laws, {len(connections)} connections")

        try:
            # Create law index for quick lookup
            law_index = {law["uri"]: law for law in ranked_laws}

            # Build relationship graph
            relationship_graph = {}
            for law in ranked_laws:
                uri = law["uri"]
                relationship_graph[uri] = {
                    "law": law,
                    "cites": [],           # Laws this law cites
                    "cited_by": [],        # Laws that cite this law
                    "authority_level": law.get("legal_status", "unknown"),
                    "importance_tier": law.get("importance_tier", "unknown"),
                    "connection_score": 0
                }

            # Add connections to graph
            for connection in connections:
                from_uri = connection["from_uri"]
                to_uri = connection["to_uri"]

                if from_uri in relationship_graph and to_uri in relationship_graph:
                    relationship_graph[from_uri]["cites"].append(to_uri)
                    relationship_graph[to_uri]["cited_by"].append(from_uri)

            # Calculate connection scores
            for uri, node in relationship_graph.items():
                # Connection score based on number of relationships
                cites_count = len(node["cites"])
                cited_by_count = len(node["cited_by"])
                node["connection_score"] = (cites_count * 2) + (cited_by_count * 5)  # Being cited is more important

                # Determine centrality role
                if cited_by_count > 10:
                    node["centrality_role"] = "foundational"  # Many laws depend on this
                elif cited_by_count > 5:
                    node["centrality_role"] = "important"    # Several laws depend on this
                elif cites_count > 10:
                    node["centrality_role"] = "integrative"  # This law integrates many others
                elif cites_count > 5:
                    node["centrality_role"] = "referential"  # This law references several others
                else:
                    node["centrality_role"] = "standalone"   # Limited connections

            # Create hierarchical structure by authority and importance
            hierarchy = {
                "codes": [],           # CODE documents (highest authority)
                "foundational_laws": [],  # High-citation LOI documents
                "active_laws": [],      # Recently active/modified laws
                "supporting_laws": [],  # Lower importance but valid laws
                "historical_laws": []   # Old but still relevant laws
            }

            for law in ranked_laws:
                if not law.get("is_valid", True):
                    continue  # Skip invalid laws

                importance = law.get("importance_tier", "low")
                
                # Simple classification based on importance tier
                if importance == "critical":
                    hierarchy["codes"].append(law)
                elif importance in ["very_high", "high"]:
                    hierarchy["foundational_laws"].append(law)
                elif importance == "medium":
                    hierarchy["active_laws"].append(law)
                else:
                    hierarchy["supporting_laws"].append(law)

            # Create network statistics
            most_connected_raw = sorted(
                relationship_graph.values(),
                key=lambda x: x["connection_score"],
                reverse=True
            )[:5]

            # Convert to serializable format
            most_connected_laws = []
            for node in most_connected_raw:
                most_connected_laws.append({
                    "uri": node["law"]["uri"],
                    "title": node["law"]["title"],
                    "connection_score": node["connection_score"],
                    "centrality_role": node.get("centrality_role", "unknown")
                })

            network_stats = {
                "total_nodes": len(relationship_graph),
                "total_connections": len(connections),
                "most_connected_laws": most_connected_laws,
                "centrality_distribution": {},
                "authority_distribution": {},
                "hierarchy_sizes": {level: len(laws) for level, laws in hierarchy.items()}
            }

            # Calculate distributions
            for node in relationship_graph.values():
                role = node.get("centrality_role", "unknown")
                network_stats["centrality_distribution"][role] = network_stats["centrality_distribution"].get(role, 0) + 1

                authority = node["authority_level"]
                network_stats["authority_distribution"][authority] = network_stats["authority_distribution"].get(authority, 0) + 1

            # Create summary insights
            insights = []

            if hierarchy["codes"]:
                insights.append(f"Found {len(hierarchy['codes'])} critical laws that form the legal backbone")

            if hierarchy["foundational_laws"]:
                insights.append(f"Identified {len(hierarchy['foundational_laws'])} foundational laws with high importance")

            if most_connected_laws:
                most_connected = most_connected_laws[0]
                insights.append(f"Most connected law: {most_connected['title'][:50]}... with {most_connected['connection_score']} connection points")

            critical_laws = len(hierarchy["codes"])
            if critical_laws:
                insights.append(f"Discovered {critical_laws} critical laws that require immediate attention")

            logger.info(f"✅ Legal map created successfully with {len(hierarchy['codes']) + len(hierarchy['foundational_laws'])} core laws")

            return {
                "legal_map": {
                    "hierarchy": hierarchy,
                    "relationship_graph": {uri: {
                        "cites": node["cites"],
                        "cited_by": node["cited_by"],
                        "connection_score": node["connection_score"],
                        "centrality_role": node.get("centrality_role", "unknown")
                    } for uri, node in relationship_graph.items()},
                    "network_statistics": network_stats,
                    "insights": insights
                },
                "summary": {
                    "total_laws_mapped": len(ranked_laws),
                    "total_relationships": len(connections),
                    "core_legal_framework": len(hierarchy["codes"]) + len(hierarchy["foundational_laws"]),
                    "active_legal_framework": len(hierarchy["active_laws"]),
                    "complete_coverage": len(hierarchy["codes"]) + len(hierarchy["foundational_laws"]) + len(hierarchy["active_laws"])
                },
                "recommendations": {
                    "priority_review": hierarchy["codes"] + hierarchy["foundational_laws"][:5],
                    "active_monitoring": hierarchy["active_laws"][:10],
                    "reference_framework": hierarchy["supporting_laws"][:15]
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Legal map creation failed: {e}")
            return {
                "error": f"Legal map creation failed: {e}", 
                "success": False,
                "legal_map": {
                    "hierarchy": {"codes": [], "foundational_laws": [], "active_laws": [], "supporting_laws": [], "historical_laws": []},
                    "relationship_graph": {},
                    "network_statistics": {"total_nodes": 0, "total_connections": 0, "most_connected_laws": [], "centrality_distribution": {}, "authority_distribution": {}, "hierarchy_sizes": {}},
                    "insights": []
                },
                "summary": {"total_laws_mapped": 0, "total_relationships": 0, "core_legal_framework": 0, "active_legal_framework": 0, "complete_coverage": 0},
                "recommendations": {"priority_review": [], "active_monitoring": [], "reference_framework": []}
            }

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
        
    def basic_document_search(self, keywords: List[str], limit: int = 50) -> Dict[str, Any]:
        """
        BONUS TOOL: Simple keyword search for when you just need to find specific documents.
        Returns data matching BasicDocumentSearchResponse model.
        """
        logger.info(f"🔍 BASIC DOCUMENT SEARCH: {keywords}")

        try:
            # Build keyword filter
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(f'regex(str(?title), "{keyword}", "i")')
            filter_clause = " && ".join(keyword_filters) if keyword_filters else "true"

            query = f"""
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?entity ?title ?date ?type ?subject ?authority WHERE {{
                ?entity jolux:isRealizedBy ?expression .
                ?expression jolux:title ?title .
                ?entity jolux:dateDocument ?date .
                OPTIONAL {{ ?entity jolux:typeDocument ?type }}
                OPTIONAL {{ ?entity jolux:subjectLevel1 ?subject }}
                OPTIONAL {{ ?entity jolux:responsibilityOf ?authority }}
                FILTER({filter_clause})
            }}
            ORDER BY DESC(?date)
            LIMIT {limit}
            """

            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            documents = []
            for b in results.get("results", {}).get("bindings", []):
                # Map entity -> uri for model compatibility
                documents.append({
                    "uri": b["entity"]["value"],
                    "title": b["title"]["value"],
                    "date": b["date"]["value"],
                    "type": b.get("type", {}).get("value", ""),
                    "subject": b.get("subject", {}).get("value", ""),
                    "authority": b.get("authority", {}).get("value", "")
                })

            logger.info(f"✅ Found {len(documents)} documents matching keywords")

            return {
                "documents": documents,
                "total_found": len(documents),
                "keywords": keywords,
                "search_type": "basic_keyword_search",
                "success": True
            }

        except Exception as e:
            logger.error(f"❌ Basic document search failed: {e}")
            return {
                "error": f"Basic document search failed: {e}", 
                "success": False,
                "documents": [],
                "total_found": 0,
                "keywords": keywords,
                "search_type": "basic_keyword_search"
            }