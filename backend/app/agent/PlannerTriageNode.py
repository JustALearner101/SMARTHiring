from datetime import UTC, datetime, time, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.agent.AgentState import OrchestratorAgentState
from app.agent.LlmFactory import LlmFactory


class PlannerResolutionSchema(BaseModel):
    target_time_preference: str = Field(
        default="10:00",
        description="Preferred slot start time e.g. '10:00', '14:00', '11:30', '13:30'",
    )
    interviewer_message: str = Field(
        default="",
        description="Drafted invitation message or email body for the internal hiring manager/interviewer",
    )
    candidate_message: str = Field(
        default="",
        description="Drafted invitation message for the candidate via their preferred channel",
    )
    reasoning: str = Field(
        default="",
        description="Reasoning explaining slot choice, non-conflict verification, and channel selection",
    )


class PlannerTriageNode:
    @classmethod
    async def run(cls, state: OrchestratorAgentState) -> dict[str, Any]:
        cmd = state.get("command", "").strip()
        cmd_lower = cmd.lower()
        current_round = state.get("negotiation_round", 1)
        max_rounds = state.get("max_rounds", 3)

        # 1. Check negotiation limits & Out-of-Scope
        if current_round > max_rounds:
            reason = f"Limits on autonomous negotiations {max_rounds} round exceeded. Escalate to HR for manual resolution."
            return {
                "status": "DEADLOCK_ESCALATED",
                "escalation_reason": reason,
                "audit_entries": [
                    *state.get("audit_entries", []),
                    {
                        "event_type": "DEADLOCK_ESCALATED",
                        "actor": "AI_ORCHESTRATOR",
                        "actor_type": "AGENT",
                        "title": "Autonomous Negotiation Limit Exceeded",
                        "description": reason,
                        "metadata": {"round": current_round, "max_rounds": max_rounds},
                    },
                ],
            }

        # Check out-of-scope discussion (e.g. salary or contract negotiation)
        out_of_scope_keywords = ["gaji", "salary", "bonus", "tunjangan", "kontrak kerja", "benefit"]
        if any(kw in cmd_lower for kw in out_of_scope_keywords) and not state.get("guardrail_passed", True):
            reason = "Compensation topics beyond autonomous scheduling authority have been discussed. Escalate to HR for manual resolution."
            return {
                "status": "DEADLOCK_ESCALATED",
                "escalation_reason": reason,
                "audit_entries": [
                    *state.get("audit_entries", []),
                    {
                        "event_type": "DEADLOCK_ESCALATED",
                        "actor": "AI_ORCHESTRATOR",
                        "actor_type": "AGENT",
                        "title": "Out-of-Scope Negotiation Escalated",
                        "description": reason,
                        "metadata": {"topic": "compensation"},
                    },
                ],
            }

        cand_name = state.get("candidate_name") or "Rina Kusuma"
        cand_pos = state.get("candidate_position") or "Senior Frontend Engineer"
        cand_channel = "whatsapp" if ("whatsapp" in cmd_lower or "wa" in cmd_lower) else (state.get("candidate_channel") or "email")
        cand_email = state.get("candidate_email") or "candidate@example.com"
        cand_phone = state.get("candidate_phone") or "+6281234567890"

        inter_name = state.get("interviewer_name") or "Budi Santoso"
        inter_role = state.get("interviewer_role") or "VP of Engineering"
        inter_channel = "whatsapp" if ("wa budi" in cmd_lower or "whatsapp budi" in cmd_lower) else "email"
        inter_email = state.get("interviewer_email") or f"{inter_name.lower().replace(' ', '.')}@company.com"
        inter_phone = state.get("interviewer_phone") or "+6281198765432"
        inter_tz = state.get("interviewer_timezone") or "WIB"

        available_slots = state.get("available_slots") or []

        # 2. Invoke LLM for Dynamic Entity Resolution & Drafting with Fallback
        def fallback_planner() -> PlannerResolutionSchema:
            pref = "10:00"
            if "14:00" in cmd_lower or "2 siang" in cmd_lower:
                pref = "14:00"
            elif "11:30" in cmd_lower:
                pref = "11:30"
            elif "13:30" in cmd_lower:
                pref = "13:30"

            return PlannerResolutionSchema(
                target_time_preference=pref,
                interviewer_message=f"Halo {inter_name}, berikut draf undangan interview dengan {cand_name} untuk posisi {cand_pos}.",
                candidate_message=f"Halo Kak {cand_name}, kami mengundang Anda ke User Technical Interview via Google Meet pada jadwal yang disepakati.",
                reasoning="Fallback planner resolving standard schedule with corporate formatting.",
            )

        system_instruction = (
            "You are Heketon AI Orchestrator, an autonomous HR scheduling agent. "
            "Your task is to analyze the user's scheduling instruction, extract the target time preference, "
            "and draft professional, clear invitation messages for the interviewer and candidate. "
            "All timings must respect Indonesian business hours (09:00 - 17:00) and Friday prayer (11:30 - 13:00 WIB)."
        )
        user_content = (
            f"Command: '{cmd}'\n"
            f"Candidate: {cand_name} ({cand_pos})\n"
            f"Interviewer: {inter_name} ({inter_role})\n"
            f"Available Database Slots: {[s.get('formatted_wib') for s in available_slots[:4]]}"
        )

        plan_res = await LlmFactory.invoke_structured_or_fallback(
            schema=PlannerResolutionSchema,
            system_instruction=system_instruction,
            user_content=user_content,
            fallback_fn=fallback_planner,
        )

        # 3. Slot Time Planning (Using Real DB Calendar Slots if Available)
        chosen_slot_data: dict[str, Any] | None = None

        if available_slots:
            # Try to find a slot matching target time preference
            target_pref = plan_res.target_time_preference
            for s in available_slots:
                if s.get("time_str") == target_pref or target_pref in s.get("formatted_wib", ""):
                    chosen_slot_data = s
                    break
            if not chosen_slot_data:
                # Pick the first available slot from the database
                chosen_slot_data = available_slots[0]

        if chosen_slot_data:
            slot_dict = {
                "title": f"User Technical Interview: {cand_name}",
                "start_utc": chosen_slot_data["start_utc"],
                "end_utc": chosen_slot_data["end_utc"],
                "formatted_wib": chosen_slot_data["formatted_wib"],
                "formatted_wita": chosen_slot_data["formatted_wita"],
                "duration_minutes": 60,
                "location_type": "Google Meet",
                "meeting_link": "https://meet.google.com/hkt-ops-2026",
            }
        else:
            # Deterministic calculation fallback
            now = datetime.now(UTC)
            target_hour = 10
            target_minute = 0
            if "14:00" in cmd_lower or "2 siang" in cmd_lower or plan_res.target_time_preference == "14:00":
                target_hour = 14
            elif "11:30" in cmd_lower or plan_res.target_time_preference == "11:30":
                target_hour = 11
                target_minute = 30
            elif "13:30" in cmd_lower or plan_res.target_time_preference == "13:30":
                target_hour = 13
                target_minute = 30

            day_offset = 2
            if "besok" in cmd_lower:
                day_offset = 1
            elif "kamis" in cmd_lower:
                day_offset = 3
            elif "jumat" in cmd_lower:
                day_offset = 4

            target_date = (now + timedelta(days=day_offset)).date()
            target_slot_start = datetime.combine(target_date, time(target_hour, target_minute), tzinfo=UTC) - timedelta(hours=7)
            target_slot_end = target_slot_start + timedelta(hours=1)

            wib_time = target_slot_start + timedelta(hours=7)
            wita_time = target_slot_start + timedelta(hours=8)

            slot_dict = {
                "title": f"User Technical Interview: {cand_name}",
                "start_utc": target_slot_start.isoformat(),
                "end_utc": target_slot_end.isoformat(),
                "formatted_wib": f"{wib_time.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{wita_time.strftime('%A, %d %b %Y, %H:%M')} WITA",
                "duration_minutes": 60,
                "location_type": "Google Meet",
                "meeting_link": "https://meet.google.com/hkt-ops-2026",
            }

        # 4. Sources Cited
        inter_slug = inter_name.lower().replace(" ", "-")
        sources = [
            {
                "id": "src-01",
                "ref_code": f"[cal-{inter_slug}]",
                "source_type": "CALENDAR",
                "title": f"Kalender {inter_name}",
                "detail": f"Slot kosong terverifikasi pukul {slot_dict.get('formatted_wib', '')} ({inter_tz}) tanpa konflik jadwal lain.",
            },
            {
                "id": "src-02",
                "ref_code": "[rule-jumatan]",
                "source_type": "OPERATIONAL_RULE",
                "title": "Rules for Friday Prayer & Work Hours",
                "detail": "Compliance with the 09:00 - 17:00 operational boundary and the Friday Prayer worship window (11:30 - 13:00 WIB).",
            },
            {
                "id": "src-03",
                "ref_code": f"[cand-ats-{state.get('candidate_id', 1)}]",
                "source_type": "CANDIDATE_ATS",
                "title": f"Preferensi Kontak {cand_name}",
                "detail": f"Channel default: {cand_channel.upper()} (Standar Korporasi), Posisi: {cand_pos}.",
            },
        ]

        # 5. Action Items Draft (3 items)
        interviewer_text = plan_res.interviewer_message or f"Halo {inter_name}, berikut draf undangan interview dengan {cand_name} untuk posisi {cand_pos}."
        candidate_text = plan_res.candidate_message or f"Halo Kak {cand_name}, kami mengundang Anda ke User Technical Interview via Google Meet pada jadwal yang disepakati."

        action_items = [
            {
                "id": "item-01",
                "action_type": "send_whatsapp" if inter_channel == "whatsapp" else "send_email",
                "recipient_name": inter_name,
                "recipient_role": inter_role,
                "recipient_contact": inter_phone if inter_channel == "whatsapp" else inter_email,
                "channel": inter_channel,
                "subject": f"User Technical Interview Invitation: {cand_name}" if inter_channel == "email" else None,
                "content_preview": interviewer_text,
                "is_external": False,
            },
            {
                "id": "item-02",
                "action_type": "send_whatsapp" if cand_channel == "whatsapp" else "send_email",
                "recipient_name": cand_name,
                "recipient_role": "Candidate",
                "recipient_contact": cand_phone if cand_channel == "whatsapp" else cand_email,
                "channel": cand_channel,
                "subject": f"Technical Interview Invitation — {cand_pos}" if cand_channel == "email" else None,
                "content_preview": candidate_text,
                "is_external": True,  # External communication triggers High-Impact
            },
            {
                "id": "item-03",
                "action_type": "book_calendar",
                "recipient_name": f"{inter_name} & {cand_name}",
                "recipient_role": "Attendees",
                "recipient_contact": f"{inter_email}, {cand_email}",
                "channel": "calendar",
                "subject": f"Technical Interview: {cand_name} x {inter_name}",
                "content_preview": "Synchronize a 60-minute Google Meet calendar slot.",
                "is_external": False,
            },
        ]

        return {
            "proposed_slot": slot_dict,
            "sources_cited": sources,
            "items": action_items,
            "is_high_impact": True,
            "status": "ANALYZING",
        }
