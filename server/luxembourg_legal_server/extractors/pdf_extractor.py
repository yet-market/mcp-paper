"""
PDF content extractor for Luxembourg legal documents using Langchain.

Fetches and extracts text content from Luxembourg government PDF documents.
"""

import logging
import tempfile
import requests
from typing import Optional, Dict, Any, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts content from Luxembourg government PDF documents using Langchain."""
    
    def __init__(self, timeout: int = 60):
        """Initialize the PDF extractor.
        
        Args:
            timeout: Request timeout in seconds (longer for PDF downloads)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP-Luxembourg-Legal/1.0 (Legal Document Processing)'
        })
        # Enable redirect following
        self.session.max_redirects = 10
    
    def extract_content(self, entity_uri: str) -> Optional[Dict[str, Any]]:
        """Extract content from a Luxembourg entity PDF document.
        
        Args:
            entity_uri: The base URI of the Luxembourg entity
            
        Returns:
            Dictionary with extracted content or None if extraction fails
        """
        # Use base URI directly - Luxembourg server handles content negotiation
        pdf_url = entity_uri
        
        try:
            logger.info(f"Fetching PDF content from: {pdf_url}")
            
            # Download PDF to temporary file
            temp_file_path = self._download_pdf(pdf_url)
            if not temp_file_path:
                return None
            
            # Use Langchain PyPDFLoader to extract content
            loader = PyPDFLoader(temp_file_path)
            documents = []
            
            for page in loader.lazy_load():
                documents.append(page)
            
            if not documents:
                logger.warning(f"No content found in PDF: {pdf_url}")
                return None
            
            # Process the loaded documents
            content_data = self._process_documents(documents, pdf_url)
            
            # Clean up temporary file
            try:
                import os
                os.unlink(temp_file_path)
            except:
                pass
            
            if content_data['text']:
                logger.info(f"Successfully extracted {len(content_data['text'])} characters from PDF")
                return {
                    'source_url': pdf_url,
                    'content_type': 'pdf',
                    'title': content_data['title'],
                    'text': content_data['text'],
                    'metadata': content_data['metadata']
                }
            else:
                logger.warning(f"No text content found in PDF: {pdf_url}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to extract PDF content from {pdf_url}: {e}")
            return None
    
    def _download_pdf(self, pdf_url: str) -> Optional[str]:
        """Download PDF to temporary file.
        
        Args:
            pdf_url: URL of the PDF to download
            
        Returns:
            Path to temporary file or None if download fails
        """
        try:
            # Use PDF Accept header and allow redirects (like curl -L)
            headers = {'Accept': 'application/pdf'}
            response = self.session.get(pdf_url, headers=headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Verify we got a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"Expected PDF but got content-type: {content_type}")
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {e}")
            return None
    
    def _process_documents(self, documents: List[Document], source_url: str) -> Dict[str, Any]:
        """Process Langchain PDF documents into structured content.
        
        Args:
            documents: List of Langchain Document objects (one per page)
            source_url: The source URL for metadata
            
        Returns:
            Dictionary with title, text, and metadata
        """
        # Combine all page content
        full_text = ""
        all_metadata = {}
        page_count = len(documents)
        
        for i, doc in enumerate(documents):
            # Add page separator
            full_text += f"\n--- Page {i + 1} ---\n"
            full_text += doc.page_content + "\n"
            
            # Merge metadata from all pages
            all_metadata.update(doc.metadata)
        
        # Clean the extracted text
        cleaned_text = self._clean_pdf_text(full_text)
        
        # Extract title from metadata or content
        title = all_metadata.get('title', '')
        if not title and cleaned_text:
            # Extract title from first meaningful lines
            lines = cleaned_text.split('\n')
            title_lines = []
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and not line.startswith('--- Page') and len(line) > 5:
                    title_lines.append(line)
                    if len(' '.join(title_lines)) > 100:  # Max title length
                        break
            title = ' '.join(title_lines)[:200]  # Truncate if too long
        
        # Extract legal document metadata
        legal_metadata = self._extract_legal_metadata(cleaned_text, all_metadata)
        legal_metadata['page_count'] = page_count
        
        return {
            'title': title,
            'text': cleaned_text,
            'metadata': legal_metadata
        }
    
    def _clean_pdf_text(self, text: str) -> str:
        """Clean extracted PDF text for legal document processing.
        
        Args:
            text: Raw extracted text from PDF
            
        Returns:
            Cleaned text suitable for AI processing
        """
        if not text:
            return ""
        
        # Split into lines for processing
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Keep page markers but clean them up
            if line.startswith('--- Page '):
                cleaned_lines.append(line)
                continue
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip lines that are just page numbers
            if line.isdigit() and len(line) <= 3:
                continue
            
            # Skip very short lines that are likely headers/footers
            if len(line) < 5:
                continue
            
            # Clean up common PDF extraction artifacts
            line = self._clean_pdf_artifacts(line)
            
            if line:
                cleaned_lines.append(line)
        
        # Join lines and clean up spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        # Remove excessive spaces
        while '  ' in cleaned_text:
            cleaned_text = cleaned_text.replace('  ', ' ')
        
        return cleaned_text.strip()
    
    def _clean_pdf_artifacts(self, line: str) -> str:
        """Clean common PDF extraction artifacts from a line.
        
        Args:
            line: Line of text to clean
            
        Returns:
            Cleaned line
        """
        # Remove common PDF artifacts
        artifacts = [
            '\x0c',  # Form feed character
            '\ufffd',  # Replacement character
        ]
        
        for artifact in artifacts:
            line = line.replace(artifact, '')
        
        # Fix common spacing issues around punctuation
        line = line.replace(' .', '.')
        line = line.replace(' ,', ',')
        line = line.replace(' ;', ';')
        line = line.replace(' :', ':')
        
        return line.strip()
    
    def _extract_legal_metadata(self, content: str, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal document metadata from PDF content.
        
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