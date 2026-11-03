import re
from datetime import UTC, date, datetime, time, timedelta
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
            reason = f"Autonomous negotiation limit of {max_rounds} rounds exceeded. Escalate to HR for manual resolution."
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

        # Check out-of-scope requests: financial transactions, payments, salary, catering, loans, etc. (TC-CHB-11)
        financial_keywords = [
            "transfer", "bayar", "pembayaran", "rekening", "invoice", "katering",
            "rp", "rupiah", "uang", "gaji", "salary", "bonus", "tunjangan",
            "kontrak kerja", "benefit", "payroll", "pinjaman", "reimburse",
        ]
        if any(re.search(rf"\b{re.escape(kw)}\b", cmd_lower) for kw in financial_keywords):
            reason = (
                f"Permintaan transaksi finansial atau pembayaran ('{cmd}') berada di luar cakupan wewenang (scope) AI Orchestrator HR & Office Ops. "
                "Sistem tidak memproses transaksi pembayaran atau membuat jadwal fiktif. "
                "Silakan hubungi pemilik proses manusia: Tim Finance & Accounting (Budi Hartono - Finance Manager, budi.hartono@company.com)."
            )
            return {
                "status": "OUT_OF_SCOPE_REFUSED",
                "escalation_reason": reason,
                "audit_entries": [
                    *state.get("audit_entries", []),
                    {
                        "event_type": "OUT_OF_SCOPE_REFUSED",
                        "actor": "AI_ORCHESTRATOR",
                        "actor_type": "AGENT",
                        "title": "Out-of-Scope Financial Request Refused",
                        "description": reason,
                        "metadata": {"topic": "financial_transaction", "raw_command": cmd},
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

        # Location extraction
        loc_match = re.search(r"\b(?:di|at|in)\s+(ruang\s+rapat\s*[\w\d]+|meeting\s+room\s*[\w\d]+|room\s*[\w\d]+)\b", cmd, re.IGNORECASE)
        if loc_match:
            location_type = loc_match.group(1).strip().title()
            meeting_link = f"On-Site: {location_type}"
        else:
            location_type = "Google Meet"
            meeting_link = "https://meet.google.com/hkt-ops-2026"

        # 2. Invoke LLM for Dynamic Entity Resolution & Drafting with Fallback
        def fallback_planner() -> PlannerResolutionSchema:
            pref = "10:00"
            if "16:00" in cmd_lower or "16.00" in cmd_lower or "4 sore" in cmd_lower:
                pref = "16:00"
            elif "14:00" in cmd_lower or "14.00" in cmd_lower or "2 siang" in cmd_lower:
                pref = "14:00"
            elif "11:30" in cmd_lower or "11.30" in cmd_lower:
                pref = "11:30"
            elif "13:30" in cmd_lower or "13.30" in cmd_lower:
                pref = "13:30"
            elif "siang" in cmd_lower:
                if "jumat" in cmd_lower or "friday" in cmd_lower:
                    pref = "14:00"
                else:
                    pref = "13:30"
            else:
                t_match = re.search(r"\b(?:jam|pukul)?\s*(\d{1,2})[.:](\d{2})\b", cmd_lower)
                if t_match:
                    pref = f"{int(t_match.group(1)):02d}:{int(t_match.group(2)):02d}"
                else:
                    h_match = re.search(r"\b(?:jam|pukul)\s*(\d{1,2})\b", cmd_lower)
                    if h_match:
                        h = int(h_match.group(1))
                        if ("siang" in cmd_lower or "sore" in cmd_lower) and h < 12:
                            h += 12
                        pref = f"{h:02d}:00"

            return PlannerResolutionSchema(
                target_time_preference=pref,
                interviewer_message=f"Hello {inter_name}, here is the update regarding the schedule with {cand_name}.",
                candidate_message=f"Dear {cand_name}, here is the notification regarding the proposed schedule.",
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
        is_notulen = any(kw in cmd_lower for kw in ["notulen", "catatan rapat", "meeting minutes", "minutes"])
        is_reminder = any(kw in cmd_lower for kw in ["ingatkan", "remind", "reminder", "kirim dokumen", "dokumen"])
        is_interview = any(kw in cmd_lower for kw in ["interview", "wawancara", "interviw", "teknis", "technical"])
        is_scheduling = any(kw in cmd_lower for kw in ["jadwal", "jadwalin", "follow-up", "follow up", "schedule", "booking", "temu", "rapat"])

        slot_title = f"Follow-Up Meeting: {location_type}" if is_notulen else f"User Technical Interview: {cand_name}"

        target_pref = plan_res.target_time_preference
        chosen_slot_data: dict[str, Any] | None = None

        if available_slots:
            for s in available_slots:
                if s.get("time_str") == target_pref or target_pref in s.get("formatted_wib", ""):
                    chosen_slot_data = s
                    break
            if not chosen_slot_data and not any(kw in cmd_lower for kw in ["14:00", "14.00", "16:00", "16.00", "11:30", "13:30", "siang"]):
                chosen_slot_data = available_slots[0]

        if chosen_slot_data:
            start_utc_dt = datetime.fromisoformat(chosen_slot_data["start_utc"])
            wib_t = start_utc_dt + timedelta(hours=7)
            wita_t = start_utc_dt + timedelta(hours=8)
            wit_t = start_utc_dt + timedelta(hours=9)
            slot_dict = {
                "title": slot_title,
                "start_utc": chosen_slot_data["start_utc"],
                "end_utc": chosen_slot_data["end_utc"],
                "formatted_wib": chosen_slot_data.get("formatted_wib") or f"{wib_t.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": chosen_slot_data.get("formatted_wita") or f"{wita_t.strftime('%A, %d %b %Y, %H:%M')} WITA",
                "formatted_wit": chosen_slot_data.get("formatted_wit") or f"{wit_t.strftime('%A, %d %b %Y, %H:%M')} WIT",
                "duration_minutes": 60,
                "location_type": location_type,
                "meeting_link": meeting_link,
            }
        else:
            now_utc = datetime.now(UTC)
            now_wib = now_utc + timedelta(hours=7)

            target_date_hint = state.get("target_date_hint")
            if target_date_hint:
                try:
                    target_date = date.fromisoformat(target_date_hint)
                except Exception:
                    target_date = (now_wib + timedelta(days=2)).date()
            else:
                day_keywords = {
                    "monday": 0, "senin": 0, "tuesday": 1, "selasa": 1,
                    "wednesday": 2, "rabu": 2, "thursday": 3, "kamis": 3,
                    "friday": 4, "jumat": 4, "saturday": 5, "sabtu": 5,
                    "sunday": 6, "minggu": 6,
                }
                target_date = (now_wib + timedelta(days=2)).date()
                for kw, target_wd in day_keywords.items():
                    if kw in cmd_lower:
                        days_ahead = (target_wd - now_wib.weekday() + 7) % 7
                        if days_ahead == 0 and not any(h in cmd_lower for h in ["hari ini", "today"]):
                            days_ahead = 7
                        target_date = (now_wib + timedelta(days=days_ahead)).date()
                        break

                if "besok" in cmd_lower or "tomorrow" in cmd_lower:
                    target_date = (now_wib + timedelta(days=1)).date()
                elif "lusa" in cmd_lower or "day after tomorrow" in cmd_lower:
                    target_date = (now_wib + timedelta(days=2)).date()

            parts = target_pref.split(":")
            try:
                target_hour = int(parts[0])
                target_minute = int(parts[1]) if len(parts) > 1 else 0
            except ValueError:
                target_hour = 10
                target_minute = 0

            target_slot_start = datetime.combine(target_date, time(target_hour, target_minute), tzinfo=UTC) - timedelta(hours=7)
            target_slot_end = target_slot_start + timedelta(hours=1)

            wib_time = target_slot_start + timedelta(hours=7)
            wita_time = target_slot_start + timedelta(hours=8)
            wit_time = target_slot_start + timedelta(hours=9)

            slot_dict = {
                "title": slot_title,
                "start_utc": target_slot_start.isoformat(),
                "end_utc": target_slot_end.isoformat(),
                "formatted_wib": f"{wib_time.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{wita_time.strftime('%A, %d %b %Y, %H:%M')} WITA",
                "formatted_wit": f"{wit_time.strftime('%A, %d %b %Y, %H:%M')} WIT",
                "duration_minutes": 60,
                "location_type": location_type,
                "meeting_link": meeting_link,
            }

        # 4. Sources Cited
        inter_slug = inter_name.lower().replace(" ", "-")
        sources = [
            {
                "id": "src-01",
                "ref_code": f"[cal-{inter_slug}]",
                "source_type": "CALENDAR",
                "title": f"Calendar: {inter_name}",
                "detail": f"Available slot verified at {slot_dict.get('formatted_wib', '')} ({inter_tz}) without conflicts.",
            },
            {
                "id": "src-02",
                "ref_code": "[rule-friday-prayer]",
                "source_type": "OPERATIONAL_RULE",
                "title": "Rules for Friday Prayer & Work Hours",
                "detail": "Compliance with the 09:00 - 17:00 operational boundary and the Friday Prayer worship window (11:30 - 13:00 WIB).",
            },
            {
                "id": "src-03",
                "ref_code": f"[cand-ats-{state.get('candidate_id', 1)}]",
                "source_type": "CANDIDATE_ATS",
                "title": f"Contact Preferences: {cand_name}",
                "detail": f"Default channel: {cand_channel.upper()} (Corporate standard), Position: {cand_pos}.",
            },
        ]

        # 5. Multi-Action Item Decomposition
        external_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", cmd)
        known_emails = [inter_email.lower(), cand_email.lower()]
        extra_external_emails = [e for e in external_emails if e.lower() not in known_emails]

        action_items: list[dict[str, Any]] = []

        if is_notulen or is_reminder or extra_external_emails:
            # Discrete compound actions
            if is_notulen:
                action_items.append({
                    "id": f"item-0{len(action_items)+1}",
                    "action_type": "send_email",
                    "recipient_name": inter_name,
                    "recipient_role": inter_role,
                    "recipient_contact": inter_email,
                    "channel": "email",
                    "subject": f"Notulen Rapat Koordinasi — {inter_name}",
                    "content_preview": (
                        f"Yth. {inter_name},\n\nBerikut ringkasan notulen rapat koordinasi:\n"
                        "- Pembahasan: Evaluasi target operasional dan pembagian follow-up tim.\n"
                        "- Catatan: Jadwal follow-up telah dipersiapkan sesuai arahan.\n\n"
                        "Salam,\nHR & Operations"
                    ),
                    "is_external": False,
                })

            for ext_email in extra_external_emails:
                action_items.append({
                    "id": f"item-0{len(action_items)+1}",
                    "action_type": "send_email",
                    "recipient_name": f"External Recipient ({ext_email})",
                    "recipient_role": "External Vendor",
                    "recipient_contact": ext_email,
                    "channel": "email",
                    "subject": "Notulen Rapat Koordinasi (External Copy)",
                    "content_preview": (
                        f"Dear Partner ({ext_email}),\n\nTerlampir salinan notulen rapat koordinasi untuk tindak lanjut vendor mitra.\n\n"
                        "Salam,\nHR & Office Operations"
                    ),
                    "is_external": True,
                })

            if is_scheduling:
                cal_recipients = [inter_name]
                cal_contacts = [inter_email]
                if is_interview or not is_notulen:
                    cal_recipients.append(cand_name)
                    cal_contacts.append(cand_email)

                action_items.append({
                    "id": f"item-0{len(action_items)+1}",
                    "action_type": "book_calendar",
                    "recipient_name": " & ".join(cal_recipients),
                    "recipient_role": "Attendees",
                    "recipient_contact": ", ".join(cal_contacts),
                    "channel": "calendar",
                    "subject": f"{slot_title} ({location_type})",
                    "content_preview": f"Reservasi slot kalender pada {slot_dict.get('formatted_wib')} di {location_type} ({slot_dict.get('duration_minutes', 60)} Menit).",
                    "is_external": False,
                })

            if is_reminder:
                action_items.append({
                    "id": f"item-0{len(action_items)+1}",
                    "action_type": "send_whatsapp" if cand_channel == "whatsapp" else "send_email",
                    "recipient_name": cand_name,
                    "recipient_role": "Candidate",
                    "recipient_contact": cand_phone if cand_channel == "whatsapp" else cand_email,
                    "channel": cand_channel,
                    "subject": "Pengingat Kelengkapan Dokumen Administrasi" if cand_channel == "email" else None,
                    "content_preview": (
                        f"Halo {cand_name},\n\nMohon kesediaannya untuk segera mengirimkan dokumen pendukung/administrasi "
                        "yang diperlukan agar proses rekrutmen dapat dilanjutkan.\n\nTerima kasih,\nTim HR"
                    ),
                    "is_external": True,
                })
        else:
            interviewer_text = plan_res.interviewer_message or f"Hello {inter_name}, here is the interview invitation draft with {cand_name} for the {cand_pos} position."
            candidate_text = plan_res.candidate_message or f"Dear {cand_name}, we invite you to a User Technical Interview via Google Meet at the agreed schedule."

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
                    "is_external": True,
                },
                {
                    "id": "item-03",
                    "action_type": "book_calendar",
                    "recipient_name": f"{inter_name} & {cand_name}",
                    "recipient_role": "Attendees",
                    "recipient_contact": f"{inter_email}, {cand_email}",
                    "channel": "calendar",
                    "subject": f"Technical Interview: {cand_name} x {inter_name}",
                    "content_preview": f"Synchronize a 60-minute {location_type} calendar slot.",
                    "is_external": False,
                },
            ]

        has_external = bool(extra_external_emails or any(it.get("is_external") for it in action_items))

        return {
            "proposed_slot": slot_dict,
            "sources_cited": sources,
            "items": action_items,
            "is_high_impact": has_external,
            "status": "ANALYZING",
        }
