"""
Simplified JSON formatter for SPARQL query results.

This module provides a formatter that converts SPARQL query results into
a simplified JSON structure that is easier to work with.
"""

import json
from typing import Any, Dict, List, Optional

from luxembourg_legal_server.formatters.formatter import ResultFormatter


class SimplifiedFormatter(ResultFormatter):
    """Formatter for simplified JSON SPARQL results.
    
    This formatter converts the standard SPARQL JSON results into a simpler
    structure that is often easier to work with in client applications.
    """
    
    def format_results(self, results: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """Format the query results as simplified JSON.
        
        For SELECT queries, converts the results to an array of objects where each
        object contains key-value pairs for the bindings.
        
        For ASK queries, returns a simple boolean result.
        
        For CONSTRUCT/DESCRIBE queries, returns a simplified triples structure.
        
        Args:
            results: The raw query results to format.
            query: The SPARQL query that produced the results (optional).
            
        Returns:
            The query results in a simplified JSON structure.
        """
        formatted_result: Dict[str, Any] = {}
        
        # Handle different types of SPARQL query results
        if "boolean" in results:
            # ASK query
            formatted_result["result"] = results["boolean"]
            formatted_result["type"] = "ASK"
            
        elif "results" in results and "bindings" in results["results"]:
            # SELECT query
            formatted_result["type"] = "SELECT"
            formatted_result["results"] = self._simplify_bindings(
                results["results"]["bindings"],
                results.get("head", {}).get("vars", [])
            )
            
        elif "head" in results and not results.get("results"):
            # Empty results
            formatted_result["type"] = "SELECT"
            formatted_result["results"] = []
            
        else:
            # Assume CONSTRUCT/DESCRIBE query with graph results
            formatted_result["type"] = "GRAPH"
            formatted_result["results"] = results
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = self._extract_metadata(results)
            if query:
                metadata["query"] = query
            formatted_result["metadata"] = metadata
        
        # Pretty-print if requested
        if self.pretty_print:
            return json.loads(json.dumps(formatted_result, indent=2))
            
        return formatted_result
    
    def _simplify_bindings(self, bindings: List[Dict[str, Any]], variables: List[str]) -> List[Dict[str, Any]]:
        """Simplify the bindings structure from SPARQL results.
        
        Converts from:
        [{"var1": {"type": "uri", "value": "http://example.org"}, ...}]
        
        To:
        [{"var1": "http://example.org", ...}]
        
        Args:
            bindings: The bindings from the SPARQL results.
            variables: The variables from the SPARQL results head.
            
        Returns:
            A list of simplified binding objects.
        """
        simplified_bindings = []
        
        for binding in bindings:
            simplified_binding = {}
            
            for var in variables:
                if var in binding:
                    # Extract just the value from the binding
                    simplified_binding[var] = binding[var]["value"]
                    
                    # Optionally include datatype or language
                    if "datatype" in binding[var]:
                        simplified_binding[f"{var}_datatype"] = binding[var]["datatype"]
                    if "xml:lang" in binding[var]:
                        simplified_binding[f"{var}_lang"] = binding[var]["xml:lang"]
                else:
                    # Variable not bound in this result
                    simplified_binding[var] = None
                    
            simplified_bindings.append(simplified_binding)
            
        return simplified_bindings