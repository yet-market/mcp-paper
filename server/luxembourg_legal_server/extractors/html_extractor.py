"""
HTML content extractor for Luxembourg legal documents using Langchain.

Fetches and extracts clean text content from Luxembourg government HTML pages.
"""

import logging
from typing import Optional, Dict, Any, List
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class HTMLExtractor:
    """Extracts content from Luxembourg government HTML pages using Langchain."""
    
    def __init__(self):
        """Initialize the HTML extractor."""
        pass
    
    def extract_content(self, entity_uri: str) -> Optional[Dict[str, Any]]:
        """Extract content from a Luxembourg entity HTML page.
        
        Args:
            entity_uri: The base URI of the Luxembourg entity
            
        Returns:
            Dictionary with extracted content or None if extraction fails
        """
        html_url = f"{entity_uri}/fr/html"
        
        try:
            logger.info(f"Fetching HTML content from: {html_url}")
            
            # Use Langchain WebBaseLoader to load HTML content
            loader = WebBaseLoader([html_url])
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No content found in HTML: {html_url}")
                return None
            
            # Process the loaded documents
            content_data = self._process_documents(documents, html_url)
            
            if content_data['text']:
                logger.info(f"Successfully extracted {len(content_data['text'])} characters from HTML")
                return {
                    'source_url': html_url,
                    'content_type': 'html',
                    'title': content_data['title'],
                    'text': content_data['text'],
                    'metadata': content_data['metadata']
                }
            else:
                logger.warning(f"No meaningful content found in HTML: {html_url}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to extract HTML content from {html_url}: {e}")
            return None
    
    def _process_documents(self, documents: List[Document], source_url: str) -> Dict[str, Any]:
        """Process Langchain documents into structured content.
        
        Args:
            documents: List of Langchain Document objects
            source_url: The source URL for metadata
            
        Returns:
            Dictionary with title, text, and metadata
        """
        # Combine all document content
        full_text = ""
        all_metadata = {}
        
        for doc in documents:
            full_text += doc.page_content + "\n"
            # Merge metadata from all documents
            all_metadata.update(doc.metadata)
        
        # Clean the extracted text
        cleaned_text = self._clean_text(full_text)
        
        # Extract title from metadata or content
        title = all_metadata.get('title', '')
        if not title and cleaned_text:
            # Extract title from first meaningful line
            lines = cleaned_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and len(line) < 200:
                    title = line
                    break
        
        # Extract legal document metadata
        legal_metadata = self._extract_legal_metadata(cleaned_text, all_metadata)
        
        return {
            'title': title,
            'text': cleaned_text,
            'metadata': legal_metadata
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text for legal document processing.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text suitable for AI processing
        """
        if not text:
            return ""
        
        # Split into lines and clean each
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and navigation elements
            if line and len(line) > 2 and not self._is_navigation_text(line):
                cleaned_lines.append(line)
        
        # Join with single newlines and remove excessive whitespace
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        # Remove excessive spaces
        while '  ' in cleaned_text:
            cleaned_text = cleaned_text.replace('  ', ' ')
        
        return cleaned_text.strip()
    
    def _is_navigation_text(self, text: str) -> bool:
        """Check if text appears to be navigation/UI element.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be navigation
        """
        nav_indicators = [
            'menu', 'navigation', 'accueil', 'home', 'recherche', 'search',
            'connexion', 'login', 'déconnexion', 'logout', 'contact',
            'aide', 'help', 'à propos', 'about', 'skip to', 'go to'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in nav_indicators)
    
    def _extract_legal_metadata(self, content: str, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal document metadata from HTML content.
        
        Args:
            content: Clean text content
            base_metadata: Base metadata from Langchain
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = base_metadata.copy()
        
        # Look for document dates in content
        import re
        date_patterns = [
            r'\d{1,2}[./]\d{1,2}[./]\d{4}',  # DD/MM/YYYY or DD.MM.YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                metadata['found_dates'] = matches[:3]  # First 3 dates found
                break
        
        # Look for document numbers/references
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
        
        # Document type indicators
        content_lower = content.lower()
        if any(word in content_lower for word in ['loi', 'law']):
            metadata['document_type'] = 'loi'
        elif any(word in content_lower for word in ['règlement', 'regulation']):
            metadata['document_type'] = 'règlement'
        elif any(word in content_lower for word in ['arrêté', 'arrete']):
            metadata['document_type'] = 'arrêté'
        elif any(word in content_lower for word in ['décret', 'decree']):
            metadata['document_type'] = 'décret'
        elif any(word in content_lower for word in ['société', 'company', 'sàrl', 'sa ']):
            metadata['document_type'] = 'company_info'
        
        return metadata