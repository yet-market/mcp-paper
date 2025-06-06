"""
SPARQL-enabled MCP Server.

This package provides a SPARQL endpoint integration for MCP servers,
with support for result formatting and query caching.

Imagined and developed by Temkit Sid-Ali for Yet.lu

This project is licensed under a dual-license model:
- Open Source: GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial: Proprietary license available for commercial use

Copyright (c) 2025 Yet.lu
"""

__version__ = "0.2.0"
__author__ = "Temkit Sid-Ali"
__email__ = "contact@yet.lu"
__license__ = "AGPL-3.0 or Commercial License"
__copyright__ = "Copyright (c) 2025 Yet.lu"

from luxembourg_legal_server.core.server import SPARQLServer
from luxembourg_legal_server.core.config import SPARQLConfig

__all__ = ["SPARQLServer", "SPARQLConfig"]