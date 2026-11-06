"""Authentication, RBAC, Approval Ticket Verification and Anti-Auto-Chain Guard for Heketon MCP Server.

File: backend/app/mcp/McpAuthGuard.py
"""

from __future__ import annotations

import os
import time

from mcp.server.fastmcp import Context

from app.core.AppConfig import settings
from app.mcp.McpSchemas import McpCallerContext

VALID_ROLES: set[str] = {"HR", "ADMIN", "INTERVIEWER"}
MIN_APPROVAL_COOLDOWN_MS: int = (
    2000  # Minimum 2-second cooldown to guarantee human turn
)

# Global in-memory registry for tracking plan draft timestamps per plan_id
_PLAN_DRAFT_TIMESTAMPS_MS: dict[str, int] = {}
# Global in-memory registry for binding plan_id to its authorized approval ticket
_PLAN_APPROVAL_TICKETS: dict[str, str] = {}


def record_draft_timestamp(plan_id: str) -> None:
    """Record creation/draft timestamp for a given plan ID in milliseconds."""
    clean_id = str(plan_id).strip()
    _PLAN_DRAFT_TIMESTAMPS_MS[clean_id] = int(time.time() * 1000)


def register_plan_approval_ticket(plan_id: str, ticket: str) -> None:
    """Register the authorized cryptographic approval ticket for a given plan ID."""
    clean_id = str(plan_id).strip()
    _PLAN_APPROVAL_TICKETS[clean_id] = ticket.strip()


def verify_plan_approval_ticket(
    plan_id: str,
    ticket: str,
    db_plan_token: str | None = None,
) -> tuple[bool, str | None]:
    """Verify that the submitted approval ticket matches the issued ticket for the plan.

    Returns (True, None) if valid, or (False, error_message) if invalid/tampered.
    """
    clean_id = str(plan_id).strip()
    clean_ticket = str(ticket).strip()

    expected_ticket = _PLAN_APPROVAL_TICKETS.get(clean_id) or (
        db_plan_token.strip() if db_plan_token else None
    )
    if not expected_ticket:
        return (
            False,
            (
                f"Tiket persetujuan untuk ActionPlan #{clean_id} tidak ditemukan atau belum pernah diterbitkan. "
                f"Persetujuan ditolak demi keamanan."
            ),
        )

    if clean_ticket != expected_ticket:
        return (
            False,
            (
                f"Tiket persetujuan '{ticket}' tidak valid untuk ActionPlan #{clean_id}. "
                f"Tiket resmi yang diterbitkan oleh sistem tidak cocok. "
                f"Persetujuan ditolak demi keamanan."
            ),
        )
    return True, None


def check_anti_auto_chain_cooldown(plan_id: str) -> tuple[bool, str | None]:
    """Verify that approve_action_plan is not called automatically in the same turn.

    Returns (True, None) if cooldown passed, or (False, error_message) if violated.
    """
    clean_id = str(plan_id).strip()
    drafted_ms = _PLAN_DRAFT_TIMESTAMPS_MS.get(clean_id, 0)
    now_ms = int(time.time() * 1000)

    if drafted_ms > 0 and (now_ms - drafted_ms) < MIN_APPROVAL_COOLDOWN_MS:
        elapsed = now_ms - drafted_ms
        return (
            False,
            (
                f"Pelanggaran dicegah (Anti-Auto-Chain Guard / COOLDOWN_ACTIVE / Anti-Auto-Chain Violation): "
                f"approve_action_plan dipanggil terlalu cepat ({elapsed}ms < {MIN_APPROVAL_COOLDOWN_MS}ms). "
                f"Wajib menunggu respon dan persetujuan eksplisit manusia pada giliran terpisah."
            ),
        )
    return True, None


async def verify_caller_rbac(
    ctx: Context | None = None,
    caller_role_override: str | None = None,
) -> McpCallerContext:
    """Resolve and validate caller identity and role against the 3 official roles (HR, ADMIN, INTERVIEWER)."""
    # 1. Check caller_role_override (permitted in testing or non-production environment)
    if caller_role_override and settings.ENVIRONMENT != "production":
        norm = caller_role_override.strip().upper()
        if norm in VALID_ROLES:
            return McpCallerContext(
                actor_id=f"override-{norm.lower()}@heketon.local",
                role=norm,
                client_name="DemoRoleSwitcher",
            )

    # 2. Extract from FastMCP Context if available (HTTP Headers via SSE)
    if ctx:
        try:
            req_ctx = getattr(ctx, "request_context", None)
            if req_ctx:
                headers = getattr(req_ctx, "headers", {})
                actor_role = headers.get("x-actor-role") or headers.get("X-Demo-Role")
                actor_id = headers.get("x-actor-id", "anonymous@heketon.local")
                if actor_role and actor_role.upper() in VALID_ROLES:
                    return McpCallerContext(
                        actor_id=actor_id,
                        role=actor_role.upper(),
                        client_name="FastMcpClient",
                    )
        except Exception:
            pass

    # 3. Fallback to Environment Variables (Standard for Stdio Transport)
    env_role = os.getenv("HEKETON_MCP_ACTOR_ROLE", "HR").strip().upper()
    env_actor = os.getenv("HEKETON_MCP_ACTOR_ID", "hr.lead@company.com").strip()
    resolved_role = env_role if env_role in VALID_ROLES else "HR"

    return McpCallerContext(
        actor_id=env_actor,
        role=resolved_role,
        client_name="StdioDefault",
    )
