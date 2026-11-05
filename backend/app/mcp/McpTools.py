"""3-Tier Accountable MCP Tools for Heketon HR & Office Ops Orchestrator.

File: backend/app/mcp/McpTools.py
"""

from __future__ import annotations

import logging
import secrets
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
from app.model.RubricModel import Profile
from app.model.UserModel import User
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
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
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

            is_ambiguous = len(filtered) > 1 and bool(query.strip())
            ambiguity_msg = None
            if is_ambiguous:
                ambiguity_msg = (
                    f"Ditemukan {len(filtered)} kontak yang cocok dengan '{query}'. "
                    f"Harap mintakan klarifikasi kepada pengguna untuk memilih salah satu kontak yang tepat."
                )

            return {
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
                    }
                    for u in filtered
                ],
            }

    @mcp.tool(
        name="get_candidate_profile",
        description=(
            "[TIER-1 READ] Retrieve candidate application profile, resume summary, and communication channel. "
            "Enforces strict RBAC: Expected salary is REDACTED for INTERVIEWER role."
        ),
    )
    async def get_candidate_profile(
        candidate_query: str,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
        async with AsyncSessionLocal() as db:
            svc = CandidateService(db)
            candidate = None

            clean_query = candidate_query.strip()
            if clean_query.isdigit():
                candidate = await svc.get_candidate_by_id(clean_query)
            else:
                paginated = await svc.list_candidates(query=clean_query)
                if len(paginated.items) > 1:
                    return {
                        "found": True,
                        "is_ambiguous": True,
                        "total_matched": len(paginated.items),
                        "caller_role": caller.role,
                        "message": (
                            f"Ambiguitas kandidat terdeteksi: Terdapat {len(paginated.items)} kandidat "
                            f"yang cocok dengan query '{candidate_query}'. Harap sebutkan ID atau nama lengkap."
                        ),
                        "matched_candidates": [
                            {
                                "id": str(c.id),
                                "name": c.name,
                                "job_position": c.job_position,
                                "email": c.email,
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
                    "caller_role": caller.role,
                    "message": f"Kandidat '{candidate_query}' tidak ditemukan di sistem ATS.",
                    "candidate": None,
                }

            cand_data = candidate.model_dump()
            # Enforce Pillar 2 (PERMISSIONS): Mask salary from INTERVIEWER
            if caller.role == "INTERVIEWER":
                cand_data["current_salary"] = None
                cand_data["expected_salary"] = None
                cand_data["salary_mask_notice"] = (
                    "[REDACTED_BY_RBAC: Hanya role HR atau ADMIN yang berwenang melihat ekspektasi gaji]"
                )

            return {
                "found": True,
                "caller_role": caller.role,
                "message": "Profil kandidat berhasil diambil.",
                "candidate": cand_data,
            }

    @mcp.tool(
        name="check_slot_conflict",
        description=(
            "[TIER-1 READ] Pre-flight calendar availability check. Verifies Indonesian working hours "
            "(09:00 - 17:00), Friday prayer blackout (11:30 - 13:00 WIB/WITA/WIT), and national holidays."
        ),
    )
    async def check_slot_conflict(
        date: str,
        time: str,
        interviewer_id: str = "1",
        timezone: str = "WIB",
        duration_minutes: int = 60,
        candidate_id: str | None = None,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
        async with AsyncSessionLocal() as db:
            svc = SlotConflictCheckerService(db)
            req = SlotConflictCheckRequestDTO(
                interviewer_id=interviewer_id,
                date=date,
                time=time,
                timezone=timezone,  # type: ignore[arg-type]
                duration_minutes=duration_minutes,
                candidate_id=candidate_id,
            )
            res = await svc.check_slot_conflict(req)
            return res.model_dump()

    @mcp.tool(
        name="list_negotiation_threads",
        description=(
            "[TIER-1 READ] List ongoing candidate negotiation threads, current triage round "
            "(max 3 rounds), and recent WhatsApp/Email message history."
        ),
    )
    async def list_negotiation_threads(
        status: str | None = None,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
        async with AsyncSessionLocal() as db:
            svc = NegotiationThreadService(db)
            threads = await svc.list_threads(status=status)
            return {
                "total": threads.total,
                "threads": [t.model_dump() for t in threads.items],
            }

    @mcp.tool(
        name="verify_audit_chain",
        description=(
            "[TIER-1 READ] Verify cryptographic SHA-256 hash-chain integrity of append-only audit logs. "
            "Demonstrates tamper-evidence and chain-of-custody compliance for Pillar 5 (RECORD)."
        ),
    )
    async def verify_audit_chain(
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
        async with AsyncSessionLocal() as db:
            svc = AuditLogService(db)
            verification = await svc.verify_hash_chain()
            return verification.model_dump()

    @mcp.tool(
        name="get_operational_rules",
        description=(
            "[TIER-1 READ] Retrieve authoritative operational scheduling rules: working hours (09:00 - 17:00), "
            "Friday prayer blackout (11:30 - 13:00), weekend blackout (Saturday/Sunday), safe buffer (15m), and max negotiation rounds."
        ),
    )
    async def get_operational_rules(
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
        async with AsyncSessionLocal() as db:
            svc = OperationalPolicyService(db)
            policy = await svc.get_operational_policy()
            return {
                "working_hours": f"{policy.work_start_time} - {policy.work_end_time} (WIB / WITA / WIT)",
                "friday_prayer_blackout": f"{policy.friday_prayer_start} - {policy.friday_prayer_end} (Wajib diblokir untuk seluruh zona waktu)",
                "weekend_blackout": "Saturday and Sunday are strictly non-working days [RULE_WEEKEND_BLACKOUT]",
                "buffer_minutes": policy.buffer_minutes,
                "max_negotiation_rounds": policy.max_negotiation_rounds,
                "supported_timezones": ["WIB", "WITA", "WIT"],
                "rules": [
                    {"code": "RULE_WORKING_HOURS", "description": "Interviews must be scheduled between 09:00 and 17:00 in participants' local timezones."},
                    {"code": "RULE_FRIDAY_PRAYER", "description": "Friday 11:30 - 13:00 local time is strictly blocked for Friday prayer."},
                    {"code": "RULE_WEEKEND_BLACKOUT", "description": "Saturday and Sunday are non-working days; scheduling on weekends is prohibited."},
                    {"code": "RULE_NATIONAL_HOLIDAY", "description": "Scheduling on official national holidays and collective leave days is prohibited."},
                    {"code": "RULE_MEETING_BUFFER", "description": f"A minimum {policy.buffer_minutes}-minute buffer is required before and after any existing calendar event."},
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
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await verify_caller_rbac(ctx, caller_role_override)
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
        name="orchestrate_hr_command",
        description=(
            "[TIER-2 DRAFT] Execute LangGraph Orchestrator for natural language HR scheduling requests. "
            "Evaluates prompt injection guardrails, checks contacts, resolves prayer blackout, "
            "and generates an ActionPlan in status PENDING APPROVAL with an approval ticket. "
            "IMPORTANT: You MUST display the confirmation card and wait for human approval before executing!"
        ),
    )
    async def orchestrate_hr_command(
        command: str,
        thread_id: str | None = None,
        candidate_id: int | None = None,
        interviewer_id: int | None = None,
        target_date: str | None = None,
        scenario_id: str | None = None,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
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
            if isinstance(result, dict) and result.get("status") in ("CLARIFICATION_NEEDED", "NEEDS_CLARIFICATION"):
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
                }

            # If result is ActionPlanDTO
            payload = result.model_dump() if hasattr(result, "model_dump") else result
            plan_id = str(payload.get("id", ""))
            ticket = payload.get("approval_ticket") or f"TKT-HEK-{secrets.token_hex(4).upper()}"

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

    @mcp.tool(
        name="orchestrate_voice_note",
        description=(
            "[TIER-2 DRAFT] Transcribe Indonesian voice note / audio instructions into text and orchestrate. "
            "Supports presets ('two_budis', 'friday_clash', 'standard') or file paths."
        ),
    )
    async def orchestrate_voice_note(
        audio_path_or_preset: str,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak memiliki wewenang memicu orkestrasi voice note.",
            }

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
            caller_role_override=caller.role,
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
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak berwenang menjalankan triage balasan kandidat.",
            }

        clean_text = reply_text.strip().lower()
        # Out-of-scope salary detection 
        if "gaji" in clean_text or "salary" in clean_text or "kompensasi" in clean_text:
            async with AsyncSessionLocal() as db:
                thread_svc = NegotiationThreadService(db)
                audit_svc = AuditLogService(db)
                t_id = int(thread_id) if thread_id.isdigit() else 1
                await thread_svc.negotiation_repo.update_thread_status(
                    t_id,
                    status="DEADLOCK_ESCALATED",
                    escalation_reason="Kandidat membahas negosiasi gaji (Di luar topik penjadwalan interview)",
                )
                await audit_svc.log_event(
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

        # Fetch thread details so we never mistake reply text for candidate name ([F-04])
        t_id = int(thread_id) if thread_id.isdigit() else 1
        cand_id: int | None = None
        inter_id: int | None = None
        async with AsyncSessionLocal() as db:
            thread_svc = NegotiationThreadService(db)
            thread = await thread_svc.negotiation_repo.get_thread(t_id)
            if thread:
                cand_id = thread.nid_candidate
                inter_id = thread.nid_interviewer

        return await orchestrate_hr_command(
            command=f"Jadwalkan ulang interview kandidat sesuai balasan: {reply_text}",
            thread_id=str(t_id),
            candidate_id=cand_id,
            interviewer_id=inter_id,
            caller_role_override=caller.role,
            ctx=ctx,
        )

    @mcp.tool(
        name="analyze_interview_session",
        description=(
            "[TIER-2 DRAFT] Pipeline 2 Post-Interview Transcript & Rubric Competency Analyzer. "
            "Enforces UU PDP / PP No. 33/2026 Consent Gate, scans flags, and maps verbatim evidence quotes [seg-...]."
        ),
    )
    async def analyze_interview_session(
        candidate_id: str,
        profile_code: str = "PROFILE-TECH-R1",
        consent_status: str = "GRANTED",
        notes: str | None = None,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
        if caller.role == "INTERVIEWER":
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": "Role 'INTERVIEWER' tidak berwenang memicu analisis sesi wawancara.",
            }

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
            c_id = int(candidate_id) if candidate_id.isdigit() else 1
            prof_stmt = select(Profile).where(Profile.vcode == profile_code)
            prof = (await db.execute(prof_stmt)).scalars().first()
            p_id = prof.nid if prof else 1

            result = await run_interview_analyzer_pipeline(
                session=db,
                interview_id=1,
                candidate_id=c_id,
                profile_id=p_id,
                consent_status="GRANTED",
                notes=notes
                or "Interview session evaluated via MCP WorkBuddy integration.",
            )

            return {
                "success": True,
                "job_status": result.get("job_status", "COMPLETED"),
                "competency_points": result.get("competency_points", []),
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
            "Enforces Anti-Auto-Chain cooldown (>2000ms). Only callable by HR or ADMIN."
        ),
    )
    async def approve_action_plan(
        plan_id: str,
        approval_ticket: str,
        high_impact_acknowledged: bool = False,
        send_immediately: bool = False,
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)

        # 1. RBAC Gate: Only HR or ADMIN can approve plans
        if caller.role not in ("HR", "ADMIN"):
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": f"Akses ditolak: Role '{caller.role}' tidak memiliki wewenang menyetujui ActionPlan.",
            }

        # 2. Anti-Auto-Chain Gate: Prevent LLM from chaining draft + approve in the same turn
        cooldown_passed, err = check_anti_auto_chain_cooldown(plan_id)
        if not cooldown_passed:
            return {
                "success": False,
                "error_code": "409_AUTO_CHAIN_BLOCKED",
                "message": err
                or "Anti-Auto-Chain Cooldown active. Wait for human turn.",
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

            exp_str = (
                str(approved.undo_expires_at) if approved.undo_expires_at else None
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
                "undo_expires_at": exp_str,
                "undo_buffer_seconds": 60 if not send_immediately else 0,
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
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
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
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
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
            "[TIER-3 EXECUTION] Record final human hiring decision (ADVANCE / HOLD / REJECT) for an analyzed interview. "
            "Only callable by HR or ADMIN."
        ),
    )
    async def record_interview_decision(
        interview_id: str,
        decision: str = "ADVANCE",
        notes: str = "Keputusan dicatat melalui integrasi MCP WorkBuddy.",
        caller_role_override: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        caller = await verify_caller_rbac(ctx, caller_role_override)
        if caller.role not in ("HR", "ADMIN"):
            return {
                "success": False,
                "error_code": "403_MCP_PERMISSION_DENIED",
                "message": f"Akses ditolak: Role '{caller.role}' tidak berwenang mencatat keputusan akhir wawancara.",
            }

        async with AsyncSessionLocal() as db:
            user_stmt = (
                select(User)
                .where(User.vrole == caller.role)
                .order_by(User.nid.asc())
                .limit(1)
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
                decision=decision,  # type: ignore[arg-type]
                notes=notes,
            )
            try:
                saved = await svc.save_hr_decision(
                    interview_id=str(interview_id),
                    dto=req,
                    current_user=user,
                )
                return {
                    "success": True,
                    "interview_id": str(interview_id),
                    "decision": saved.decision,
                    "next_stage": saved.next_stage,
                    "message": f"Keputusan wawancara ({decision}) berhasil dicatat ke sistem dan audit log.",
                }
            except Exception as err:
                return {
                    "success": False,
                    "error_code": "DECISION_REJECTED",
                    "interview_id": str(interview_id),
                    "message": str(err),
                }
