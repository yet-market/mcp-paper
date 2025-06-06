"""
LRU cache implementation for SPARQL query results.

This module provides a Least Recently Used (LRU) cache implementation
for SPARQL query results.
"""

import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from luxembourg_legal_server.cache.query_cache import QueryCache


class LRUCache(QueryCache):
    """Least Recently Used (LRU) cache for SPARQL query results.
    
    This cache implements the LRU replacement policy, which evicts
    the least recently used items first when the cache is full.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        """Initialize the LRU cache.
        
        Args:
            ttl: Time-to-live for cache entries in seconds.
            max_size: Maximum number of entries in the cache.
        """
        super().__init__(ttl, max_size)
        # Use OrderedDict to track insertion/access order
        self._cache: OrderedDict = OrderedDict()
        # Store timestamps for TTL checking
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value, or None if the key is not in the cache
            or the cache entry has expired.
        """
        if key not in self._cache:
            return None
        
        # Check if the entry has expired
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self.ttl:
            # Entry has expired, remove it
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        # Move the item to the end of the OrderedDict to mark it as recently used
        value = self._cache.pop(key)
        self._cache[key] = value
        
        return value
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a value in the cache.
        
        Args:
            key: The cache key.
            value: The value to store in the cache.
        """
        # If the cache is full, remove the least recently used item (first item)
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key, _ = self._cache.popitem(last=False)
            if oldest_key in self._timestamps:
                del self._timestamps[oldest_key]
        
        # Remove the key if it exists to update its position
        if key in self._cache:
            del self._cache[key]
        
        # Add the new value and update timestamp
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.
        
        Args:
            key: The cache key to invalidate.
            
        Returns:
            True if the key was in the cache and was invalidated,
            False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._timestamps.clear()
    
    def get_size(self) -> int:
        """Get the current size of the cache.
        
        Returns:
            The number of entries in the cache.
        """
        return len(self._cache)