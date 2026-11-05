"""Dual-Transport Model Context Protocol (MCP) Server for Heketon.

File: backend/app/mcp/McpServer.py
Supports:
  1. Streamable HTTP / SSE mounted on FastAPI at /mcp
  2. Standard I/O (stdio) via `uv run python -m app.mcp.McpServer`
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.mcp.McpResources import register_heketon_mcp_resources_and_prompts
from app.mcp.McpTools import register_heketon_mcp_tools

# Inisialisasi FastMCP server dengan instruksi akuntabilitas resmi 5 Pilar
heketon_mcp = FastMCP(
    name="Heketon-HR-Office-Orchestrator-MCP",
    instructions=(
        "Anda terhubung ke Heketon Accountable Office Agent MCP Server. "
        "Patuhi 5 Pilar Akuntabilitas: "
        "(1) Selalu tampilkan sources_cited dari respons tool; "
        "(2) Jangan menebak kontak ambigu seperti 'Pak Budi'—tanyakan klarifikasi ke pengguna; "
        "(3) Jangan pernah memanggil approve_action_plan pada giliran yang sama dengan pembuatan draf—"
        "sajikan Confirmation Card terlebih dahulu dan tunggu persetujuan manusia pada giliran berikutnya; "
        "(4) Jika is_high_impact=True, minta konfirmasi eksplisit pengguna sebelum menyetujui; "
        "(5) Role INTERVIEWER tidak berwenang melihat gaji atau menyetujui rencana aksi."
    ),
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "127.0.0.1:*",
            "localhost:*",
            "[::1]:*",
            "test:*",
            "test",
            "localhost",
            "127.0.0.1",
        ],
        allowed_origins=[
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
            "http://test",
            "http://test:*",
        ],
    ),
)

# Registrasi seluruh Tools, Resources (heketon://), dan Prompts
register_heketon_mcp_tools(heketon_mcp)
register_heketon_mcp_resources_and_prompts(heketon_mcp)


def mount_mcp_on_fastapi(app: FastAPI) -> None:
    """Mount endpoint MCP (SSE / Streamable HTTP) pada aplikasi FastAPI utama di /mcp."""
    mcp_asgi_app = heketon_mcp.sse_app()
    app.mount("/mcp", mcp_asgi_app, name="heketon_mcp_server")


if __name__ == "__main__":
    # Entrypoint untuk koneksi lokal WorkBuddy via transport stdio
    transport_mode = os.getenv("HEKETON_MCP_TRANSPORT", "stdio")
    heketon_mcp.run(transport=transport_mode)
