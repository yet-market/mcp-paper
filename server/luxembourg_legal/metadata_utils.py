"""
Shared metadata extraction utilities for Luxembourg legal documents.
"""

import re
from typing import Dict, Any


def extract_legal_metadata(content: str, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract legal document metadata from content.
    
    Args:
        content: Document text content
        base_metadata: Base metadata dictionary to extend
        
    Returns:
        Enhanced metadata dictionary with legal document information
    """
    metadata = base_metadata.copy()
    
    # Extract dates using multiple patterns
    date_patterns = [
        r'\d{1,2}[./]\d{1,2}[./]\d{4}',  # DD/MM/YYYY or DD.MM.YYYY
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}'  # French dates
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            metadata['found_dates'] = matches[:3]  # First 3 dates found
            break
    
    # Extract document references
    ref_patterns = [
        r'[A-Z]{1,3}[\s-]?\d{4}[\s-]?\d+',  # Legal reference patterns
        r'n°\s*\d+',  # Numéro patterns
        r'ref[\.:]\s*[\w\d\-/]+',  # Reference patterns
    ]
    
    for pattern in ref_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            metadata['references'] = matches[:3]
            break
    
    # Detect document type from content
    content_lower = content.lower()
    
    # Luxembourg legal document type patterns
    type_patterns = {
        'loi': ['loi', 'law'],
        'règlement': ['règlement', 'regulation', 'reglement'],
        'arrêté': ['arrêté', 'arrete', 'ministerial'],
        'décret': ['décret', 'decree'],
        'code': ['code'],
        'constitution': ['constitution'],
        'circulaire': ['circulaire', 'circular'],
        'directive': ['directive'],
        'ordonnance': ['ordonnance'],
        'convention': ['convention', 'accord', 'agreement'],
        'jurisprudence': ['cour', 'tribunal', 'jugement', 'arrêt', 'court'],
        'company_info': ['société', 'company', 'enterprise', 'sàrl', 'sa ', 'rcs']
    }
    
    for doc_type, patterns in type_patterns.items():
        if any(pattern in content_lower for pattern in patterns):
            metadata['document_type'] = doc_type
            break
    
    return metadata