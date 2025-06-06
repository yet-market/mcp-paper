"""
Base cache interface for SPARQL query results.

This module defines the base cache interface and common functionality
for all cache implementations.
"""

import time
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class QueryCache(ABC):
    """Base class for SPARQL query result caches.
    
    This abstract class defines the interface for all query caches.
    Caches store query results to avoid redundant execution of the same queries.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        """Initialize the cache with the specified parameters.
        
        Args:
            ttl: Time-to-live for cache entries in seconds.
            max_size: Maximum number of entries in the cache.
        """
        self.ttl = ttl
        self.max_size = max_size
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value, or None if the key is not in the cache
            or the cache entry has expired.
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a value in the cache.
        
        Args:
            key: The cache key.
            value: The value to store in the cache.
        """
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.
        
        Args:
            key: The cache key to invalidate.
            
        Returns:
            True if the key was in the cache and was invalidated,
            False otherwise.
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the entire cache."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get the current size of the cache.
        
        Returns:
            The number of entries in the cache.
        """
        pass
    
    def get_query_key(self, query: str, endpoint: str, format_name: str) -> str:
        """Generate a cache key for a SPARQL query.
        
        The key is a hash of the query string, endpoint URL, and format name.
        This ensures that the same query executed against different endpoints
        or with different formatting options will have different cache keys.
        
        Args:
            query: The SPARQL query string.
            endpoint: The SPARQL endpoint URL.
            format_name: The name of the result format.
            
        Returns:
            A string hash that can be used as a cache key.
        """
        # Create a string with all the components that affect the result
        key_string = f"{query}|{endpoint}|{format_name}"
        
        # Create a hash of the string
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return key_hash