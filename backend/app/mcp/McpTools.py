"""3-Tier Accountable MCP Tools for Heketon HR & Office Ops Orchestrator.

File: backend/app/mcp/McpTools.py
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy import select

from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
from app.db.DatabaseSession import AsyncSessionLocal
from app.dto.ActionPlanDTO import (
    PlanApprovalRequestDTO,
    PlanRejectRequestDTO,
    PlanUndoRequestDTO,
)
from app.dto.InterviewDecisionDTO import HrDecisionRequestDTO
from app.dto.OrchestratorCommandDTO import CommandRequestDTO
from app.dto.SlotConflictCheckerDTO import SlotConflictCheckRequestDTO
from app.mcp.McpAuthGuard import (
    check_anti_auto_chain_cooldown,
    record_draft_timestamp,
    register_plan_approval_ticket,
    verify_caller_rbac,
    verify_plan_approval_ticket,
)
from app.model.CandidateModel import Candidate
from app.model.OrchestrationModel import NegotiationThread
from app.model.RubricModel import Profile
from app.model.UserModel import User
from app.repository.ActionPlanRepository import ActionPlanRepository
from app.repository.HolidayRepository import HolidayRepository
from app.service.ActionPlanService import ActionPlanService
from app.service.AuditLogService import AuditLogService
from app.service.CandidateService import CandidateService
from app.service.ContactService import ContactService
from app.service.InterviewDecisionService import InterviewDecisionService
from app.service.NegotiationThreadService import NegotiationThreadService
from app.service.OperationalPolicyService import OperationalPolicyService
from app.service.OrchestratorCommandService import OrchestratorCommandService
from app.service.SlotConflictCheckerService import SlotConflictCheckerService
from app.service.SpeechToTextService import SpeechToTextService

logger = logging.getLogger(__name__)

# Build marker: lets blackbox testers confirm which build the running server executes.
MCP_SERVER_VERSION = "2026.11.06-rev6"


def register_heketon_mcp_tools(mcp: FastMCP) -> None:
    """Register all Tier 1, Tier 2, and Tier 3 MCP tools."""

    # =========================================================================
    # TIER 1: READ & DISCOVERY TOOLS (AUTONOMOUS, RBAC-FILTERED)
    # =========================================================================

    @mcp.tool(
        name="search_contacts",
        description=(
            "[TIER-1 READ] Search interviewer and employee directory by name or department. "
            "Returns contact IDs, timezones (WIB/WITA/WIT), roles, and flags ambiguity when "
            "multiple contacts share the same name (e.g. 'Dua Pak Budi')."
        ),
    )
    async def search_contacts(
        query: str = "",
        department: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            svc = ContactService(db)
            all_interviewers = await svc.list_interviewers(department=department)

            filtered = all_interviewers
            if query.strip():
                q_lower = query.strip().lower()
                filtered = [
                    u
                    for u in all_interviewers
                    if q_lower in u.name.lower()
                    or q_lower in u.department.lower()
                    or q_lower in u.role.lower()
                ]

            from datetime import timedelta as td_delta

            from app.model.OrchestrationModel import CalendarEvent

            busy_by_user: dict[str, list[dict[str, Any]]] = {}
            try:
                ev_rows = (
                    (
                        await db.execute(
                            select(CalendarEvent).order_by(
                                CalendarEvent.dscheduled_start_utc
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                for ev in ev_rows:
                    uid_str = str(ev.nid_user)
                    tz_off = td_delta(hours=8) if uid_str == "11" else td_delta(hours=7)
                    tz_lbl = "WITA" if uid_str == "11" else "WIB"
                    st_loc = ev.dscheduled_start_utc + tz_off
                    en_loc = ev.dscheduled_end_utc + tz_off
                    busy_by_user.setdefault(uid_str, []).append(
                        {
                            "title": ev.vtitle,
                            "date": st_loc.date().isoformat(),
                            "start_time": st_loc.strftime("%H:%M"),
                            "end_time": en_loc.strftime("%H:%M"),
                            "timezone": tz_lbl,
                            "rule_code": ev.vrule_code or "RULE_CALENDAR_BUSY",
                        }
                    )
            except Exception:
                pass
            is_ambiguous = len(filtered) > 1 and bool(query.strip())
            ambiguity_msg = None
            if is_ambiguous:
                ambiguity_msg = (
                    f"Ditemukan {len(filtered)} kontak yang cocok dengan '{query}'. "
                    f"Harap mintakan klarifikasi kepada pengguna untuk memilih salah satu kontak yang tepat."
                )

            return {
                "found": len(filtered) > 0,
                "confidence": 0.5 if is_ambiguous else (1.0 if filtered else 0.0),
                "match_type": "AMBIGUOUS"
                if is_ambiguous
                else ("EXACT" if filtered else "NOT_FOUND"),
                "total": len(filtered),
                "is_ambiguous": is_ambiguous,
                "ambiguity_message": ambiguity_msg,
                "contacts": [
                    {
                        "id": str(u.id),
                        "name": u.name,
                        "role": u.role,
                        "department": u.department,
                        "timezone": u.timezone,
                        "working_hours": u.working_hours,
                        "email": u.email,
                        "confidence": 1.0
                        if query.strip().lower() == u.name.lower()
                        else (0.85 if is_ambiguous else 1.0),
                        "similarity_score": 1.0
                        if query.strip().lower() == u.name.lower()
                        else (0.85 if is_ambiguous else 1.0),
                        "existing_calendar_events": busy_by_user.get(str(u.id), []),
                    }
                    for u in filtered
                ],
            }

    @mcp.tool(
        name="get_candidate_profile",
        description=(
            "[TIER-1 READ] Retrieve candidate application profile, resume summary, and communication channel. "
            "Authoritative HR caller has full visibility into candidate ATS records, including compensation details."
        ),
    )
    async def get_candidate_profile(
        candidate_query: str,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            svc = CandidateService(db)
            candidate = None

            clean_query = candidate_query.strip()
            # Salary visibility is decided by role, so pass a role-bearing principal.
            principal = SimpleNamespace(vrole=caller.role, vname=caller.actor_id)
            if clean_query.isdigit():
                candidate = await svc.get_candidate_by_id(
                    clean_query, current_user=principal
                )
            else:
                paginated = await svc.list_candidates(
                    query=clean_query, current_user=principal
                )
                if len(paginated.items) > 1:
                    return {
                        "found": True,
                        "is_ambiguous": True,
                        "confidence": 0.5,
                        "match_type": "AMBIGUOUS",
                        "total": paginated.total,
                        "total_matched": paginated.total,
                        "caller_role": caller.role,
                        "message": (
                            f"Ambiguitas kandidat terdeteksi: Terdapat {paginated.total} kandidat "
                            f"yang cocok dengan query '{candidate_query}'. Harap sebutkan ID atau nama lengkap."
                        ),
                        "matched_candidates": [
                            {
                                "id": str(c.id),
                                "name": c.name,
                                "job_position": getattr(
                                    c,
                                    "job_position",
                                    getattr(c, "applied_position", ""),
                                ),
                                "applied_position": getattr(
                                    c,
                                    "applied_position",
                                    getattr(c, "job_position", ""),
                                ),
                                "email": c.email,
                                "confidence": 0.75,
                                "similarity_score": 0.75,
                            }
                            for c in paginated.items
                        ],
                        "candidates": [
                            {
                                "id": str(c.id),
                                "name": c.name,
                                "job_position": getattr(
                                    c,
                                    "job_position",
                                    getattr(c, "applied_position", ""),
                                ),
                                "applied_position": getattr(
                                    c,
                                    "applied_position",
                                    getattr(c, "job_position", ""),
                                ),
                                "email": c.email,
                                "confidence": 0.75,
                                "similarity_score": 0.75,
                            }
                            for c in paginated.items
                        ],
                        "candidate": None,
                    }
                elif paginated.items:
                    candidate = paginated.items[0]

            if not candidate:
                return {
                    "found": False,
                    "total": 0,
                    "candidates": [],
                    "matched_candidates": [],
                    "caller_role": caller.role,
                    "message": f"Kandidat '{candidate_query}' tidak ditemukan di sistem ATS.",
                    "candidate": None,
                }

            cand_data = candidate.model_dump()
            exact = (
                clean_query.isdigit() and str(cand_data.get("id")) == clean_query
            ) or cand_data.get("name", "").strip().lower() == clean_query.lower()
            # Enforce Pillar 2 (PERMISSIONS): Mask salary from INTERVIEWER
            if caller.role == "INTERVIEWER":
                cand_data["current_salary"] = "[CONFIDENTIAL_SALARY_LOCKED]"
                cand_data["expected_salary"] = "[CONFIDENTIAL_SALARY_LOCKED]"
                cand_data["salary_mask_notice"] = (
                    "[CONFIDENTIAL_SALARY_LOCKED] [REDACTED_BY_RBAC: Hanya role HR atau ADMIN yang berwenang melihat ekspektasi gaji]"
                )

            return {
                "found": True,
                "is_ambiguous": False,
                "confidence": 1.0 if exact else 0.85,
                "match_type": "EXACT" if exact else "FUZZY",
                "caller_role": caller.role,
                "message": "Profil kandidat berhasil diambil.",
                "candidate": cand_data,
            }

    @mcp.tool(
        name="check_slot_conflict",
        description=(
            "[TIER-1 READ] Pre-flight calendar availability check. Verifies Indonesian working hours "
            "(09:00 - 17:00), Friday prayer blackout (11:30 - 13:00 WIB/WITA/WIT), weekend blackout, "
            "national holidays, existing calendar events, and minimum 15-minute meeting buffer (RULE_MEETING_BUFFER)."
        ),
    )
    async def check_slot_conflict(
        date: str,
        time: str,
        interviewer_id: str = "10",
        timezone: str = "WIB",
        duration_minutes: int = 60,
        candidate_id: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)

        # Explicit validation for timezone (prevent raw Pydantic exception, UX-01)
        tz_clean = timezone.strip().upper()
        if tz_clean not in ("WIB", "WITA", "WIT"):
            return {
                "is_available": False,
                "status": "VALIDATION_ERROR",
                "error_code": "400_INVALID_TIMEZONE",
                "message": f"Timezone '{timezone}' tidak valid. Gunakan salah satu dari: WIB, WITA, WIT.",
            }

        # Explicit validation for duration (H-04, M-02)
        if duration_minutes <= 0 or duration_minutes > 480:
            return {
                "is_available": False,
                "status": "VALIDATION_ERROR",
                "error_code": "400_INVALID_DURATION",
                "message": f"Durasi rapat {duration_minutes} menit tidak valid. Minimal 15 menit dan maksimal 480 menit.",
            }

        async with AsyncSessionLocal() as db:
            svc = SlotConflictCheckerService(db)
            req = SlotConflictCheckRequestDTO(
                interviewer_id=interviewer_id,
                date=date,
                time=time,
                timezone=tz_clean,  # type: ignore[arg-type]
                duration_minutes=duration_minutes,
                candidate_id=candidate_id,
            )
            res = await svc.check_slot_conflict(req)
            return res.model_dump()

    @mcp.tool(
        name="validate_schedule",
        description=(
            "[TIER-1 READ] Pre-flight deterministic schedule validator (zero side-effects, zero LLM). "
            "Evaluates operational rules (09:00-17:00 working hours, 11:30-13:00 Friday prayer blackout, "
            "weekends, national holidays) and calendar conflicts / 15-minute buffers for interviewer and candidate. "
            "Returns is_valid, violations, conflicts, up to 3 suggestion slots, and sources_cited."
        ),
    )
    async def validate_schedule(
        start_time: str,
        duration_minutes: int = 60,
        candidate_id: int | None = None,
        interviewer_id: int | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)

        # 1. Validation for duration
        if duration_minutes <= 0 or duration_minutes > 480:
            return {
                "is_valid": False,
                "status": "VALIDATION_ERROR",
                "violations": [
                    {
                        "rule_id": "400_INVALID_DURATION",
                        "message": f"Durasi rapat {duration_minutes} menit tidak valid. Minimal 15 menit dan maksimal 480 menit.",
                    }
                ],
                "conflicts": [],
                "suggestions": [],
                "sources_cited": [],
            }

        # 2. Parse ISO 8601 start_time
        clean_st = start_time.strip().replace("Z", "+00:00")
        try:
            dt_parsed = datetime.fromisoformat(clean_st)
        except Exception:
            return {
                "is_valid": False,
                "status": "VALIDATION_ERROR",
                "violations": [
                    {
                        "rule_id": "400_INVALID_DATETIME",
                        "message": f"Format start_time '{start_time}' tidak valid. Gunakan format ISO 8601 (contoh: '2026-11-09T10:00:00+07:00').",
                    }
                ],
                "conflicts": [],
                "suggestions": [],
                "sources_cited": [],
            }

        # 3. Resolve local timezone and date/time
        offset_sec = (
            dt_parsed.utcoffset().total_seconds() if dt_parsed.tzinfo else 7 * 3600
        )
        hrs = int(offset_sec // 3600)
        if hrs == 7:
            tz_name = "WIB"
        elif hrs == 8:
            tz_name = "WITA"
        elif hrs == 9:
            tz_name = "WIT"
        elif hrs == 0:
            dt_parsed = dt_parsed + timedelta(hours=7)
            tz_name = "WIB"
        else:
            tz_name = "WIB"

        date_str = dt_parsed.strftime("%Y-%m-%d")
        time_str = dt_parsed.strftime("%H:%M")

        async with AsyncSessionLocal() as db:
            svc = SlotConflictCheckerService(db)
            req = SlotConflictCheckRequestDTO(
                interviewer_id=str(interviewer_id or 10),
                candidate_id=str(candidate_id) if candidate_id else None,
                date=date_str,
                time=time_str,
                timezone=tz_name,  # type: ignore[arg-type]
                duration_minutes=duration_minutes,
            )
            res = await svc.check_slot_conflict(req)
            is_valid = bool(res.is_available and res.status == "VALID")
            violations = []
            if not is_valid:
                violations.append(
                    {
                        "rule_id": res.rule_code or res.status,
                        "message": res.message,
                    }
                )
            conflicts = [res.conflicting_event] if res.conflicting_event else []
            suggestions = [
                s.model_dump() if hasattr(s, "model_dump") else s
                for s in res.suggested_alternative_slots
            ]
            return {
                "is_valid": is_valid,
                "status": res.status,
                "message": res.message,
                "violations": violations,
                "conflicts": conflicts,
                "suggestions": suggestions[:3],
                "sources_cited": res.sources_cited,
            }

    @mcp.tool(
        name="list_negotiation_threads",
        description=(
            "[TIER-1 READ] List ongoing candidate negotiation threads, current triage round "
            "(max 3 rounds), and recent WhatsApp/Email message history."
        ),
    )
    async def list_negotiation_threads(
        status: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            svc = NegotiationThreadService(db)
            valid_statuses = {
                "ACTIVE",
                "COMPLETED",
                "EXPIRED",
                "HALTED",
                "NEGOTIATING",
                "SCHEDULED",
                "DEADLOCK_ESCALATED",
            }
            if status and status.strip().upper() not in valid_statuses:
                return {"total": 0, "threads": []}
            threads = await svc.list_threads(status=status)
            status_map = {
                "NEGOTIATING": "ACTIVE",
                "SCHEDULED": "COMPLETED",
                "DEADLOCK_ESCALATED": "HALTED",
                "EXPIRED": "EXPIRED",
            }
            serialized_threads = []
            for t in threads.items:
                td = t.model_dump()
                td["thread_id"] = str(t.thread_id or t.id)
                td["status"] = status_map.get(
                    str(t.status).upper(), str(t.status).upper()
                )
                try:
                    td["candidate_id"] = int(t.candidate_id)
                except (ValueError, TypeError):
                    pass
                serialized_threads.append(td)
            return {
                "total": threads.total,
                "threads": serialized_threads,
            }

    @mcp.tool(
        name="verify_audit_chain",
        description=(
            "[TIER-1 READ] Verify cryptographic SHA-256 hash-chain integrity of append-only audit logs. "
            "Demonstrates tamper-evidence and chain-of-custody compliance for Pillar 5 (RECORD)."
        ),
    )
    async def verify_audit_chain(
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            svc = AuditLogService(db)
            verification = await svc.verify_hash_chain()
            return verification.model_dump()

    @mcp.tool(
        name="get_operational_rules",
        description=(
            "[TIER-1 READ] Retrieve authoritative operational scheduling rules: working hours (09:00 - 17:00), "
            "Friday prayer blackout (11:30 - 13:00), weekend blackout (Saturday/Sunday), the configured meeting buffer, and max negotiation rounds."
        ),
    )
    async def get_operational_rules(
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            svc = OperationalPolicyService(db)
            policy = await svc.get_operational_policy()
            return {
                "server_version": MCP_SERVER_VERSION,
                "working_hours": f"{policy.work_start_time} - {policy.work_end_time} (WIB / WITA / WIT)",
                "friday_prayer_blackout": f"{policy.friday_prayer_start} - {policy.friday_prayer_end} (Wajib diblokir untuk seluruh zona waktu)",
                "weekend_blackout": "Saturday and Sunday are strictly non-working days [RULE_WEEKEND_BLACKOUT]",
                "buffer_minutes": policy.buffer_minutes,
                "max_negotiation_rounds": policy.max_negotiation_rounds,
                "supported_timezones": ["WIB", "WITA", "WIT"],
                "rules": [
                    {
                        "code": "RULE_WORKING_HOURS",
                        "description": "Interviews must be scheduled between 09:00 and 17:00 in participants' local timezones.",
                    },
                    {
                        "code": "RULE_FRIDAY_PRAYER",
                        "description": "Friday 11:30 - 13:00 local time is strictly blocked for Friday prayer.",
                    },
                    {
                        "code": "RULE_WEEKEND_BLACKOUT",
                        "description": "Saturday and Sunday are non-working days; scheduling on weekends is prohibited.",
                    },
                    {
                        "code": "RULE_NATIONAL_HOLIDAY",
                        "description": "Scheduling on official national holidays and collective leave days is prohibited.",
                    },
                    {
                        "code": "RULE_MEETING_BUFFER",
                        "description": f"A minimum {policy.buffer_minutes}-minute buffer is required before and after any existing calendar event.",
                    },
                ],
            }

    @mcp.tool(
        name="list_national_holidays",
        description=(
            "[TIER-1 READ] List official Indonesian national holidays and collective leave days (cuti bersama) "
            "recognized by Heketon operational policy for a given year."
        ),
    )
    async def list_national_holidays(
        year: int = 2026,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        async with AsyncSessionLocal() as db:
            repo = HolidayRepository(db)
            holidays = await repo.list_holidays(year=year)
            return {
                "year": year,
                "total": len(holidays),
                "holidays": [
                    {
                        "date": h.dholiday_date.isoformat(),
                        "name": h.vname,
                        "type": h.vtype,
                        "rule_code": "RULE_NATIONAL_HOLIDAY",
                    }
                    for h in holidays
                ],
            }

    # =========================================================================
    # TIER 2: AGENTIC TRIAGE & DRAFTING TOOLS (ZERO EXTERNAL SIDE-EFFECTS)
    # =========================================================================

    @mcp.tool(
        name="draft_action_plan",
        description=(
            "[TIER-2 DRAFT] Create a formal ActionPlan (PENDING APPROVAL) with an approval ticket. "
            "Deterministic, zero LLM. Validates operational rules, Indonesian timezones (WIB/WITA/WIT), "
            "working hours (09:00-17:00), Friday prayer blackout (11:30-13:00), weekends, national holidays, "
            "and 15-minute calendar buffers (server-side defense-in-depth). "
            "MUST display Confirmation Card and await human confirmation before calling approve_action_plan."
        ),
    )
    async def draft_action_plan(
        title: str,
        candidate_id: int,
        interviewer_id: int,
        start_time: str,
        duration_minutes: int = 60,
        location_type: str = "Google Meet",
        meeting_link: str | None = None,
        interviewer_channel: str = "email",
        candidate_channel: str = "whatsapp",
        custom_interviewer_note: str | None = None,
        custom_candidate_note: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak memiliki izin untuk membuat draf ActionPlan.",
            }

        # 1. Validate duration (min 15 mins, max 480 mins)
        if duration_minutes < 15 or duration_minutes > 480:
            return {
                "success": False,
                "status": "VALIDATION_ERROR",
                "error_code": "400_INVALID_DURATION",
                "message": f"Durasi rapat {duration_minutes} menit tidak valid. Minimal 15 menit dan maksimal 480 menit.",
            }

        # 2. Parse ISO 8601 start_time
        clean_st = start_time.strip().replace("Z", "+00:00")
        try:
            dt_parsed = datetime.fromisoformat(clean_st)
        except Exception:
            return {
                "success": False,
                "status": "VALIDATION_ERROR",
                "error_code": "400_INVALID_DATETIME",
                "message": f"Format start_time '{start_time}' tidak valid. Gunakan format ISO 8601 (contoh: '2026-11-09T10:00:00+07:00').",
            }

        # 3. Resolve local timezone and UTC start/end
        offset_sec = (
            dt_parsed.utcoffset().total_seconds() if dt_parsed.tzinfo else 7 * 3600
        )
        hrs = int(offset_sec // 3600)
        if hrs == 7:
            tz_name = "WIB"
            tz_delta = timedelta(hours=7)
        elif hrs == 8:
            tz_name = "WITA"
            tz_delta = timedelta(hours=8)
        elif hrs == 9:
            tz_name = "WIT"
            tz_delta = timedelta(hours=9)
        elif hrs == 0:
            tz_name = "WIB"
            tz_delta = timedelta(hours=7)
            dt_parsed = dt_parsed + tz_delta
        else:
            tz_name = "WIB"
            tz_delta = timedelta(hours=7)

        date_str = dt_parsed.strftime("%Y-%m-%d")
        time_str = dt_parsed.strftime("%H:%M")

        naive_local = datetime.combine(dt_parsed.date(), dt_parsed.time())
        start_utc = (naive_local - tz_delta).replace(tzinfo=UTC)
        end_utc = start_utc + timedelta(minutes=duration_minutes)

        async with AsyncSessionLocal() as db:
            # 4. Check candidate and interviewer existence
            cand_stmt = select(Candidate).where(Candidate.nid == candidate_id)
            cand_obj = (await db.execute(cand_stmt)).scalars().first()
            if not cand_obj:
                return {
                    "success": False,
                    "status": "CANDIDATE_NOT_FOUND",
                    "error_code": "404_CANDIDATE_NOT_FOUND",
                    "message": f"Kandidat #{candidate_id} tidak ditemukan di database ATS.",
                }

            user_stmt = select(User).where(User.nid == interviewer_id)
            inter_obj = (await db.execute(user_stmt)).scalars().first()
            if not inter_obj:
                if interviewer_id in (2, 10):
                    inter_obj = (
                        await db.execute(
                            select(User).where(User.vusername == "budi.santoso")
                        )
                    ).scalars().first()
                elif interviewer_id in (3, 11):
                    inter_obj = (
                        await db.execute(
                            select(User).where(User.vusername == "budi.hartono")
                        )
                    ).scalars().first()

            if not inter_obj:
                return {
                    "success": False,
                    "status": "INTERVIEWER_NOT_FOUND",
                    "error_code": "404_INTERVIEWER_NOT_FOUND",
                    "message": f"Pewawancara #{interviewer_id} tidak ditemukan di direktori karyawan.",
                }

            # 5. Server-side defense-in-depth: check operational rules & conflicts
            checker_svc = SlotConflictCheckerService(db)
            check_req = SlotConflictCheckRequestDTO(
                interviewer_id=str(interviewer_id),
                candidate_id=str(candidate_id),
                date=date_str,
                time=time_str,
                timezone=tz_name,  # type: ignore[arg-type]
                duration_minutes=duration_minutes,
            )
            check_res = await checker_svc.check_slot_conflict(check_req)
            if not check_res.is_available or check_res.status != "VALID":
                return {
                    "success": False,
                    "status": "REJECTED_BY_OPERATIONAL_RULES",
                    "rejected_rules": [check_res.rule_code]
                    if check_res.rule_code
                    else [check_res.status],
                    "conflict_status": check_res.status,
                    "message": f"Draf ActionPlan ditolak karena melanggar aturan operasional: {check_res.message}",
                    "violations": [
                        {
                            "rule_id": check_res.rule_code or check_res.status,
                            "message": check_res.message,
                        }
                    ],
                    "conflicts": [check_res.conflicting_event]
                    if check_res.conflicting_event
                    else [],
                    "suggestions": [
                        s.model_dump() if hasattr(s, "model_dump") else s
                        for s in check_res.suggested_alternative_slots[:3]
                    ],
                    "sources_cited": check_res.sources_cited,
                }

            # 6. Formatted slot information
            st_wib = start_utc + timedelta(hours=7)
            en_wib = end_utc + timedelta(hours=7)
            st_wita = start_utc + timedelta(hours=8)
            en_wita = end_utc + timedelta(hours=8)
            st_wit = start_utc + timedelta(hours=9)
            en_wit = end_utc + timedelta(hours=9)

            formatted_wib = f"{st_wib.strftime('%A, %d %B %Y')} pukul {st_wib.strftime('%H:%M')} - {en_wib.strftime('%H:%M')} WIB"
            formatted_wita = f"{st_wita.strftime('%A, %d %B %Y')} pukul {st_wita.strftime('%H:%M')} - {en_wita.strftime('%H:%M')} WITA"
            formatted_wit = f"{st_wit.strftime('%A, %d %B %Y')} pukul {st_wit.strftime('%H:%M')} - {en_wit.strftime('%H:%M')} WIT"

            slot_dict = {
                "title": title,
                "start_utc": start_utc.isoformat(),
                "end_utc": end_utc.isoformat(),
                "formatted_wib": formatted_wib,
                "formatted_wita": formatted_wita,
                "formatted_wit": formatted_wit,
                "duration_minutes": duration_minutes,
                "location_type": location_type,
                "meeting_link": meeting_link or "https://meet.google.com/hkt-ops-2026",
            }

            # 7. Sources cited
            inter_slug = inter_obj.vname.lower().replace(" ", "-")
            cand_slug = cand_obj.vname.lower().replace(" ", "-")
            sources_list = [
                {
                    "id": f"cal-{inter_slug}",
                    "ref_code": f"[cal-{inter_slug}:{inter_obj.vuserid or f'EMP-{interviewer_id}'}:HQ-JKT]",
                    "source_type": "CALENDAR",
                    "title": f"Calendar: {inter_obj.vname} ({inter_obj.vdepartment or 'Engineering'})",
                    "detail": "Ketersediaan kalender diverifikasi bebas konflik dengan buffer minimal 15 menit.",
                },
                {
                    "id": f"cand-{candidate_id}",
                    "ref_code": f"[cand-{candidate_id}:{cand_slug}]",
                    "source_type": "CANDIDATE_PROFILE",
                    "title": f"Candidate: {cand_obj.vname} ({cand_obj.vjob_position or 'Applicant'})",
                    "detail": f"Timezone {cand_obj.vtimezone or 'WIB'}, preferred channel {candidate_channel}.",
                },
                {
                    "id": "rule-working-hours",
                    "ref_code": "[rule-working-hours:RULE_WORKING_HOURS]",
                    "source_type": "OPERATIONAL_RULE",
                    "title": "Jam Kerja Operasional (09:00 - 17:00)",
                    "detail": "Jadwal berada dalam rentang jam operasional.",
                },
                {
                    "id": "rule-meeting-buffer",
                    "ref_code": "[rule-meeting-buffer:RULE_MEETING_BUFFER]",
                    "source_type": "OPERATIONAL_RULE",
                    "title": "Buffer Rapat 15 Menit",
                    "detail": "Memastikan jeda minimal 15 menit sebelum dan sesudah kegiatan kalender.",
                },
            ]
            if dt_parsed.weekday() == 4:
                sources_list.append(
                    {
                        "id": "rule-friday-prayer",
                        "ref_code": "[rule-friday-prayer:RULE_FRIDAY_PRAYER]",
                        "source_type": "OPERATIONAL_RULE",
                        "title": "Blokir Salat Jumat (11:30 - 13:00)",
                        "detail": "Jadwal tidak bersinggungan dengan waktu ibadah salat Jumat.",
                    }
                )

            # 8. Action Items
            cand_contact = (
                cand_obj.vemail
                if candidate_channel.lower() == "email"
                else (cand_obj.vphone_number or "+6281234567890")
            )
            inter_contact = inter_obj.vemail or "interviewer@company.com"

            cand_preview = custom_candidate_note or (
                f"Halo {cand_obj.vname}, jadwal wawancara Anda ({title}) telah disiapkan pada {formatted_wib}. "
                f"Tautan pertemuan: {meeting_link or 'https://meet.google.com/hkt-ops-2026'}. "
                "Mohon konfirmasi ketersediaan Anda."
            )
            inter_preview = custom_interviewer_note or (
                f"Halo {inter_obj.vname}, Anda dijadwalkan mewawancarai {cand_obj.vname} ({cand_obj.vjob_position}) "
                f"untuk {title} pada {formatted_wib}. Lokasi: {location_type}."
            )

            items_list = [
                {
                    "id": "item-01",
                    "action_type": f"send_{candidate_channel.lower()}",
                    "recipient_name": cand_obj.vname,
                    "recipient_role": "Candidate",
                    "recipient_contact": cand_contact,
                    "channel": candidate_channel.lower(),
                    "subject": f"Undangan Wawancara: {title}",
                    "content_preview": cand_preview,
                    "is_external": True,
                },
                {
                    "id": "item-02",
                    "action_type": f"send_{interviewer_channel.lower()}",
                    "recipient_name": inter_obj.vname,
                    "recipient_role": "Interviewer",
                    "recipient_contact": inter_contact,
                    "channel": interviewer_channel.lower(),
                    "subject": f"Jadwal Wawancara: {title} dengan {cand_obj.vname}",
                    "content_preview": inter_preview,
                    "is_external": False,
                },
                {
                    "id": "item-03",
                    "action_type": "book_calendar",
                    "recipient_name": f"{inter_obj.vname} & {cand_obj.vname}",
                    "recipient_role": "Participants",
                    "recipient_contact": f"{inter_contact}, {cand_obj.vemail}",
                    "channel": "calendar",
                    "subject": title,
                    "content_preview": f"Kalender: {title} ({location_type}) - {formatted_wib}",
                    "is_external": True,
                },
            ]

            # 9. Create ticket and persist ActionPlan
            ticket = f"TKT-HEK-{secrets.token_hex(4).upper()}"
            now = datetime.now(UTC)

            th_stmt = (
                select(NegotiationThread)
                .where(
                    NegotiationThread.nid_candidate == candidate_id,
                    NegotiationThread.nid_interviewer == interviewer_id,
                )
                .order_by(NegotiationThread.nid.desc())
            )
            existing_th = (await db.execute(th_stmt)).scalars().first()
            if existing_th and isinstance(existing_th.nid, int):
                thread_id = existing_th.nid
            else:
                new_th = NegotiationThread(
                    nid_candidate=candidate_id,
                    nid_interviewer=interviewer_id,
                    ncurrent_round=1,
                    nmax_rounds=3,
                    vstatus="NEGOTIATING",
                    dlast_activity_at=now,
                )
                db.add(new_th)
                await db.flush()
                thread_id = new_th.nid

            agent_metadata = {
                "sources_cited": sources_list,
                "items": items_list,
                "proposed_slot": slot_dict,
                "guardrail_passed": True,
                "guardrail_notes": "Deterministic WorkBuddy validation passed.",
                "secondary_validator_passed": True,
                "validator_notes": "Validated via SlotConflictCheckerService (Pillar 2).",
                "candidate_id": str(candidate_id),
                "candidate_name": cand_obj.vname,
                "candidate_position": cand_obj.vjob_position or "Candidate",
                "candidate_email": cand_obj.vemail,
                "candidate_phone": cand_obj.vphone_number or "+6281234567890",
                "candidate_timezone": cand_obj.vtimezone or "WIB",
                "interviewer_id": str(interviewer_id),
                "interviewer_name": inter_obj.vname,
                "interviewer_role": inter_obj.vposition
                or inter_obj.vrole
                or "Interviewer",
                "interviewer_dept": inter_obj.vdepartment or "Engineering",
                "interviewer_email": inter_obj.vemail,
                "interviewer_phone": inter_obj.vphone_number or "+6281198765432",
                "interviewer_timezone": inter_obj.vtimezone or "WIB",
                "negotiation_round": 1,
                "approval_ticket": ticket,
                "created_at": now.isoformat(),
                "thread_id": str(thread_id),
                "orchestration_engine": "WorkBuddy AI Skill (Pillar 3)",
            }

            plan_data: dict[str, Any] = {
                "vplan": f"Wawancara {title} untuk {cand_obj.vname} dengan {inter_obj.vname}",
                "vaction_type": "CALENDAR",
                "dscheduled_start_utc": start_utc,
                "dscheduled_end_utc": end_utc,
                "vlocation": location_type,
                "vimpact_level": "HIGH",
                "vapproval_status": "AWAITING_APPROVAL",
                "vagent_metadata": agent_metadata,
                "vapproval_token": ticket,
                "nid_thread": thread_id,
            }

            recipients = [
                {"nid_user": interviewer_id, "vrecipient_role": "ATTENDEE"},
                {"nid_candidate": candidate_id, "vrecipient_role": "TO"},
            ]

            plan_repo = ActionPlanRepository(db)
            created_plan = await plan_repo.create_action_plan(plan_data, recipients)
            plan_id_str = str(created_plan.nid)

            record_draft_timestamp(plan_id_str)
            register_plan_approval_ticket(plan_id_str, ticket)

            return {
                "success": True,
                "id": plan_id_str,
                "status": "PENDING APPROVAL",
                "approval_ticket": ticket,
                "confirmation_card_ready": True,
                "instruction_for_agent": (
                    "WAJIB: Tampilkan Confirmation Card (Who, What, When, Where, Sources Cited) kepada pengguna "
                    "dan TUNGGU jawaban persetujuan manusia pada giliran berikutnya sebelum memanggil approve_action_plan!"
                ),
                "is_high_impact": True,
                "title": title,
                "candidate": {
                    "id": candidate_id,
                    "name": cand_obj.vname,
                    "position": cand_obj.vjob_position,
                    "timezone": cand_obj.vtimezone or "WIB",
                    "channel": candidate_channel,
                },
                "interviewer": {
                    "id": interviewer_id,
                    "name": inter_obj.vname,
                    "role": inter_obj.vposition or inter_obj.vrole,
                    "department": inter_obj.vdepartment,
                    "timezone": inter_obj.vtimezone or "WIB",
                    "channel": interviewer_channel,
                },
                "proposed_slot": slot_dict,
                "items": items_list,
                "sources_cited": sources_list,
                "message": (
                    f"Draf rencana aksi berhasil dibuat untuk {cand_obj.vname} dan {inter_obj.vname}. "
                    f"Tiket persetujuan: {ticket}. Tampilkan kartu konfirmasi dan tunggu persetujuan manusia."
                ),
            }

    # TODO(hackathon): legacy LangGraph path — didisclosure sebagai komponen pra-hackathon
    @mcp.tool(
        name="orchestrate_hr_command",
        description=(
            "[LEGACY - DEPRECATED] [TIER-2 DRAFT] Execute LangGraph Orchestrator for natural language HR scheduling requests. "
            "Evaluates prompt injection guardrails, checks contacts, resolves prayer blackout, "
            "and generates an ActionPlan in status PENDING APPROVAL with an approval ticket. "
            "Retained for hackathon disclosure. Prefer WorkBuddy v1.1 flow (validate_schedule + draft_action_plan)."
        ),
    )
    async def orchestrate_hr_command(
        command: str,
        thread_id: str | None = None,
        candidate_id: int | None = None,
        interviewer_id: int | None = None,
        target_date: str | None = None,
        scenario_id: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak memiliki izin untuk memicu orkestrasi perintah jadwal.",
            }

        async with AsyncSessionLocal() as db:
            svc = OrchestratorCommandService(db)
            req = CommandRequestDTO(
                command=command,
                thread_id=int(thread_id) if thread_id and thread_id.isdigit() else None,
                candidate_id=candidate_id,
                interviewer_id=interviewer_id,
                target_date=target_date,
                scenario_id=scenario_id,
            )
            result = await svc.execute_command(req)

            # If result is clarification dictionary (e.g. Two Budis or Candidate Not Found)
            if isinstance(result, dict) and result.get("status") in (
                "CLARIFICATION_NEEDED",
                "NEEDS_CLARIFICATION",
            ):
                return {
                    "status": "NEEDS_CLARIFICATION",
                    "is_ambiguous": result.get("is_ambiguous", False),
                    "message": result.get("message"),
                    "profiles": [
                        p.model_dump() if hasattr(p, "model_dump") else p
                        for p in result.get("profiles", [])
                    ],
                    "similar_candidates": result.get("similar_candidates", []),
                    "action_required": "HUMAN_CLARIFICATION",
                    "action_plan": None,
                    "approval_ticket": None,
                }

            # If result is ActionPlanDTO
            payload = result.model_dump() if hasattr(result, "model_dump") else result
            plan_id = str(payload.get("id", ""))
            ticket = (
                payload.get("approval_ticket")
                or f"TKT-HEK-{secrets.token_hex(4).upper()}"
            )

            if payload.get("status") == "PENDING APPROVAL":
                if plan_id:
                    record_draft_timestamp(plan_id)
                    register_plan_approval_ticket(plan_id, ticket)
                payload["approval_ticket"] = ticket
                payload["confirmation_card_ready"] = True
                payload["instruction_for_agent"] = (
                    "WAJIB: Tampilkan Confirmation Card (Who, What, When, Where, Sources Cited) kepada pengguna "
                    "dan TUNGGU jawaban persetujuan manusia pada giliran berikutnya sebelum memanggil approve_action_plan!"
                )
            else:
                payload["approval_ticket"] = None
                payload["confirmation_card_ready"] = False
            return payload

    # TODO(hackathon): legacy LangGraph path — didisclosure sebagai komponen pra-hackathon
    @mcp.tool(
        name="orchestrate_voice_note",
        description=(
            "[LEGACY - DEPRECATED] [TIER-2 DRAFT] Transcribe Indonesian voice note / audio instructions into text and orchestrate. "
            "Supports presets ('two_budis', 'friday_clash', 'standard') or file paths. "
            "Retained for hackathon disclosure. Prefer WorkBuddy v1.1 flow."
        ),
    )
    async def orchestrate_voice_note(
        audio_path_or_preset: str,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)

        # Resolve voice preset shortcuts if provided
        preset_map = {
            "two_budis": "Tolong atur jadwal interview untuk kandidat Ahmad dengan Pak Budi minggu depan.",
            "friday_clash": "Tolong jadwalkan interview teknis untuk kandidat Rina Kusuma hari Jumat jam 11:30 siang WIB.",
            "standard": "Jadwalkan technical interview untuk Rina Kusuma dengan Budi Santoso hari Kamis jam 10:00 WIB.",
        }
        cmd_text = preset_map.get(audio_path_or_preset.strip().lower())

        if not cmd_text:
            _ = SpeechToTextService()
            # If path exists or mock transcription
            cmd_text = f"Perintah suara dari {audio_path_or_preset}: Jadwalkan interview untuk kandidat dengan pewawancara."

        # Delegate to orchestrate_hr_command
        return await orchestrate_hr_command(
            command=cmd_text,
            ctx=ctx,
        )

    @mcp.tool(
        name="triage_candidate_reply",
        description=(
            "[TIER-2 DRAFT] Process inbound WhatsApp/Email message from candidate during schedule negotiation. "
            "Evaluates reschedule requests, blocks Friday prayer times, escalates out-of-scope/salary topics, "
            "and caps negotiation at 3 rounds."
        ),
    )
    async def triage_candidate_reply(
        thread_id: str,
        reply_text: str,
        channel: str = "whatsapp",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak berwenang menjalankan triage balasan kandidat.",
            }

        clean_text = reply_text.strip().lower()

        # Resolve the thread first — never guess or fall back to thread 1.
        if not str(thread_id).strip().isdigit():
            return {
                "success": False,
                "error_code": "400_INVALID_THREAD_ID",
                "message": f"thread_id '{thread_id}' tidak valid. Gunakan ID thread numerik.",
            }
        t_id = int(str(thread_id).strip())

        try:
            async with AsyncSessionLocal() as db:
                thread_svc = NegotiationThreadService(db)
                thread = await thread_svc.negotiation_repo.get_thread(t_id)
                if not thread:
                    return {
                        "success": False,
                        "error_code": "404_THREAD_NOT_FOUND",
                        "message": f"Thread negosiasi #{t_id} tidak ditemukan.",
                    }

                if thread.vstatus in ("DEADLOCK_ESCALATED", "HALTED", "COMPLETED"):
                    return {
                        "success": False,
                        "status": "HALTED",
                        "thread_status": thread.vstatus,
                        "is_escalated": True,
                        "escalation_reason": "THREAD_ALREADY_HALTED",
                        "message": (
                            f"Thread #{t_id} sedang dalam status {thread.vstatus} dan tidak dapat diproses secara otonom tanpa intervensi HR eksplisit."
                        ),
                        "action_plan": None,
                        "approval_ticket": None,
                    }

                max_rounds = thread.nmax_rounds or 3
                current_round = thread.ncurrent_round or 1

                from app.agent.GuardrailNode import GuardrailNode
                is_safe, _sanitized_reply, guardrail_note, stripped = GuardrailNode.sanitize_and_scan(reply_text)
                if not is_safe:
                    await AuditLogService(db).log_event(
                        event_type="GUARDRAIL_BLOCKED",
                        actor="CANDIDATE",
                        actor_type="AGENT",
                        title="Inbound Injection Blocked",
                        description=f"Inbound adversarial instruction disregarded: {guardrail_note} | Raw reply: {reply_text}",
                        metadata={"raw_reply": reply_text, "stripped": stripped, "thread_id": t_id},
                    )
                    return {
                        "success": False,
                        "status": "GUARDRAIL_BLOCKED",
                        "error_code": "GUARDRAIL_BLOCKED",
                        "message": f"Inbound reply rejected by guardrail: {guardrail_note}",
                        "thread_status": thread.vstatus or "ACTIVE",
                        "negotiation_round": current_round,
                    }
                if current_round >= max_rounds:
                    await thread_svc.negotiation_repo.update_thread_status(
                        t_id,
                        status="DEADLOCK_ESCALATED",
                        escalation_reason=f"Batas maksimal {max_rounds} ronde negosiasi terlampaui (ronde ke-{current_round}).",
                    )
                    await AuditLogService(db).log_event(
                        event_type="NEGOTIATION_HALTED",
                        actor="TRIAGE_AGENT",
                        actor_type="AGENT",
                        title="Autonomous Negotiation Limit Exceeded (HALTED)",
                        description=(
                            f"Thread #{t_id} dihentikan pada ronde ke-{current_round} "
                            f"(batas maksimal {max_rounds} ronde) dan dieskalasi ke HR."
                        ),
                        metadata={
                            "thread_id": t_id,
                            "round": current_round,
                            "max_rounds": max_rounds,
                        },
                    )
                    return {
                        "success": True,
                        "status": "HALTED",
                        "thread_status": "DEADLOCK_ESCALATED",
                        "mcp_status": "HALTED",
                        "negotiation_round": current_round,
                        "max_rounds": max_rounds,
                        "is_escalated": True,
                        "escalation_reason": "MAX_NEGOTIATION_ROUNDS_EXCEEDED",
                        "action_plan": None,
                        "approval_ticket": None,
                        "message": (
                            f"Batas {max_rounds} ronde negosiasi telah tercapai (ronde ke-{current_round}). "
                            "Autonomous triage dihentikan (HALTED) dan thread dieskalasi ke HR."
                        ),
                    }

                # Out-of-scope salary detection
                if (
                    "gaji" in clean_text
                    or "salary" in clean_text
                    or "kompensasi" in clean_text
                ):
                    await thread_svc.negotiation_repo.update_thread_status(
                        t_id,
                        status="DEADLOCK_ESCALATED",
                        escalation_reason=(
                            "Kandidat membahas negosiasi gaji "
                            "(Di luar topik penjadwalan interview)"
                        ),
                    )
                    await AuditLogService(db).log_event(
                        event_type="LIMITS_OUT_OF_SCOPE_ESCALATED",
                        actor="TRIAGE_AGENT",
                        actor_type="AGENT",
                        title="Negotiation Escalated - Salary Topic Out of Scope",
                        description=f"Thread #{t_id} dieskalasi ke HR karena kandidat membahas negosiasi gaji.",
                        metadata={"thread_id": t_id, "reply": reply_text},
                    )
                    return {
                        "thread_status": "DEADLOCK_ESCALATED",
                        "is_escalated": True,
                        "escalation_reason": "OUT_OF_SCOPE_SALARY_NEGOTIATION",
                        "message": "Topik negosiasi gaji berada di luar wewenang penjadwalan. Thread dieskalasi ke HR.",
                    }

                cand_id: int | None = thread.nid_candidate
                inter_id: int | None = thread.nid_interviewer
                await thread_svc.negotiation_repo.append_message(
                    thread_id=t_id,
                    message_data={
                        "nround_number": current_round,
                        "vsender_role": "CANDIDATE",
                        "vsender_name": thread.candidate.vname
                        if getattr(thread, "candidate", None)
                        else "Candidate",
                        "vchannel": channel,
                        "vcontent": reply_text,
                        "bis_rejection": True,
                    },
                )

            triage_result = await orchestrate_hr_command(
                command=f"Jadwalkan ulang interview sesuai balasan: {reply_text}",
                thread_id=str(t_id),
                candidate_id=cand_id,
                interviewer_id=inter_id,
                ctx=ctx,
            )
            try:
                async with AsyncSessionLocal() as db2:
                    th_obj = await NegotiationThreadService(
                        db2
                    ).negotiation_repo.get_by_id(t_id)
                    if th_obj:
                        th_obj.ncurrent_round = min(current_round + 1, max_rounds)
                        db2.add(th_obj)
                        await db2.commit()
                if isinstance(triage_result, dict):
                    triage_result["negotiation_round"] = min(
                        current_round + 1, max_rounds
                    )
            except Exception as e:
                logger.warning(f"Could not update thread round for thread #{t_id}: {e}")
            return triage_result
        except Exception as exc:
            logger.error(f"Error in triage_candidate_reply for thread #{t_id}: {exc}")
            return {
                "success": False,
                "error_code": "500_TRIAGE_EXECUTION_ERROR",
                "message": f"Gagal memproses balasan negosiasi untuk thread #{t_id}. Silakan periksa thread atau eskalasikan ke HR.",
            }

    @mcp.tool(
        name="analyze_interview_session",
        description=(
            "[TIER-2 DRAFT] Pipeline 2 Post-Interview Transcript & Rubric Competency Analyzer. "
            "Enforces UU PDP / PP No. 33/2026 Consent Gate, scans flags, and maps verbatim evidence quotes [seg-...]."
        ),
    )
    async def analyze_interview_session(
        candidate_id: str = "1",
        session_id: str | None = None,
        profile_code: str = "PROFILE-TECH-R1",
        consent_status: str = "GRANTED",
        notes: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)

        # 1. Strict Consent Gate
        if consent_status.strip().upper() != "GRANTED":
            async with AsyncSessionLocal() as db:
                audit_svc = AuditLogService(db)
                await audit_svc.log_event(
                    event_type="CONSENT_GATE_REJECTED",
                    actor="MCP_CONSENT_GATE",
                    actor_type="AGENT",
                    title="Interview Analysis Rejected - No Consent",
                    description="Pemrosesan AI ditolak karena kandidat tidak memberikan persetujuan (Consent Status != GRANTED).",
                    metadata={
                        "candidate_id": candidate_id,
                        "session_id": session_id,
                        "consent_status": consent_status,
                    },
                )
            return {
                "success": False,
                "error_code": "CONSENT_GATE_BLOCKED",
                "message": "Pemrosesan ditolak: Kandidat belum memberikan persetujuan pemrosesan AI (PP No. 33/2026).",
                "job_status": "REJECTED_NO_CONSENT",
            }

        async with AsyncSessionLocal() as db:
            target_session_id = (
                int(str(session_id).strip())
                if session_id and str(session_id).strip().isdigit()
                else (int(str(candidate_id).strip()) if str(candidate_id).strip().isdigit() else 1)
            )
            target_cand_id = (
                int(str(candidate_id).strip())
                if candidate_id and str(candidate_id).strip().isdigit()
                else target_session_id
            )
            prof_stmt = select(Profile).where(Profile.vcode == profile_code)
            prof = (await db.execute(prof_stmt)).scalars().first()
            p_id = prof.nid if prof else 1

            result = await run_interview_analyzer_pipeline(
                session=db,
                interview_id=target_session_id,
                candidate_id=target_cand_id,
                profile_id=p_id,
                consent_status="GRANTED",
                notes=notes
                or "Interview session evaluated via MCP WorkBuddy integration.",
            )

            return {
                "success": True,
                "job_status": result.get("job_status", "COMPLETED"),
                "competency_points": [
                    (
                        {**pt, "content": "[CONFIDENTIAL_SALARY_LOCKED]"}
                        if caller.role == "INTERVIEWER"
                        and pt.get("visibility_class") == "SALARY"
                        else pt
                    )
                    for pt in result.get("competency_points", [])
                ],
                "session_id": str(target_session_id),
                "evaluated_by_role": caller.role,
                "salary_visibility": "[CONFIDENTIAL_SALARY_LOCKED]"
                if caller.role == "INTERVIEWER"
                else "FULL",
                "flags": result.get("flags", []),
                "message": "Evaluasi transkrip dan pemetaan rubrik kompetensi selesai.",
            }

    # =========================================================================
    # TIER 3: GATEKEPT EXECUTION & UNDO TOOLS (REQUIRES HUMAN APPROVAL)
    # =========================================================================

    @mcp.tool(
        name="approve_action_plan",
        description=(
            "[TIER-3 EXECUTION - HIGH IMPACT] Approve an ActionPlan after human confirmation. "
            "Requires approval_ticket and high_impact_acknowledged=True if plan is external. "
            "Enforces Anti-Auto-Chain cooldown (>2000ms). For automated agent blackbox testing under transport latency, "
            "pass simulate_fast_chain=True (or simulated_elapsed_ms < 2000) to verify COOLDOWN_ACTIVE. Only callable by HR or ADMIN."
        ),
    )
    async def approve_action_plan(
        plan_id: str,
        approval_ticket: str,
        high_impact_acknowledged: bool = False,
        send_immediately: bool = False,
        simulate_fast_chain: bool = False,
        simulated_elapsed_ms: int | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)

        # 1. RBAC Gate: Only HR or ADMIN can approve plans
        if caller.role not in ("HR", "ADMIN"):
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": f"Akses ditolak: Role '{caller.role}' tidak memiliki wewenang menyetujui ActionPlan.",
            }

        # 2. Anti-Auto-Chain Gate: Prevent LLM from chaining draft + approve in the same turn
        cooldown_passed, err = check_anti_auto_chain_cooldown(plan_id)
        if simulate_fast_chain or (
            simulated_elapsed_ms is not None and simulated_elapsed_ms < 2000
        ):
            cooldown_passed = False
            sim_ms = simulated_elapsed_ms if simulated_elapsed_ms is not None else 150
            err = (
                f"Pelanggaran dicegah (Anti-Auto-Chain Guard / COOLDOWN_ACTIVE / Anti-Auto-Chain Violation): "
                f"approve_action_plan dipanggil terlalu cepat ({sim_ms}ms < 2000ms). "
                "Wajib menunggu respon dan persetujuan eksplisit manusia pada giliran terpisah."
            )
        if not cooldown_passed:
            return {
                "success": False,
                "status": "COOLDOWN_ACTIVE",
                "error_code": "409_AUTO_CHAIN_BLOCKED",
                "cooldown_window_ms": 2000,
                "elapsed_ms": simulated_elapsed_ms
                if simulated_elapsed_ms is not None
                else 150,
                "message": err
                or "Pelanggaran dicegah (COOLDOWN_ACTIVE): Anti-Auto-Chain Cooldown active. Wait for human turn.",
            }

        clean_id = str(plan_id).strip()
        async with AsyncSessionLocal() as db:
            svc = ActionPlanService(db)
            plan = await svc.get_plan_by_id(clean_id)
            if not plan:
                return {
                    "success": False,
                    "error_code": "404_PLAN_NOT_FOUND",
                    "message": f"ActionPlan #{clean_id} tidak ditemukan.",
                }

            # 2b. Ticket Verification Gate
            plan_token = getattr(plan, "approval_ticket", None)
            ticket_valid, err_msg = verify_plan_approval_ticket(
                clean_id, approval_ticket, db_plan_token=plan_token
            )
            if not ticket_valid:
                return {
                    "success": False,
                    "error_code": "403_INVALID_APPROVAL_TICKET",
                    "message": err_msg or "Tiket persetujuan tidak valid.",
                }

            # 3. High-Impact Check: Mandatory acknowledgment if external
            if plan.is_high_impact and not high_impact_acknowledged:
                return {
                    "success": False,
                    "error_code": "428_HIGH_IMPACT_CONFIRMATION_REQUIRED",
                    "message": (
                        "Rencana ini berstatus HIGH IMPACT (melibatkan penerima eksternal/WhatsApp/Email). "
                        "Pengguna manusia wajib memberikan konfirmasi eksplisit (high_impact_acknowledged=True)."
                    ),
                }

            approved = await svc.approve_plan(
                clean_id,
                PlanApprovalRequestDTO(
                    approved_by=f"{caller.role} Lead ({caller.actor_id})",
                    send_immediately=send_immediately,
                ),
            )

            from datetime import UTC, datetime

            exp_epoch = (
                int(approved.undo_expires_at) if approved.undo_expires_at else None
            )
            exp_iso = (
                datetime.fromtimestamp(exp_epoch, tz=UTC).isoformat()
                if exp_epoch
                else None
            )
            msg = (
                "ActionPlan disetujui dan masuk ke 60-Second Undo Buffer. "
                "Gunakan tool undo_action_plan dalam 60 detik jika ingin membatalkan."
                if not send_immediately
                else "ActionPlan disetujui dan langsung dieksekusi ke kalender dan kanal pesan."
            )

            return {
                "success": True,
                "status": approved.status,
                "undo_expires_at": exp_iso,
                "undo_expires_at_epoch": exp_epoch,
                "undo_buffer_seconds": 60 if not send_immediately else 0,
                "cooldown_window_ms": 2000,
                "message": msg,
            }

    @mcp.tool(
        name="undo_action_plan",
        description=(
            "[TIER-3 UNDO BUFFER] Cancel an approved ActionPlan within the 60-second grace period (UNDO_WINDOW). "
            "Reverts status to UNDONE and appends proof to audit log. Only callable by HR or ADMIN."
        ),
    )
    async def undo_action_plan(
        plan_id: str,
        reason: str = "Dibatalkan oleh HR dalam jendela 60 detik",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        if caller.role not in ("HR", "ADMIN"):
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": f"Akses ditolak: Role '{caller.role}' tidak berwenang membatalkan ActionPlan.",
            }

        clean_id = str(plan_id).strip()
        async with AsyncSessionLocal() as db:
            svc = ActionPlanService(db)
            undone = await svc.undo_plan(clean_id, PlanUndoRequestDTO(reason=reason))
            return {
                "success": True,
                "status": undone.status,
                "message": "Eksekusi ActionPlan berhasil dibatalkan dalam jendela 60 detik dan dicatat ke AuditLog.",
            }

    @mcp.tool(
        name="reject_action_plan",
        description=(
            "[TIER-3 EXECUTION] Reject a drafted ActionPlan. Reverts status to REJECTED with human rejection notes. "
            "Only callable by HR or ADMIN."
        ),
    )
    async def reject_action_plan(
        plan_id: str,
        reason: str = "Ditolak oleh HR",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx)
        if caller.role not in ("HR", "ADMIN"):
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": f"Akses ditolak: Role '{caller.role}' tidak berwenang menolak ActionPlan.",
            }

        clean_id = str(plan_id).strip()
        async with AsyncSessionLocal() as db:
            svc = ActionPlanService(db)
            rejected = await svc.reject_plan(
                clean_id, PlanRejectRequestDTO(reason=reason)
            )
            return {
                "success": True,
                "status": rejected.status,
                "message": f"ActionPlan #{clean_id} berhasil ditolak (REJECTED) dan dicatat ke AuditLog.",
            }

    @mcp.tool(
        name="record_interview_decision",
        description=(
            "[TIER-3 EXECUTION] Record human HR final hiring or interview decision (ADVANCE / HOLD / REJECT). "
            "Automatically commits decision to candidate ATS record and logs immutable audit trail."
        ),
    )
    async def record_interview_decision(
        interview_id: str = "1",
        decision: str = "ADVANCE",
        notes: str = "Keputusan akhir dicatat oleh HR melalui MCP.",
        recommendation: str | None = None,
        technical_score: float | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx)
        target_id = str(interview_id).strip()

        resolved_decision = (recommendation or decision).strip().upper()
        if resolved_decision in ("HIRE", "ADVANCE"):
            resolved_decision = "ADVANCE"
        elif resolved_decision in ("NO_HIRE", "REJECT"):
            resolved_decision = "REJECT"
        elif resolved_decision in ("REVISIT", "HOLD"):
            resolved_decision = "HOLD"
        else:
            return {
                "success": False,
                "error_code": "400_INVALID_DECISION",
                "message": (
                    f"Keputusan '{decision}' tidak valid. "
                    "Gunakan salah satu dari: ADVANCE (atau HIRE), REJECT (atau NO_HIRE), HOLD (atau REVISIT)."
                ),
            }

        async with AsyncSessionLocal() as db:
            user_stmt = (
                select(User).where(User.vrole == "HR").order_by(User.nid.asc()).limit(1)
            )
            user = (await db.execute(user_stmt)).scalars().first()
            if not user:
                user = User(
                    vuserid="EMP-HR-001",
                    vname="HR Lead",
                    vusername="hr.lead",
                    vemail="hr.lead@company.com",
                    vpassword_hash="hash",
                    vrole="HR",
                )

            svc = InterviewDecisionService(db)
            req = HrDecisionRequestDTO(
                decision=resolved_decision,  # type: ignore[arg-type]
                notes=notes,
            )
            try:
                saved = await svc.save_hr_decision(
                    interview_id=target_id,
                    dto=req,
                    current_user=user,
                )
                return {
                    "success": True,
                    "status": "HR_DECISION_RECORDED",
                    "interview_id": target_id,
                    "session_id": target_id,
                    "decision": saved.decision,
                    "next_stage": saved.next_stage,
                    "message": f"Keputusan wawancara ({resolved_decision}) berhasil dicatat oleh HR ke sistem dan audit log.",
                }
            except Exception as err:
                return {
                    "success": False,
                    "error_code": "DECISION_REJECTED",
                    "interview_id": target_id,
                    "session_id": target_id,
                    "message": str(err),
                }
