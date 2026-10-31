import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.AuditLogDTO import (
    AuditEventDTO,
    AuditStatsDTO,
    HashChainVerificationDTO,
)
from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.model.AuditModel import AuditLog, SystemLog
from app.repository.AuditLogRepository import AuditLogRepository


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_repo = AuditLogRepository(session)

    async def log_event(
        self,
        event_type: str,
        actor: str,
        actor_type: str,
        title: str,
        description: str,
        metadata: dict[str, Any] | None = None,
        job_id: int | None = None,
    ) -> AuditEventDTO:
        latest = await self.audit_repo.get_latest_audit_log()
        prev_hash = latest.vhash if latest else "GENESIS_BLOCK_000000000000000000000000000000000000000000000000"

        now_str = datetime.now(UTC).isoformat()
        payload_str = json.dumps(metadata or {}, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        chain_string = f"{prev_hash}:{payload_hash}:{event_type}:{now_str}"
        current_hash = hashlib.sha256(chain_string.encode()).hexdigest()

        saved = await self.audit_repo.append_audit_log(
            job_id=job_id,
            actor_type=actor_type,
            actor_id=actor,
            event_type=event_type,
            payload_hash=payload_hash,
            masked_detail=description,
            prev_hash=prev_hash,
            current_hash=current_hash,
        )

        badge = "success"
        if "INJECTION" in event_type or "BLOCKED" in event_type or "REJECT" in event_type:
            badge = "error"
        elif "CLARIFICATION" in event_type or "ESCALATED" in event_type:
            badge = "warning"

        return AuditEventDTO(
            id=str(saved.nid),
            timestamp=saved.dcrea.isoformat(),
            event_type=event_type,
            title=title,
            description=description,
            actor=actor,
            status_badge=badge,  # type: ignore[arg-type]
            metadata={"hash": current_hash, "prev_hash": prev_hash, **(metadata or {})},
        )

    async def list_audit_events(
        self,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[AuditEventDTO]:
        p = params or PaginationParams()
        logs, total = await self.audit_repo.list_audit_logs(offset=p.offset, limit=p.limit)
        events = []
        for log in logs:
            badge = "success"
            if "INJECTION" in log.vevent_type or "BLOCKED" in log.vevent_type or "REJECT" in log.vevent_type:
                badge = "error"
            elif "CLARIFICATION" in log.vevent_type or "ESCALATED" in log.vevent_type:
                badge = "warning"

            events.append(
                AuditEventDTO(
                    id=str(log.nid),
                    timestamp=log.dcrea.isoformat(),
                    event_type=log.vevent_type,
                    title=f"Event {log.vevent_type}",
                    description=log.vmasked_detail,
                    actor=log.vactor_id,
                    status_badge=badge,  # type: ignore[arg-type]
                    metadata={"hash": log.vhash, "prev_hash": log.vprev_hash},
                )
            )
        return PaginatedResponse.create(
            items=events,
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def verify_hash_chain(self) -> HashChainVerificationDTO:
        """Verifikasi integritas kriptografis rantai hash SHA-256 seluruh entri audit log."""
        stmt = select(AuditLog).order_by(AuditLog.nid.asc())
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        now_str = datetime.now(UTC).isoformat()
        genesis_default = "GENESIS_BLOCK_000000000000000000000000000000000000000000000000"

        if not logs:
            return HashChainVerificationDTO(
                is_valid=True,
                total_blocks=0,
                genesis_hash=genesis_default,
                latest_hash=genesis_default,
                verified_at=now_str,
            )

        genesis_hash = logs[0].vprev_hash or genesis_default
        prev_hash = genesis_hash

        for log in logs:
            if log.vprev_hash != prev_hash:
                return HashChainVerificationDTO(
                    is_valid=False,
                    total_blocks=len(logs),
                    genesis_hash=genesis_hash,
                    latest_hash=logs[-1].vhash,
                    broken_at_block_id=log.nid,
                    verified_at=now_str,
                )
            prev_hash = log.vhash

        return HashChainVerificationDTO(
            is_valid=True,
            total_blocks=len(logs),
            genesis_hash=genesis_hash,
            latest_hash=logs[-1].vhash,
            verified_at=now_str,
        )

    async def get_audit_stats(self) -> AuditStatsDTO:
        """Menghitung metrik agregat untuk dashboard Audit & Security."""
        # 1. Total event audit
        total_stmt = select(func.count()).select_from(AuditLog)
        total_events = (await self.session.execute(total_stmt)).scalar_one() or 0

        # 2. Total log teknis sistem
        sys_stmt = select(func.count()).select_from(SystemLog)
        total_system_logs = (await self.session.execute(sys_stmt)).scalar_one() or 0

        # 3. Total error di system logs
        err_stmt = (
            select(func.count())
            .select_from(SystemLog)
            .where(SystemLog.vlog_level == "ERROR")
        )
        total_system_errors = (await self.session.execute(err_stmt)).scalar_one() or 0

        # 4. Latest event
        latest_stmt = select(AuditLog.dcrea).order_by(AuditLog.nid.desc()).limit(1)
        latest_dt = (await self.session.execute(latest_stmt)).scalar_one_or_none()

        # 5. Cek validitas hash chain
        verification = await self.verify_hash_chain()

        return AuditStatsDTO(
            total_events=total_events,
            total_system_logs=total_system_logs,
            total_system_errors=total_system_errors,
            hash_chain_valid=verification.is_valid,
            latest_event_timestamp=latest_dt.isoformat() if latest_dt else None,
        )
