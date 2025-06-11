"""
Configuration settings for Luxembourg Legal Intelligence MCP Server
"""

import logging
import sys
from SPARQLWrapper import SPARQLWrapper, JSON, POST


class Config:
    """Configuration class for the Luxembourg Legal Intelligence server."""
    
    # SPARQL Configuration
    SPARQL_ENDPOINT = "https://data.legilux.public.lu/sparqlendpoint"
    SPARQL_TIMEOUT = 30
    
    # Content Extraction Configuration
    PDF_TIMEOUT = 60
    MAX_DOCUMENTS_PER_EXTRACTION = 3
    PREFER_HTML_EXTRACTION = True
    
    # Search Configuration
    DEFAULT_SEARCH_LIMIT = 50
    MAX_SEARCH_LIMIT = 100
    
    # Logging Configuration
    LOG_LEVEL = logging.DEBUG
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def initialize_sparql(endpoint: str = None) -> SPARQLWrapper:
    """Initialize SPARQL connection."""
    endpoint = endpoint or Config.SPARQL_ENDPOINT
    sparql = SPARQLWrapper(endpoint)
    # Set User-Agent header to identify requests and suppress SPARQLWrapper warnings
    import os
    user_agent = os.getenv("USER_AGENT", "mcp-legilux-server/1.0")
    sparql.addCustomHttpHeader("User-Agent", user_agent)
    # Use POST to preserve special characters (e.g., '+' in arithmetic) in the SPARQL query
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    return sparql