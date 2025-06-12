"""
Tool-specific response models matching SPARQL query structures
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .base import BaseSPARQLResponse, BaseSearchMetadata, BaseDocumentItem


# =============================================================================
# DISCOVERY TOOLS MODELS (Phase 1)
# =============================================================================

class CitedLawItem(BaseDocumentItem):
    """SPARQL: SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count)"""
    cited_doc: str  # We'll map uri -> cited_doc for consistency
    citation_count: int


class FindMostCitedLawsResponse(BaseSPARQLResponse):
    laws: List[CitedLawItem]
    keywords: List[str]
    method: str
    total_found: int


class ModifiedLawItem(BaseDocumentItem):
    """SPARQL: SELECT ?modified_doc ?title ?date (COUNT(?modifier) as ?modification_count)"""
    modified_doc: str  # We'll map uri -> modified_doc for consistency
    modification_count: int


class FindMostChangedLawsResponse(BaseSPARQLResponse):
    laws: List[ModifiedLawItem]
    keywords: List[str]
    method: str
    total_found: int


class ActiveLawItem(BaseDocumentItem):
    """SPARQL: SELECT ?doc ?title ?date ?type_doc"""
    doc: str  # We'll map uri -> doc for consistency
    type_doc: Optional[str] = None


class FindNewestActiveLawsResponse(BaseSPARQLResponse):
    laws: List[ActiveLawItem]
    keywords: List[str]
    method: str
    total_found: int


class HighestAuthorityLawItem(BaseDocumentItem):
    """SPARQL: SELECT ?doc ?title ?date ?type_doc"""
    doc: str  # We'll map uri -> doc for consistency
    type_doc: str


class FindHighestAuthorityLawsResponse(BaseSPARQLResponse):
    laws: List[HighestAuthorityLawItem]
    keywords: List[str]
    method: str
    total_found: int


# =============================================================================
# ANALYSIS TOOLS MODELS (Phase 2)
# =============================================================================

class ComparedLawItem(BaseModel):
    """Laws with comparison analysis data"""
    uri: str
    title: str
    date: str
    discovery_methods: List[str]
    importance_scores: List[int]
    total_score: int
    method_count: int
    confidence: str


class ComparisonStatistics(BaseModel):
    total_laws: int
    multi_method_count: int
    high_confidence_count: int
    methods_used: List[str]
    method_count: int


class CompareResultsResponse(BaseSPARQLResponse):
    ranked_laws: List[ComparedLawItem]
    multi_method_laws: List[ComparedLawItem]
    high_confidence_laws: List[ComparedLawItem]
    statistics: ComparisonStatistics


class ConnectionItem(BaseModel):
    """Citation connections between laws"""
    from_uri: str
    to_uri: str
    to_title: str
    to_date: str
    to_type: str
    relationship: str
    direction: str


class ConnectionCount(BaseModel):
    uri: str
    outbound_count: int
    inbound_count: int
    total_connections: int


class ConnectionStatistics(BaseModel):
    total_connections: int
    laws_analyzed: int
    connected_laws: int


class CheckConnectionsResponse(BaseSPARQLResponse):
    connections: List[ConnectionItem]
    connection_matrix: Dict[str, Dict[str, List[str]]]
    most_connected_laws: List[ConnectionCount]
    statistics: ConnectionStatistics


# =============================================================================
# RELATIONSHIP TOOLS MODELS (Phase 3)
# =============================================================================

class ReferenceItem(BaseModel):
    """SPARQL: SELECT ?cited ?title ?date ?type"""
    uri: str  # We'll map cited -> uri
    title: str
    date: str
    type: str
    relationship: str


class FindWhatLawReferencesResponse(BaseSPARQLResponse):
    source_document: str
    references: List[ReferenceItem]
    total_found: int
    relationship_type: str


class CitingLawItem(BaseModel):
    """SPARQL: SELECT ?citing ?title ?date ?type"""
    uri: str  # We'll map citing -> uri
    title: str
    date: str
    type: str
    relationship: str


class FindWhatReferencesLawResponse(BaseSPARQLResponse):
    target_document: str
    citing_laws: List[CitingLawItem]
    total_found: int
    relationship_type: str


class AmendmentItem(BaseModel):
    """SPARQL: SELECT ?neighbor ?title ?date ?type ?direction"""
    uri: str  # We'll map neighbor -> uri
    title: str
    date: str
    type: str
    direction: str


class FindAmendmentChainResponse(BaseSPARQLResponse):
    document_uri: str
    amendments: List[AmendmentItem]
    incoming_amendments: List[AmendmentItem]
    outgoing_amendments: List[AmendmentItem]
    activity_score: int
    total_amendments: int
    is_actively_modified: bool


# =============================================================================
# FINAL TOOLS MODELS (Phase 4)
# =============================================================================

class LegalStatusEvent(BaseModel):
    uri: str
    title: str
    date: str
    type: str


class LegalStatusItem(BaseModel):
    """Legal status verification results"""
    uri: str
    legal_status: str
    entry_date: Optional[str] = None
    expiry_date: Optional[str] = None
    events: List[LegalStatusEvent]
    is_valid: bool


class LegalStatusStatistics(BaseModel):
    total_checked: int
    valid_count: int
    invalid_count: int
    validity_rate: float


class VerifyStillValidResponse(BaseSPARQLResponse):
    law_statuses: List[LegalStatusItem]
    valid_laws: List[LegalStatusItem]
    invalid_laws: List[LegalStatusItem]
    statistics: LegalStatusStatistics


class RankedLawItem(BaseModel):
    """Final ranked law with all importance metrics"""
    uri: str
    title: str
    date: str
    legal_status: Optional[str] = None
    is_valid: Optional[bool] = None
    entry_date: Optional[str] = None
    events: Optional[List[LegalStatusEvent]] = None
    final_importance_score: int
    importance_tier: str


class TierDistribution(BaseModel):
    critical: int
    very_high: int
    high: int
    medium: int
    low: int


class ScoreRange(BaseModel):
    highest: int
    lowest: int


class RankingStatistics(BaseModel):
    total_laws: int
    valid_laws: int
    average_score: float
    tier_distribution: TierDistribution
    score_range: ScoreRange


class RankByImportanceResponse(BaseSPARQLResponse):
    ranked_laws: List[RankedLawItem]
    tiers: Dict[str, List[RankedLawItem]]
    top_10_laws: List[RankedLawItem]
    critical_laws: List[RankedLawItem]
    statistics: RankingStatistics


class NetworkStatistics(BaseModel):
    total_nodes: int
    total_connections: int
    most_connected_laws: List[Dict[str, Any]]  # Keep flexible for now
    centrality_distribution: Dict[str, int]
    authority_distribution: Dict[str, int]
    hierarchy_sizes: Dict[str, int]


class LegalMapHierarchy(BaseModel):
    codes: List[RankedLawItem]
    foundational_laws: List[RankedLawItem]
    active_laws: List[RankedLawItem]
    supporting_laws: List[RankedLawItem]
    historical_laws: List[RankedLawItem]


class LegalMap(BaseModel):
    hierarchy: LegalMapHierarchy
    relationship_graph: Dict[str, Any]  # Keep flexible due to complexity
    network_statistics: NetworkStatistics
    insights: List[str]


class MapSummary(BaseModel):
    total_laws_mapped: int
    total_relationships: int
    core_legal_framework: int
    active_legal_framework: int
    complete_coverage: int


class MapRecommendations(BaseModel):
    priority_review: List[RankedLawItem]
    active_monitoring: List[RankedLawItem]
    reference_framework: List[RankedLawItem]


class CreateFinalMapResponse(BaseSPARQLResponse):
    legal_map: LegalMap
    summary: MapSummary
    recommendations: MapRecommendations


# =============================================================================
# BONUS TOOLS MODELS
# =============================================================================

class BasicDocumentItem(BaseModel):
    """SPARQL: SELECT ?entity ?title ?date ?type ?subject ?authority"""
    uri: str  # We'll map entity -> uri
    title: str
    date: str
    type: str
    subject: str
    authority: str


class BasicDocumentSearchResponse(BaseSPARQLResponse):
    documents: List[BasicDocumentItem]
    total_found: int
    keywords: List[str]
    search_type: str