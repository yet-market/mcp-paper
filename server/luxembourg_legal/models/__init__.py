"""
Luxembourg Legal Models Package
"""

from .base import BaseSPARQLResponse
from .tool_models import *

__all__ = [
    'BaseSPARQLResponse',
    # Discovery models
    'FindMostCitedLawsResponse',
    'FindMostChangedLawsResponse', 
    'FindNewestActiveLawsResponse',
    'FindHighestAuthorityLawsResponse',
    # Analysis models
    'CompareResultsResponse',
    'CheckConnectionsResponse',
    # Relationship models
    'FindWhatLawReferencesResponse',
    'FindWhatReferencesLawResponse',
    'FindAmendmentChainResponse',
    # Final models
    'VerifyStillValidResponse',
    'RankByImportanceResponse',
    'CreateFinalMapResponse',
    # Bonus models
    'BasicDocumentSearchResponse',
]