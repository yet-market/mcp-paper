"""
Tabular formatter for SPARQL query results.

This module provides a formatter that converts SPARQL query results into
a tabular structure with columns and rows.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from luxembourg_legal_server.formatters.formatter import ResultFormatter


class TabularFormatter(ResultFormatter):
    """Formatter for tabular SPARQL results.
    
    This formatter converts SPARQL query results into a structure with
    columns and rows, similar to a database result set.
    """
    
    def format_results(self, results: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """Format the query results in a tabular structure.
        
        Args:
            results: The raw query results to format.
            query: The SPARQL query that produced the results (optional).
            
        Returns:
            A dictionary with a tabular representation of the results.
        """
        formatted_result: Dict[str, Any] = {}
        
        # Handle different types of SPARQL query results
        if "boolean" in results:
            # ASK query - not really tabular, but we'll handle it anyway
            formatted_result["type"] = "ASK"
            formatted_result["value"] = results["boolean"]
            
        elif "results" in results and "bindings" in results["results"]:
            # SELECT query - convert to columns and rows
            variables = results.get("head", {}).get("vars", [])
            bindings = results["results"]["bindings"]
            
            columns, rows = self._create_tabular_structure(variables, bindings)
            
            formatted_result["type"] = "SELECT"
            formatted_result["columns"] = columns
            formatted_result["rows"] = rows
            
        elif "head" in results and not results.get("results"):
            # Empty results
            formatted_result["type"] = "SELECT"
            formatted_result["columns"] = results.get("head", {}).get("vars", [])
            formatted_result["rows"] = []
            
        else:
            # Assume CONSTRUCT/DESCRIBE query with graph results
            # These don't convert well to tabular format, so we'll just pass them through
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
    
    def _create_tabular_structure(
        self, variables: List[str], bindings: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, str]], List[List[Any]]]:
        """Create a tabular structure from SPARQL results.
        
        Args:
            variables: The variables from the SPARQL query.
            bindings: The bindings from the SPARQL results.
            
        Returns:
            A tuple containing (columns, rows) where:
            - columns is a list of column definitions
            - rows is a list of row values
        """
        # Create column definitions
        columns = [{"name": var, "label": var} for var in variables]
        
        # Create rows
        rows = []
        for binding in bindings:
            row = []
            for var in variables:
                if var in binding:
                    row.append(binding[var].get("value"))
                else:
                    row.append(None)
            rows.append(row)
            
        return columns, rows