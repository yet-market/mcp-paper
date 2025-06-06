"""
JSON formatter for SPARQL query results.

This module provides a formatter for SPARQL query results that preserves
the standard JSON structure returned by SPARQL endpoints.
"""

import json
from typing import Any, Dict, Optional

from luxembourg_legal_server.formatters.formatter import ResultFormatter


class JSONFormatter(ResultFormatter):
    """Formatter for standard JSON SPARQL results.
    
    This formatter preserves the standard JSON structure returned by SPARQL endpoints,
    with optional pretty-printing and metadata inclusion.
    """
    
    def format_results(self, results: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """Format the query results as standard JSON.
        
        Args:
            results: The raw query results to format.
            query: The SPARQL query that produced the results (optional).
            
        Returns:
            The formatted query results in standard JSON structure.
        """
        formatted_results = results.copy()
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = self._extract_metadata(results)
            if query:
                metadata["query"] = query
            formatted_results["metadata"] = metadata
        
        # If pretty print is requested, convert to string and back for formatting
        # This is mainly for logging or debugging purposes
        if self.pretty_print:
            return json.loads(json.dumps(formatted_results, indent=2))
        
        return formatted_results