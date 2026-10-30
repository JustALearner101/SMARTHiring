from typing import Any, Literal
from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class AuditEventDTO(BaseDTO):
    id: str
    timestamp: str
    event_type: str
    title: str
    description: str
    actor: str
    status_badge: Literal["success", "warning", "error", "info"]
    metadata: dict[str, Any] | None = None


class HashChainVerificationDTO(BaseDTO):
    """Hasil verifikasi integritas kriptografis ledger hash-chain."""
    is_valid: bool
    total_blocks: int
    genesis_hash: str
    latest_hash: str
    algorithm: str = "SHA-256"
    broken_at_block_id: int | None = None
    verified_at: str


class AuditStatsDTO(BaseDTO):
    """Metrik agregasi sistem Audit & Security."""
    total_events: int = 0
    total_system_logs: int = 0
    total_system_errors: int = 0
    hash_chain_valid: bool = True
    latest_event_timestamp: str | None = None
