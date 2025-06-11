#!/usr/bin/env python3
"""
Luxembourg Legal Intelligence MCP Server - Professional Edition
Clean, modular implementation with streamlined workflow tools
"""

import argparse
import logging
from typing import List
from fastmcp import FastMCP
from luxembourg_legal.config import setup_logging, initialize_sparql
from luxembourg_legal.config import Config
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


# PHASE 1: Discovery Tools (Find Big Laws)
@mcp.tool(description="STEP 1A: Find laws that other laws reference a lot = important foundational laws")
def find_most_cited_laws(keywords: List[str], limit: int = 10):
    """Find laws that other laws reference a lot = important foundational laws."""
    return legal_tools.find_most_cited_laws(keywords, limit)


@mcp.tool(description="STEP 1B: Find laws that get updated frequently = active/important laws")
def find_most_changed_laws(keywords: List[str], limit: int = 10):
    """Find laws that get updated frequently = active/important laws."""
    return legal_tools.find_most_changed_laws(keywords, limit)


@mcp.tool(description="STEP 1C: Find recent laws that haven't been canceled = current legal framework")
def find_newest_active_laws(keywords: List[str], limit: int = 10):
    """Find recent laws that haven't been canceled = current legal framework."""
    return legal_tools.find_newest_active_laws(keywords, limit)


@mcp.tool(description="STEP 1D: Find LOI and CODE documents = most powerful legal authority")
def find_highest_authority_laws(keywords: List[str], limit: int = 10):
    """Find LOI and CODE documents = most powerful legal authority."""
    return legal_tools.find_highest_authority_laws(keywords, limit)


# PHASE 2: Analysis Tools (Check Results)
@mcp.tool(description="STEP 2: Compare results from multiple discovery methods to find overlaps and rank importance")
def compare_results(result_sets: List[dict]):
    """Compare results from multiple discovery methods to find overlaps and rank importance."""
    return legal_tools.compare_results(result_sets)


@mcp.tool(description="STEP 2B: Check how important laws connect to each other through citations")
def check_connections(document_uris: List[str]):
    """Check how important laws connect to each other through citations."""
    return legal_tools.check_connections(document_uris)


# PHASE 3: Relationship Tools (Build Family Tree)
@mcp.tool(description="STEP 3A: Find what this important law points to (its legal foundations)")
def find_what_law_references(document_uri: str, limit: int = 20):
    """Find what this important law points to (its legal foundations)."""
    return legal_tools.find_what_law_references(document_uri, limit)


@mcp.tool(description="STEP 3B: Find what other laws point to this one (its legal impact)")
def find_what_references_law(document_uri: str, limit: int = 20):
    """Find what other laws point to this one (its legal impact)."""
    return legal_tools.find_what_references_law(document_uri, limit)


@mcp.tool(description="STEP 3C: Find how this law has changed over time (amendment history)")
def find_amendment_chain(document_uri: str, limit: int = 20):
    """Find how this law has changed over time (amendment history)."""
    return legal_tools.find_amendment_chain(document_uri, limit)


# PHASE 4: Final Tools (Complete Picture)
@mcp.tool(description="STEP 4A: Make sure the laws aren't canceled/repealed")
def verify_still_valid(document_uris: List[str]):
    """Make sure the laws aren't canceled/repealed."""
    return legal_tools.verify_still_valid(document_uris)


@mcp.tool(description="STEP 4B: Put all discovered laws in order of importance using multiple factors")
def rank_by_importance(laws_data: dict):
    """Put all discovered laws in order of importance using multiple factors."""
    return legal_tools.rank_by_importance(laws_data)


@mcp.tool(description="STEP 4C: Create complete map showing all laws and how they connect")
def create_final_map(ranked_laws: List[dict], connections: List[dict]):
    """Create complete map showing all laws and how they connect."""
    return legal_tools.create_final_map(ranked_laws, connections)


# BONUS: Simple Tools
@mcp.tool(description="BONUS: Simple keyword search for when you just need to find specific documents")
def basic_document_search(keywords: List[str], limit: int = 50):
    """Simple keyword search for when you just need to find specific documents."""
    return legal_tools.basic_document_search(keywords, limit)


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
    logger.info(f"🚀 Starting Luxembourg Legal Intelligence MCP Server - Streamlined Workflow Edition")
    logger.info(f"📊 SPARQL endpoint: {args.endpoint}")
    logger.info(f"🔧 Phase 1 (Discovery): find_most_cited_laws, find_most_changed_laws, find_newest_active_laws, find_highest_authority_laws")
    logger.info(f"🔍 Phase 2 (Analysis): compare_results, check_connections")
    logger.info(f"🕸️ Phase 3 (Relationships): find_what_law_references, find_what_references_law, find_amendment_chain")
    logger.info(f"🏆 Phase 4 (Final): verify_still_valid, rank_by_importance, create_final_map")
    logger.info(f"🎁 Bonus: basic_document_search")
    logger.info(f"⚡ Simple workflow: Discovery → Analysis → Relationships → Final Map")

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
