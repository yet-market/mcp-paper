"""
Base formatter class for SPARQL query results.

This module defines the base formatter interface and common functionality
for all result formatters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ResultFormatter(ABC):
    """Base class for SPARQL query result formatters.
    
    This abstract class defines the interface for all result formatters.
    Formatters convert raw SPARQL query results into specific formats.
    """
    
    def __init__(self, include_metadata: bool = True, pretty_print: bool = False):
        """Initialize the formatter with formatting options.
        
        Args:
            include_metadata: Whether to include query metadata in the output.
            pretty_print: Whether to pretty-print the output (if applicable).
        """
        self.include_metadata = include_metadata
        self.pretty_print = pretty_print
    
    @abstractmethod
    def format_results(self, results: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
        """Format the query results into the desired format.
        
        Args:
            results: The raw query results to format.
            query: The SPARQL query that produced the results (optional).
            
        Returns:
            The formatted query results.
        """
        pass
    
    def _extract_metadata(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from query results.
        
        Args:
            results: The raw query results.
            
        Returns:
            A dictionary containing metadata about the query results.
        """
        metadata = {}
        
        # Extract common metadata fields if they exist
        if "head" in results:
            metadata["variables"] = results["head"].get("vars", [])
            metadata["links"] = results["head"].get("links", [])
        
        # Include result count if available
        if "results" in results and "bindings" in results["results"]:
            metadata["count"] = len(results["results"]["bindings"])
        elif "boolean" in results:
            # For ASK queries
            metadata["type"] = "ASK"
        
        return metadata