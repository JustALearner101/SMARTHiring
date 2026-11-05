"""Heketon Model Context Protocol (MCP) Package."""

from app.mcp.McpServer import heketon_mcp, mount_mcp_on_fastapi

__all__ = ["heketon_mcp", "mount_mcp_on_fastapi"]
