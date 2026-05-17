#!/usr/bin/env python3
"""Paper Search MCP server runner for SAGE."""
import sys
import os

# Ensure the package is importable
from paper_search_mcp.server import mcp

if __name__ == "__main__":
    # Run as stdio MCP server (standard for Claude Code / Bob)
    mcp.run(transport="stdio")
