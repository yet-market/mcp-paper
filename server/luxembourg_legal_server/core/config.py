"""
Configuration module for the SPARQL server.

This module defines the configuration options and defaults for the SPARQL server.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, validator


class ResultFormat(str, Enum):
    """Supported result formats for SPARQL queries."""
    
    JSON = "json"
    SIMPLIFIED = "simplified"
    TABULAR = "tabular"


class CacheStrategy(str, Enum):
    """Supported cache replacement strategies."""
    
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out


class SPARQLConfig(BaseModel):
    """Configuration for the SPARQL server.
    
    This class defines all configurable aspects of the SPARQL server,
    including endpoint URL, request parameters, caching, and result formatting.
    """
    
    # SPARQL endpoint configuration
    endpoint_url: HttpUrl
    request_timeout: int = Field(default=30, ge=1, le=3600)
    max_results: int = Field(default=1000, ge=1, le=100000)
    
    # Cache configuration
    cache_enabled: bool = True
    cache_ttl: int = Field(default=300, ge=1, le=86400)  # seconds
    cache_max_size: int = Field(default=100, ge=1, le=10000)
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    
    # Result formatting configuration
    default_format: ResultFormat = ResultFormat.JSON
    pretty_print: bool = False
    include_metadata: bool = True
    
    # HTTP server configuration (when using http transport)
    http_host: str = "localhost"
    http_port: int = Field(default=8000, ge=1, le=65535)
    transport: str = Field(default="stdio", pattern="^(stdio|streamable-http|sse)$")
    
    @classmethod
    def from_env(cls) -> "SPARQLConfig":
        """Create a configuration instance from environment variables.
        
        Returns:
            SPARQLConfig: Configuration initialized from environment variables.
            
        Raises:
            ValueError: If required variables are missing or invalid.
        """
        # Get required endpoint URL from environment
        endpoint_url = os.environ.get("SPARQL_ENDPOINT")
        if not endpoint_url:
            raise ValueError("SPARQL_ENDPOINT environment variable is required")
            
        # Process optional configuration from environment
        return cls(
            endpoint_url=endpoint_url,
            request_timeout=int(os.environ.get("SPARQL_TIMEOUT", "30")),
            max_results=int(os.environ.get("SPARQL_MAX_RESULTS", "1000")),
            cache_enabled=os.environ.get("SPARQL_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.environ.get("SPARQL_CACHE_TTL", "300")),
            cache_max_size=int(os.environ.get("SPARQL_CACHE_MAX_SIZE", "100")),
            cache_strategy=CacheStrategy(
                os.environ.get("SPARQL_CACHE_STRATEGY", CacheStrategy.LRU.value)
            ),
            default_format=ResultFormat(
                os.environ.get("SPARQL_FORMAT", ResultFormat.JSON.value)
            ),
            pretty_print=os.environ.get("SPARQL_PRETTY_PRINT", "false").lower() == "true",
            include_metadata=os.environ.get("SPARQL_INCLUDE_METADATA", "true").lower() == "true",
            http_host=os.environ.get("MCP_HOST", "localhost"),
            http_port=int(os.environ.get("MCP_PORT", "8000")),
            transport=os.environ.get("MCP_TRANSPORT", "stdio"),
        )
    
    @validator("endpoint_url")
    def validate_endpoint_url(cls, v):
        """Ensure the endpoint URL is valid and using HTTP/HTTPS protocol."""
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("Endpoint URL must use HTTP or HTTPS protocol")
        return v