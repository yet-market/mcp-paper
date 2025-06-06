"""
Cache implementation for SPARQL query results.

This package provides caching functionality for SPARQL queries
to improve performance for repeated queries.
"""

from luxembourg_legal_server.cache.query_cache import QueryCache
from luxembourg_legal_server.cache.lru_cache import LRUCache
from luxembourg_legal_server.cache.lfu_cache import LFUCache
from luxembourg_legal_server.cache.fifo_cache import FIFOCache

__all__ = ["QueryCache", "LRUCache", "LFUCache", "FIFOCache"]