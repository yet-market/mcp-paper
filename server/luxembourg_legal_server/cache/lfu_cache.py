"""
LFU cache implementation for SPARQL query results.

This module provides a Least Frequently Used (LFU) cache implementation
for SPARQL query results.
"""

import time
import heapq
from typing import Any, Dict, List, Optional, Tuple

from luxembourg_legal_server.cache.query_cache import QueryCache


class LFUCache(QueryCache):
    """Least Frequently Used (LFU) cache for SPARQL query results.
    
    This cache implements the LFU replacement policy, which evicts
    the least frequently used items first when the cache is full.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        """Initialize the LFU cache.
        
        Args:
            ttl: Time-to-live for cache entries in seconds.
            max_size: Maximum number of entries in the cache.
        """
        super().__init__(ttl, max_size)
        # Main cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        # Store access frequencies
        self._frequencies: Dict[str, int] = {}
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
            self._remove_item(key)
            return None
        
        # Increment the access frequency
        self._frequencies[key] = self._frequencies.get(key, 0) + 1
        
        return self._cache[key]
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a value in the cache.
        
        Args:
            key: The cache key.
            value: The value to store in the cache.
        """
        # If the key already exists, update it
        if key in self._cache:
            self._cache[key] = value
            self._timestamps[key] = time.time()
            # Don't reset frequency - existing items keep their frequency
            return
        
        # If the cache is full, remove the least frequently used item
        if len(self._cache) >= self.max_size:
            self._evict_lfu_item()
        
        # Add the new value with initial frequency 1
        self._cache[key] = value
        self._frequencies[key] = 1
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
            self._remove_item(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._frequencies.clear()
        self._timestamps.clear()
    
    def get_size(self) -> int:
        """Get the current size of the cache.
        
        Returns:
            The number of entries in the cache.
        """
        return len(self._cache)
    
    def _remove_item(self, key: str) -> None:
        """Remove an item from the cache and all tracking structures.
        
        Args:
            key: The key of the item to remove.
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._frequencies:
            del self._frequencies[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def _evict_lfu_item(self) -> None:
        """Evict the least frequently used item from the cache."""
        if not self._cache:
            return
        
        # Find the key with the lowest frequency
        min_freq = min(self._frequencies.values())
        lfu_keys = [k for k, v in self._frequencies.items() if v == min_freq]
        
        # If multiple items have the same frequency, remove the oldest one
        oldest_key = None
        oldest_time = float('inf')
        
        for key in lfu_keys:
            timestamp = self._timestamps.get(key, float('inf'))
            if timestamp < oldest_time:
                oldest_time = timestamp
                oldest_key = key
        
        if oldest_key:
            self._remove_item(oldest_key)