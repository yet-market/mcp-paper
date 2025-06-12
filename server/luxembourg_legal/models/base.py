"""
Base models for Luxembourg Legal Intelligence responses
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class BaseSPARQLResponse(BaseModel):
    """Base response model for all SPARQL-based tools."""
    success: bool
    error: Optional[str] = None


class BaseSearchMetadata(BaseModel):
    """Common metadata for search operations."""
    keywords: List[str]
    method: str
    total_found: int


class BaseDocumentItem(BaseModel):
    """Base structure for document items from SPARQL queries."""
    uri: str
    title: str
    date: str