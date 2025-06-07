#!/usr/bin/env python3
"""
Luxembourg Legal Intelligence MCP Server - Professional Edition
Clean, modular implementation with 6 specialized tools
"""

import argparse
import logging
from typing import List
from fastmcp import FastMCP
from luxembourg_legal.config import setup_logging, initialize_sparql
from luxembourg_legal.tools import LuxembourgLegalTools

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Luxembourg Legal Intelligence Server")

# Global tools instance
legal_tools = None


def initialize_legal_tools(sparql_endpoint: str):
    """Initialize the legal tools with SPARQL connection."""
    global legal_tools
    sparql = initialize_sparql(sparql_endpoint)
    legal_tools = LuxembourgLegalTools(sparql)


@mcp.tool(description="Find relevant legal documents with complete metadata using single-keyword strategy")
def search_documents(keyword: str, limit: int = 50):
    """Search Luxembourg legal documents using proven single-keyword strategy."""
    return legal_tools.search_documents(keyword, limit)


@mcp.tool(description="Get complete citation network for legal precedent analysis")
def get_citations(document_uri: str):
    """Get complete citation network using proven jolux:cites relationships."""
    return legal_tools.get_citations(document_uri)


@mcp.tool(description="Track complete legal evolution and modification history")
def get_amendments(document_uri: str):
    """Get complete amendment history using proven jolux:modifies relationships."""
    return legal_tools.get_amendments(document_uri)


@mcp.tool(description="Check current legal validity and consolidation status")
def check_legal_status(document_uri: str):
    """Check current legal validity using proven jolux:repeals and jolux:consolidates."""
    return legal_tools.check_legal_status(document_uri)


@mcp.tool(description="Discover legal foundations and implementing acts")
def get_relationships(document_uri: str):
    """Get legal foundations and implementing acts using proven JOLUX relationships."""
    return legal_tools.get_relationships(document_uri)


@mcp.tool(description="Extract actual legal text from Luxembourg documents with HTML/PDF fallback")
def extract_content(document_uris: List[str], max_documents: int = 3, prefer_html: bool = True):
    """Extract real legal text using proven HTML/PDF extraction with fallback."""
    return legal_tools.extract_content(document_uris, max_documents, prefer_html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Luxembourg Legal Intelligence MCP Server")
    parser.add_argument("--endpoint", required=True, help="SPARQL endpoint URL")
    parser.add_argument("--transport", default="stdio", help="Transport type")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Initialize legal tools
    initialize_legal_tools(args.endpoint)
    
    # Run server
    logger.info(f"🚀 Starting Luxembourg Legal Intelligence MCP Server")
    logger.info(f"📊 SPARQL endpoint: {args.endpoint}")
    logger.info(f"🔧 6 Professional Tools: search_documents, get_citations, get_amendments, check_legal_status, get_relationships, extract_content")
    logger.info(f"⚡ Single-keyword precision strategy")
    logger.info(f"📄 HTML/PDF content extraction with fallback")
    
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)