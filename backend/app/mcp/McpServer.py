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
from starlette.types import ASGIApp, Receive, Scope, Send

from app.mcp.McpResources import register_heketon_mcp_resources_and_prompts
from app.mcp.McpTools import register_heketon_mcp_tools

# Resolve allowed hosts and origins dynamically with production domain support
ALLOWED_MCP_HOSTS: list[str] = [
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
    "test:*",
    "test",
    "localhost",
    "127.0.0.1",
    "smart-hiring.akhtarramadhan.dev",
    "smart-hiring.akhtarramadhan.dev:*",
]
_env_hosts = os.getenv("MCP_ALLOWED_HOSTS", "").strip()
if _env_hosts:
    for _h in _env_hosts.split(","):
        _clean_h = _h.strip()
        if _clean_h and _clean_h not in ALLOWED_MCP_HOSTS:
            ALLOWED_MCP_HOSTS.append(_clean_h)

ALLOWED_MCP_ORIGINS: list[str] = [
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
    "http://test",
    "http://test:*",
    "https://smart-hiring.akhtarramadhan.dev",
    "https://smart-hiring.akhtarramadhan.dev:*",
]
_env_origins = os.getenv("MCP_ALLOWED_ORIGINS", "").strip()
if _env_origins:
    for _o in _env_origins.split(","):
        _clean_o = _o.strip()
        if _clean_o and _clean_o not in ALLOWED_MCP_ORIGINS:
            ALLOWED_MCP_ORIGINS.append(_clean_o)

_enable_rebinding_protection = os.getenv(
    "MCP_ENABLE_DNS_REBINDING_PROTECTION", "true"
).lower() in ("true", "1", "yes")

# Inisialisasi FastMCP server dengan instruksi akuntabilitas
heketon_mcp = FastMCP(
    name="Heketon-HR-Office-Orchestrator-MCP",
    instructions=(
        "Anda terhubung ke Heketon Accountable Office Agent MCP Server. "
        "Patuhi 5 Akuntabilitas: "
        "(1) Selalu tampilkan sources_cited dari respons tool; "
        "(2) Jangan menebak kontak ambigu seperti 'Pak Budi'—tanyakan klarifikasi ke pengguna; "
        "(3) Jangan pernah memanggil approve_action_plan pada giliran yang sama dengan pembuatan draf—"
        "sajikan Confirmation Card terlebih dahulu dan tunggu persetujuan manusia pada giliran berikutnya; "
        "(4) Jika is_high_impact=True, minta konfirmasi eksplisit pengguna sebelum menyetujui; "
        "(5) Role INTERVIEWER tidak berwenang melihat gaji atau menyetujui rencana aksi."
    ),
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=_enable_rebinding_protection,
        allowed_hosts=ALLOWED_MCP_HOSTS,
        allowed_origins=ALLOWED_MCP_ORIGINS,
    ),
)

# Registrasi seluruh Tools, Resources (heketon://), dan Prompts
register_heketon_mcp_tools(heketon_mcp)
register_heketon_mcp_resources_and_prompts(heketon_mcp)


class SseHeadersMiddleware:
    """Inject no-transform and no-buffering headers to prevent Cloudflare/Nginx/proxy buffering."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            async def custom_send(message: dict) -> None:
                if message["type"] == "http.response.start":
                    headers = [
                        (k, v)
                        for k, v in message.get("headers", [])
                        if k.lower() not in (b"cache-control", b"x-accel-buffering")
                    ]
                    headers.append((b"cache-control", b"no-cache, no-transform"))
                    headers.append((b"x-accel-buffering", b"no"))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, custom_send)
        else:
            await self.app(scope, receive, send)


def mount_mcp_on_fastapi(app: FastAPI) -> None:
    """Mount endpoint MCP (SSE / Streamable HTTP) pada aplikasi FastAPI utama di /mcp dan /api/mcp."""
    # Mount tanpa mount_path agar FastMCP tidak menduplikasi prefix (misal /mcp/mcp/messages)
    mcp_asgi_app = SseHeadersMiddleware(heketon_mcp.sse_app())
    app.mount("/mcp", mcp_asgi_app, name="heketon_mcp_server")

    # Secondary mount under /api/mcp for direct proxy compatibility
    mcp_api_app = SseHeadersMiddleware(heketon_mcp.sse_app())
    app.mount("/api/mcp", mcp_api_app, name="heketon_mcp_server_api")


if __name__ == "__main__":
    # Entrypoint untuk koneksi lokal WorkBuddy via transport stdio
    transport_mode = os.getenv("HEKETON_MCP_TRANSPORT", "stdio")
    heketon_mcp.run(transport=transport_mode)
