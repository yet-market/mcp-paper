"""
Content extraction modules for Luxembourg legal documents.
Provides HTML and PDF extraction with intelligent fallback.
"""

import logging
import tempfile
import requests
from typing import Dict, List, Any, Optional
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_core.documents import Document
from .metadata_utils import extract_legal_metadata

logger = logging.getLogger(__name__)


class HTMLExtractor:
    """Extracts content from Luxembourg government HTML pages using Langchain."""
    
    def extract_content(self, entity_uri: str) -> Optional[Dict[str, Any]]:
        """Extract content from a Luxembourg entity HTML page."""
        html_url = f"{entity_uri}/fr/html"
        
        try:
            logger.info(f"Fetching HTML content from: {html_url}")
            
            loader = WebBaseLoader([html_url])
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No content found in HTML: {html_url}")
                return None
            
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
        """Process Langchain documents into structured content."""
        full_text = ""
        all_metadata = {}
        
        for doc in documents:
            full_text += doc.page_content + "\n"
            all_metadata.update(doc.metadata)
        
        cleaned_text = self._clean_text(full_text)
        
        title = all_metadata.get('title', '')
        if not title and cleaned_text:
            lines = cleaned_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and len(line) < 200:
                    title = line
                    break
        
        legal_metadata = extract_legal_metadata(cleaned_text, all_metadata)
        
        return {
            'title': title,
            'text': cleaned_text,
            'metadata': legal_metadata
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text for legal document processing."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and not self._is_navigation_text(line):
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        while '  ' in cleaned_text:
            cleaned_text = cleaned_text.replace('  ', ' ')
        
        return cleaned_text.strip()
    
    def _is_navigation_text(self, text: str) -> bool:
        """Check if text appears to be navigation/UI element."""
        nav_indicators = [
            'menu', 'navigation', 'accueil', 'home', 'recherche', 'search',
            'connexion', 'login', 'déconnexion', 'logout', 'contact',
            'aide', 'help', 'à propos', 'about', 'skip to', 'go to'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in nav_indicators)
    


class PDFExtractor:
    """Extracts content from Luxembourg government PDF documents using Langchain."""
    
    def __init__(self, timeout: int = 60):
        """Initialize the PDF extractor."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP-Luxembourg-Legal/1.0 (Legal Document Processing)'
        })
        self.session.max_redirects = 10
    
    def extract_content(self, entity_uri: str) -> Optional[Dict[str, Any]]:
        """Extract content from a Luxembourg entity PDF document."""
        pdf_url = entity_uri
        
        try:
            logger.info(f"Fetching PDF content from: {pdf_url}")
            
            temp_file_path = self._download_pdf(pdf_url)
            if not temp_file_path:
                return None
            
            loader = PyPDFLoader(temp_file_path)
            documents = []
            
            for page in loader.lazy_load():
                documents.append(page)
            
            if not documents:
                logger.warning(f"No content found in PDF: {pdf_url}")
                return None
            
            content_data = self._process_documents(documents, pdf_url)
            
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
        """Download PDF to temporary file."""
        try:
            headers = {'Accept': 'application/pdf'}
            response = self.session.get(pdf_url, headers=headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"Expected PDF but got content-type: {content_type}")
                return None
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {e}")
            return None
    
    def _process_documents(self, documents: List[Document], source_url: str) -> Dict[str, Any]:
        """Process Langchain PDF documents into structured content."""
        full_text = ""
        all_metadata = {}
        page_count = len(documents)
        
        for i, doc in enumerate(documents):
            full_text += f"\n--- Page {i + 1} ---\n"
            full_text += doc.page_content + "\n"
            all_metadata.update(doc.metadata)
        
        cleaned_text = self._clean_pdf_text(full_text)
        
        title = all_metadata.get('title', '')
        if not title and cleaned_text:
            lines = cleaned_text.split('\n')
            title_lines = []
            for line in lines[:10]:
                line = line.strip()
                if line and not line.startswith('--- Page') and len(line) > 5:
                    title_lines.append(line)
                    if len(' '.join(title_lines)) > 100:
                        break
            title = ' '.join(title_lines)[:200]
        
        legal_metadata = extract_legal_metadata(cleaned_text, all_metadata)
        legal_metadata['page_count'] = page_count
        
        return {
            'title': title,
            'text': cleaned_text,
            'metadata': legal_metadata
        }
    
    def _clean_pdf_text(self, text: str) -> str:
        """Clean extracted PDF text for legal document processing."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('--- Page '):
                cleaned_lines.append(line)
                continue
            
            if not line or line.isdigit() and len(line) <= 3 or len(line) < 5:
                continue
            
            line = self._clean_pdf_artifacts(line)
            
            if line:
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        while '  ' in cleaned_text:
            cleaned_text = cleaned_text.replace('  ', ' ')
        
        return cleaned_text.strip()
    
    def _clean_pdf_artifacts(self, line: str) -> str:
        """Clean common PDF extraction artifacts from a line."""
        artifacts = ['\x0c', '\ufffd']
        
        for artifact in artifacts:
            line = line.replace(artifact, '')
        
        line = line.replace(' .', '.').replace(' ,', ',').replace(' ;', ';').replace(' :', ':')
        
        return line.strip()
    
