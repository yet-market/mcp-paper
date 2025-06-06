"""
Luxembourg Legal Content Processing Module
Simple content extraction and processing for legal documents.
"""

import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import requests
from .extractors.content_processor import ContentProcessor

logger = logging.getLogger(__name__)


class LuxembourgContent:
    """Simple content extraction for Luxembourg legal documents."""
    
    def __init__(self):
        self.content_processor = ContentProcessor()
    
    def extract_document_content(self, document_uri: str) -> Optional[Dict[str, Any]]:
        """Extract content from a Luxembourg legal document.
        
        Args:
            document_uri: URI of the document to extract
            
        Returns:
            Dictionary with extracted content or None if failed
        """
        logger.info(f"📄 CONTENT EXTRACTION: {document_uri}")
        
        try:
            content = self.content_processor.extract_entity_content(document_uri)
            
            if content:
                logger.info(f"✅ Content extracted: {len(content.get('text', ''))} characters")
                return content
            else:
                logger.warning(f"❌ Content extraction failed for {document_uri}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Content extraction error: {str(e)}")
            return None
    
    def assess_document_relevance(self, documents: List[Dict], legal_question: str) -> List[Dict]:
        """Assess which documents are most relevant to a legal question.
        
        Args:
            documents: List of documents with titles
            legal_question: The legal question being researched
            
        Returns:
            Documents ranked by relevance with enhanced legal hierarchy scoring
        """
        logger.info(f"📊 RELEVANCE ASSESSMENT: {len(documents)} documents")
        
        # Enhanced relevance with legal hierarchy priority
        question_keywords = set(legal_question.lower().split())
        
        scored_documents = []
        for doc in documents:
            title = doc.get('title', '').lower()
            doc_type = doc.get('type', '')
            
            # Base relevance score
            title_keywords = set(title.split())
            overlap = len(question_keywords.intersection(title_keywords))
            relevance_score = overlap / max(len(question_keywords), 1)
            
            # Legal hierarchy boost (Luxembourg specific)
            if 'BaseAct' in doc_type or 'ConstitutionalAct' in doc_type:
                relevance_score += 0.4  # Constitutional/foundational law
            elif 'Act' in doc_type or 'Law' in doc_type:
                relevance_score += 0.3  # Regular laws
            elif 'Regulation' in doc_type or 'MemorialA' in doc_type:
                relevance_score += 0.2  # Regulations
            elif 'AdministrativeDecision' in doc_type:
                relevance_score += 0.1  # Administrative decisions
            
            # Date relevance (prefer recent documents)
            date_str = doc.get('date', '')
            if date_str:
                try:
                    import datetime
                    if 'T' in date_str:
                        doc_date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        doc_date = datetime.datetime.strptime(date_str[:10], '%Y-%m-%d')
                    now = datetime.datetime.now()
                    years_old = (now - doc_date).days / 365.25
                    if years_old < 2:
                        relevance_score += 0.15  # Very recent
                    elif years_old < 5:
                        relevance_score += 0.1   # Recent
                    elif years_old > 20:
                        relevance_score -= 0.05  # Old documents penalty
                except:
                    pass
            
            doc_with_score = doc.copy()
            doc_with_score['relevance_score'] = relevance_score
            scored_documents.append(doc_with_score)
        
        # Sort by relevance score (highest first)
        scored_documents.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ Enhanced relevance assessment complete, top score: {scored_documents[0]['relevance_score']:.2f} (type: {scored_documents[0].get('type', 'unknown')})")
        
        return scored_documents
    
    def recommend_document_types(self, legal_question: str) -> List[str]:
        """Recommend document types based on the legal question.
        
        Args:
            legal_question: The legal question
            
        Returns:
            List of recommended JOLUX document types
        """
        question_lower = legal_question.lower()
        
        # Simple rule-based recommendations
        if any(word in question_lower for word in ['comment', 'procédure', 'créer', 'formation']):
            # Procedural questions - need laws and regulations
            return ['Act', 'BaseAct', 'Regulation']
        elif any(word in question_lower for word in ['définition', 'qu\'est-ce', 'signifie']):
            # Definitional questions - prefer legal acts
            return ['Act', 'BaseAct']
        elif any(word in question_lower for word in ['obligation', 'devoir', 'doit']):
            # Obligation questions - laws and regulations
            return ['Act', 'Regulation']
        else:
            # General questions - all legal documents
            return ['Act', 'BaseAct', 'Regulation', 'LegalResource']