#!/usr/bin/env python3
"""
Smoke-test client for all MCP tools in the Luxembourg Legal Intelligence server.
Connects via HTTP transport, lists available tools, and exercises each one with example parameters.
"""

import os
import json
import asyncio
import logging

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

def serialize_mcp_result(result):
    """Convert MCP result to JSON-serializable format."""
    if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
        # Handle list of TextContent objects
        serializable_result = []
        for item in result:
            if hasattr(item, 'text'):
                serializable_result.append(item.text)
            else:
                serializable_result.append(str(item))
        return serializable_result
    elif hasattr(result, 'text'):
        # Handle single TextContent object
        return result.text
    elif isinstance(result, dict):
        # Handle dict with potential TextContent values
        serialized = {}
        for k, v in result.items():
            if hasattr(v, 'text'):
                serialized[k] = v.text
            elif hasattr(v, '__iter__') and not isinstance(v, (str, dict)):
                serialized[k] = [item.text if hasattr(item, 'text') else str(item) for item in v]
            else:
                serialized[k] = v
        return serialized
    else:
        return str(result)


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Always target the local MCP server on port 8080 for smoke testing
    mcp_server_url = "http://localhost:8080"
    logger.info("🌐 Connecting to local MCP server at %s/mcp/", mcp_server_url)
    transport = StreamableHttpTransport(url=f"{mcp_server_url}/mcp/")

    async with Client(transport) as client:
        tools = await client.list_tools()
        logger.info("Available MCP tools: %s", tools)

        # 1. search_documents
        keywords = ["sarl", "condition", "creation"]
        limit = 5
        logger.info("Testing search_documents: keywords=%s, limit=%d", keywords, limit)
        search_res = await client.call_tool("search_documents", {"keywords": keywords, "limit": limit})
        print(json.dumps(serialize_mcp_result(search_res), indent=2))

        # Determine a document URI for downstream calls
        search_data = serialize_mcp_result(search_res) if isinstance(search_res, str) else search_res
        docs = search_data.get("documents", []) if isinstance(search_data, dict) else []
        doc_uri = docs[0]["uri"] if docs else None
        if not doc_uri:
            logger.warning("No documents returned by search_documents; skipping doc-based tests")
            return

        # 2. get_citations
        logger.info("Testing get_citations for %s", doc_uri)
        cit_res = await client.call_tool(
            "get_citations",
            {"document_uri": doc_uri, "type_filter": [], "limit": 5, "offset": 0},
        )
        print(json.dumps(serialize_mcp_result(cit_res), indent=2))

        # 3. get_amendments
        start_date = "2020-01-01"
        logger.info("Testing get_amendments for %s since %s", doc_uri, start_date)
        amend_res = await client.call_tool(
            "get_amendments",
            {"document_uri": doc_uri, "start_date": start_date, "limit": 5, "offset": 0},
        )
        print(json.dumps(serialize_mcp_result(amend_res), indent=2))

        # 4. check_legal_status
        logger.info("Testing check_legal_status for %s", doc_uri)
        status_res = await client.call_tool("check_legal_status", {"document_uri": doc_uri})
        print(json.dumps(serialize_mcp_result(status_res), indent=2))

        # 5. get_relationships
        logger.info("Testing get_relationships for %s", doc_uri)
        rel_res = await client.call_tool(
            "get_relationships", {"document_uri": doc_uri, "limit": 5, "offset": 0}
        )
        print(json.dumps(serialize_mcp_result(rel_res), indent=2))

        # 6. extract_content
        logger.info("Testing extract_content for %s", doc_uri)
        content_res = await client.call_tool(
            "extract_content", {"document_uris": [doc_uri], "max_documents": 1, "prefer_html": True}
        )
        print(json.dumps(serialize_mcp_result(content_res), indent=2))

        # 7. discover_foundation_laws
        domain = "commercial"
        foundation_keywords = ["sarl", "commercial"]
        logger.info(
            "Testing discover_foundation_laws: domain=%s, keywords=%s", domain, foundation_keywords
        )
        foundation_res = await client.call_tool(
            "discover_foundation_laws",
            {"legal_domain": domain, "keywords": foundation_keywords, "max_results": 5},
        )
        print(json.dumps(serialize_mcp_result(foundation_res), indent=2))

        # 8. super_search
        super_keywords = ["sarl", "condition", "creation"]
        logger.info(
            "Testing super_search: keywords=%s, max_results=5", super_keywords
        )
        super_res = await client.call_tool(
            "super_search", {"keywords": super_keywords, "max_results": 5}
        )
        print(json.dumps(serialize_mcp_result(super_res), indent=2))


if __name__ == "__main__":
    asyncio.run(main())