"""Authentication, RBAC, Approval Ticket Verification and Anti-Auto-Chain Guard for Heketon MCP Server.

File: backend/app/mcp/McpAuthGuard.py
"""

from __future__ import annotations

import os
import time

from mcp.server.fastmcp import Context

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


def check_anti_auto_chain_cooldown(
    plan_id: str,
    simulated_elapsed_ms: int | None = None,
) -> tuple[bool, str | None]:
    """Verify that approve_action_plan is not called automatically in the same turn.

    Supports simulated_elapsed_ms for deterministic automated testing.
    Returns (True, None) if cooldown passed, or (False, error_message) if violated.
    """
    clean_id = str(plan_id).strip()

    if simulated_elapsed_ms is not None:
        if simulated_elapsed_ms < MIN_APPROVAL_COOLDOWN_MS:
            return (
                False,
                (
                    f"Pelanggaran dicegah (Anti-Auto-Chain Guard / COOLDOWN_ACTIVE / Anti-Auto-Chain Violation): "
                    f"approve_action_plan dipanggil terlalu cepat ({simulated_elapsed_ms}ms < {MIN_APPROVAL_COOLDOWN_MS}ms). "
                    f"Wajib menunggu respon dan persetujuan eksplisit manusia pada giliran terpisah."
                ),
            )
        return True, None

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
    """Resolve caller identity and role for Heketon MCP Server.

    Architecture Decision (HR-Only by Default):
    The MCP server operates strictly as an internal Office Ops Copilot for HR.
    All calls are authoritatively executed under the HR Lead identity ('hr.lead@company.com', role 'HR').
    Client-side role overrides are strictly ignored or disallowed to prevent privilege spoofing.
    """
    env_actor = os.getenv("HEKETON_MCP_ACTOR_ID", "hr.lead@company.com").strip()
    return McpCallerContext(
        actor_id=env_actor,
        role="HR",
        client_name="OfficeOpsHR",
    )
