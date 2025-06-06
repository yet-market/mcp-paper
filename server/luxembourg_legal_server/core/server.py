"""
SPARQL server implementation.

This module provides the main SPARQL server class that handles
querying SPARQL endpoints with support for caching and result formatting.
"""

import logging
from typing import Any, Dict, Optional, Type, Union

from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions

from luxembourg_legal_server.core.config import SPARQLConfig, ResultFormat, CacheStrategy
from luxembourg_legal_server.formatters import (
    ResultFormatter, 
    JSONFormatter,
    SimplifiedFormatter,
    TabularFormatter
)
from luxembourg_legal_server.cache import QueryCache, LRUCache, LFUCache, FIFOCache


# Set up logging
logger = logging.getLogger(__name__)


class SPARQLServer:
    """SPARQL server with support for caching and result formatting.
    
    This class connects to a SPARQL endpoint and provides methods for
    executing queries with optional caching and result formatting.
    """
    
    def __init__(self, config: SPARQLConfig):
        """Initialize the SPARQL server with the given configuration.
        
        Args:
            config: Configuration for the SPARQL server.
        """
        self.config = config
        
        # Initialize the SPARQL wrapper
        self.sparql = SPARQLWrapper(str(config.endpoint_url))
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(config.request_timeout)
        
        # Set up formatters
        self.formatters = {
            ResultFormat.JSON: JSONFormatter(
                include_metadata=config.include_metadata,
                pretty_print=config.pretty_print
            ),
            ResultFormat.SIMPLIFIED: SimplifiedFormatter(
                include_metadata=config.include_metadata,
                pretty_print=config.pretty_print
            ),
            ResultFormat.TABULAR: TabularFormatter(
                include_metadata=config.include_metadata,
                pretty_print=config.pretty_print
            )
        }
        
        # Set up caching
        self.cache_enabled = config.cache_enabled
        if self.cache_enabled:
            self.cache = self._create_cache(
                config.cache_strategy,
                config.cache_ttl,
                config.cache_max_size
            )
    
    def query(
        self, 
        query_string: str, 
        format_type: Optional[ResultFormat] = None
    ) -> Dict[str, Any]:
        """Execute a SPARQL query and return the results.
        
        Args:
            query_string: The SPARQL query to execute.
            format_type: The format to return the results in (default: from config).
            
        Returns:
            The query results in the specified format.
            
        Raises:
            ValueError: If the query string is empty.
            SPARQLExceptions.EndPointNotFound: If the endpoint URL is invalid.
        """
        if not query_string or not query_string.strip():
            raise ValueError("Query string cannot be empty")
        
        # Determine the format to use
        format_type = format_type or self.config.default_format
        formatter = self.formatters[format_type]
        
        # Check the cache if enabled
        if self.cache_enabled:
            cache_key = self.cache.get_query_key(
                query_string, 
                str(self.config.endpoint_url), 
                format_type.value
            )
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for query: %s", query_string[:50])
                return cached_result
            
            logger.debug("Cache miss for query: %s", query_string[:50])
        
        # Execute the query
        try:
            self.sparql.setQuery(query_string)
            results = self.sparql.query().convert()
            
            # Format the results
            formatted_results = formatter.format_results(results, query_string)
            
            # Cache the results if enabled
            if self.cache_enabled:
                self.cache.set(cache_key, formatted_results)
            
            return formatted_results
            
        except SPARQLExceptions.EndPointNotFound:
            error_msg = f"SPARQL endpoint not found: {self.config.endpoint_url}"
            logger.error(error_msg)
            return {"error": error_msg, "query": query_string}
            
        except SPARQLExceptions.QueryBadFormed:
            error_msg = "Malformed SPARQL query"
            logger.error("%s: %s", error_msg, query_string)
            return {"error": error_msg, "query": query_string}
            
        except Exception as e:
            error_msg = f"Query error: {str(e)}"
            logger.error("%s: %s", error_msg, query_string)
            return {"error": error_msg, "query": query_string}
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache.
        
        Returns:
            A dictionary with cache statistics.
        """
        if self.cache_enabled:
            return {
                "enabled": True,
                "size": self.cache.get_size(),
                "max_size": self.cache.max_size,
                "ttl": self.cache.ttl,
                "strategy": self.config.cache_strategy.value
            }
        else:
            return {"enabled": False}
    
    def _create_cache(
        self, strategy: CacheStrategy, ttl: int, max_size: int
    ) -> QueryCache:
        """Create a cache instance based on the specified strategy.
        
        Args:
            strategy: The cache replacement strategy to use.
            ttl: Time-to-live for cache entries in seconds.
            max_size: Maximum number of entries in the cache.
            
        Returns:
            A QueryCache instance.
            
        Raises:
            ValueError: If the strategy is not supported.
        """
        if strategy == CacheStrategy.LRU:
            return LRUCache(ttl=ttl, max_size=max_size)
        elif strategy == CacheStrategy.LFU:
            return LFUCache(ttl=ttl, max_size=max_size)
        elif strategy == CacheStrategy.FIFO:
            return FIFOCache(ttl=ttl, max_size=max_size)
        else:
            raise ValueError(f"Unsupported cache strategy: {strategy}")
    
    def update_config(self, new_config: SPARQLConfig) -> None:
        """Update the server configuration.
        
        Args:
            new_config: The new configuration to use.
        """
        # Save the old config
        old_config = self.config
        
        # Update the config
        self.config = new_config
        
        # If the endpoint URL changed, update the SPARQL wrapper
        if old_config.endpoint_url != new_config.endpoint_url:
            self.sparql = SPARQLWrapper(str(new_config.endpoint_url))
            self.sparql.setReturnFormat(JSON)
        
        # If the timeout changed, update the SPARQL wrapper
        if old_config.request_timeout != new_config.request_timeout:
            self.sparql.setTimeout(new_config.request_timeout)
        
        # If formatter settings changed, update the formatters
        if (old_config.include_metadata != new_config.include_metadata or
                old_config.pretty_print != new_config.pretty_print):
            self.formatters = {
                ResultFormat.JSON: JSONFormatter(
                    include_metadata=new_config.include_metadata,
                    pretty_print=new_config.pretty_print
                ),
                ResultFormat.SIMPLIFIED: SimplifiedFormatter(
                    include_metadata=new_config.include_metadata,
                    pretty_print=new_config.pretty_print
                ),
                ResultFormat.TABULAR: TabularFormatter(
                    include_metadata=new_config.include_metadata,
                    pretty_print=new_config.pretty_print
                )
            }
        
        # If cache settings changed, update the cache
        if (old_config.cache_enabled != new_config.cache_enabled or
                old_config.cache_strategy != new_config.cache_strategy or
                old_config.cache_ttl != new_config.cache_ttl or
                old_config.cache_max_size != new_config.cache_max_size):
            
            # Enable/disable caching
            self.cache_enabled = new_config.cache_enabled
            
            # If caching is enabled, create/recreate the cache
            if self.cache_enabled:
                self.cache = self._create_cache(
                    new_config.cache_strategy,
                    new_config.cache_ttl,
                    new_config.cache_max_size
                )