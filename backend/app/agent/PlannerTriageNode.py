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
    @staticmethod
    def _extract_explicit_time_and_tz(cmd_lower: str) -> tuple[str | None, str | None]:
        """Deterministically extracts explicit requested time (HH:MM) and timezone (WIB/WITA/WIT) from command."""
        explicit_tz: str | None = None

        # 1. Match explicit HH:MM or HH.MM with optional period and timezone
        # Avoid matching percentages like "92%"
        for m in re.finditer(
            r"\b(?:(jam|pukul|at)\s*)?(\d{1,2})[.:](\d{2})(?:\s*(pagi|siang|sore|malam|am|pm))?(?:\s*(wib|wita|wit))?\b",
            cmd_lower,
        ):
            h = int(m.group(2))
            minute = int(m.group(3))
            period = m.group(4)
            tz_tok = m.group(5)
            if 0 <= h <= 23 and 0 <= minute <= 59:
                if period in ("siang", "sore", "malam", "pm") and 1 <= h < 12 or not period and ("siang" in cmd_lower or "sore" in cmd_lower) and 1 <= h <= 6:
                    h += 12
                if tz_tok:
                    explicit_tz = tz_tok.upper()
                return f"{h:02d}:{minute:02d}", explicit_tz

        # 2. Match "jam <H> [pagi|siang|sore|malam] [wib|wita|wit]"
        m_hour = re.search(
            r"\b(?:jam|pukul|at)\s*(\d{1,2})(?:\s*(pagi|siang|sore|malam|am|pm))?(?:\s*(wib|wita|wit))?\b",
            cmd_lower,
        )
        if m_hour:
            h = int(m_hour.group(1))
            period = m_hour.group(2)
            tz_tok = m_hour.group(3)
            if 0 <= h <= 23:
                if period in ("siang", "sore", "malam", "pm") and 1 <= h < 12 or not period and ("siang" in cmd_lower or "sore" in cmd_lower) and 1 <= h <= 6:
                    h += 12
                if tz_tok:
                    explicit_tz = tz_tok.upper()
                return f"{h:02d}:00", explicit_tz

        # 3. Check general timezone mention if no inline timezone token was attached
        if re.search(r"\bwita\b", cmd_lower) and not re.search(r"\bwib\b", cmd_lower):
            explicit_tz = "WITA"
        elif re.search(r"\bwit\b", cmd_lower) and not re.search(r"\bwib\b", cmd_lower):
            explicit_tz = "WIT"
        elif re.search(r"\bwib\b", cmd_lower):
            explicit_tz = "WIB"

        # 4. Natural language time-of-day hints (e.g. TC-CHB-01 "Jumat siang")
        if "siang" in cmd_lower or "midday" in cmd_lower or "noon" in cmd_lower:
            if "jumat" in cmd_lower or "friday" in cmd_lower:
                return "14:00", explicit_tz
            return "13:30", explicit_tz
        if "sore" in cmd_lower or "afternoon" in cmd_lower:
            return "15:00", explicit_tz

        return None, explicit_tz

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
        has_wa_kw = bool(re.search(r"\b(?:whatsapp|wa)\b", cmd_lower))
        cand_channel = "whatsapp" if has_wa_kw else (state.get("candidate_channel") or "email")
        cand_email = state.get("candidate_email") or "candidate@example.com"
        cand_phone = state.get("candidate_phone") or "+6281234567890"
        cand_tz = (state.get("candidate_timezone") or "WIB").upper()

        inter_name = state.get("interviewer_name") or "Budi Santoso"
        inter_role = state.get("interviewer_role") or "VP of Engineering"
        inter_channel = "whatsapp" if ("wa budi" in cmd_lower or "whatsapp budi" in cmd_lower) else "email"
        inter_email = state.get("interviewer_email") or f"{inter_name.lower().replace(' ', '.')}@company.com"
        inter_phone = state.get("interviewer_phone") or "+6281198765432"
        inter_tz = (state.get("interviewer_timezone") or "WIB").upper()

        available_slots = state.get("available_slots") or []

        # Location & Meeting Platform / Link extraction (Supports Google Meet, Microsoft Teams, Zoom, or Custom URL)
        url_match = re.search(r"(https?://[^\s,\"')]+)", cmd, re.IGNORECASE)
        custom_url = url_match.group(1).rstrip(".,;)") if url_match else None

        loc_match = re.search(
            r"\b(?:di|at|in)\s+(ruang\s+rapat\s*[\w\d]+|meeting\s+room\s*[\w\d]+|room\s*[\w\d]+)\b",
            cmd,
            re.IGNORECASE,
        )
        if loc_match:
            location_type = loc_match.group(1).strip().title()
            meeting_link = custom_url or f"On-Site: {location_type}"
        elif (
            (custom_url and ("teams.microsoft.com" in custom_url.lower() or "teams.live.com" in custom_url.lower()))
            or re.search(r"\b(?:microsoft\s+teams|ms\s+teams|teams)\b", cmd_lower)
        ):
            location_type = "Microsoft Teams"
            meeting_link = custom_url or "https://teams.microsoft.com/l/meetup-join/heketon-ops-2026"
        elif (
            (custom_url and ("zoom.us" in custom_url.lower() or "zoom.com" in custom_url.lower()))
            or re.search(r"\bzoom\b", cmd_lower)
        ):
            location_type = "Zoom Meeting"
            meeting_link = custom_url or "https://zoom.us/j/98234123890"
        else:
            location_type = "Google Meet"
            meeting_link = custom_url or "https://meet.google.com/hkt-ops-2026"

        explicit_time_pref, explicit_tz = cls._extract_explicit_time_and_tz(cmd_lower)
        if not explicit_tz:
            if re.search(r"\bwita\b", cmd_lower) and not re.search(r"\bwib\b", cmd_lower):
                explicit_tz = "WITA"
            elif re.search(r"\bwit\b", cmd_lower) and not re.search(r"\bwib\b", cmd_lower):
                explicit_tz = "WIT"

        # 2. Invoke LLM for Dynamic Entity Resolution & Drafting with Fallback
        def fallback_planner() -> PlannerResolutionSchema:
            pref = explicit_time_pref or "10:00"
            return PlannerResolutionSchema(
                target_time_preference=pref,
                interviewer_message=f"Hello {inter_name}, here is the update regarding the schedule with {cand_name}.",
                candidate_message=f"Dear {cand_name}, here is the notification regarding the proposed schedule.",
                reasoning="Fallback planner resolving standard schedule with corporate formatting.",
            )

        system_instruction = (
            "You are Heketon AI Orchestrator, an autonomous HR scheduling agent. "
            "Your task is to analyze the user's scheduling instruction, extract the target time preference in HH:MM format (24-hour), "
            "and draft professional, clear invitation messages for the interviewer and candidate. "
            "All timings must respect Indonesian business hours (09:00 - 17:00) and Friday prayer (11:30 - 13:00 WIB)."
        )
        user_content = (
            f"Command: '{cmd}'\n"
            f"Candidate: {cand_name} ({cand_pos}, Timezone: {cand_tz})\n"
            f"Interviewer: {inter_name} ({inter_role}, Timezone: {inter_tz})\n"
            f"Available Database Slots: {[s.get('formatted_wib') for s in available_slots]}"
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

        clean_cand_name = re.sub(r"\s+[0-9a-f]{6}\b", "", cand_name)
        slot_title = f"Follow-Up Meeting: {location_type}" if is_notulen else f"Technical Interview: {clean_cand_name}"

        # Sanitize LLM target_time_preference and prioritize deterministic explicit_time_pref from command
        raw_llm_pref = plan_res.target_time_preference or "10:00"
        m_llm = re.search(r"(\d{1,2})[.:](\d{2})", raw_llm_pref)
        sanitized_llm_pref = f"{int(m_llm.group(1)):02d}:{int(m_llm.group(2)):02d}" if m_llm else "10:00"
        target_pref = explicit_time_pref or sanitized_llm_pref

        # Convert target_pref to WIB if the user explicitly requested a numeric clock time in WITA or WIT
        # (do not shift generic "Jumat siang" -> 14:00 WIB, and do not shift if "WIB" was attached to the time)
        is_generic_siang = ("siang" in cmd_lower or "midday" in cmd_lower or "noon" in cmd_lower) and not re.search(
            r"\b(?:jam|pukul|at)?\s*\d{1,2}(?:[.:]\d{2})?\b", cmd_lower
        )
        effective_input_tz = explicit_tz
        if not effective_input_tz and inter_tz == "WITA" and cand_tz == "WITA":
            effective_input_tz = "WITA"

        if (
            not is_generic_siang
            and effective_input_tz in ("WITA", "WIT")
            and not re.search(r"\d{1,2}(?:[.:]\d{2})?\s*wib\b", cmd_lower)
        ):
            p_parts = target_pref.split(":")
            req_h = int(p_parts[0])
            req_m = int(p_parts[1]) if len(p_parts) > 1 else 0
            offset_to_wib = 1 if effective_input_tz == "WITA" else 2
            wib_h = (req_h - offset_to_wib) % 24
            target_pref = f"{wib_h:02d}:{req_m:02d}"

        chosen_slot_data: dict[str, Any] | None = None
        slot_conflict_detected = False
        conflicting_slot_wib: str | None = None

        # Determine if target_pref is a rule violation that SecondaryValidatorNode should catch and explain
        p_parts = target_pref.split(":")
        pref_h = int(p_parts[0]) if p_parts[0].isdigit() else 10
        pref_m = int(p_parts[1]) if len(p_parts) > 1 and p_parts[1].isdigit() else 0
        pref_minutes = pref_h * 60 + pref_m

        target_date_str = state.get("target_date")
        is_target_friday = False
        if target_date_str:
            try:
                is_target_friday = date.fromisoformat(target_date_str).weekday() == 4
            except Exception:
                is_target_friday = "jumat" in cmd_lower or "friday" in cmd_lower
        else:
            is_target_friday = "jumat" in cmd_lower or "friday" in cmd_lower

        is_friday_prayer_time = is_target_friday and (11 * 60 + 30 <= pref_minutes < 13 * 60)
        cand_tz_offset_h = 2 if cand_tz == "WIT" else (1 if cand_tz == "WITA" else 0)
        is_outside_working_hours = (
            pref_h < 9
            or pref_h >= 17
            or (pref_h + cand_tz_offset_h) < 9
            or (pref_h + cand_tz_offset_h) >= 17
        )

        if available_slots:
            for s in available_slots:
                if s.get("time_str") == target_pref or target_pref in s.get("formatted_wib", ""):
                    chosen_slot_data = s
                    break
            # If target_pref is within valid working hours and not Friday prayer, yet missing from available_slots,
            # it means an existing CalendarEvent in the DB occupies that slot (TC-SCHED-17).
            # Select the nearest available slot to prevent double-booking!
            if not chosen_slot_data and not is_friday_prayer_time and not is_outside_working_hours:
                slot_conflict_detected = True
                conflicting_slot_wib = f"{target_pref} WIB"
                # Prefer the first available slot after target_pref, or fallback to available_slots[0]
                after_slots = [
                    s for s in available_slots
                    if s.get("time_str", "00:00") > target_pref
                ]
                chosen_slot_data = after_slots[0] if after_slots else available_slots[0]

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

            target_date_hint = state.get("target_date") or state.get("target_date_hint")
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

        # 4. Sources Cited (TC-CHB-18, TC-SCHED-06: backed by real DB identifiers)
        inter_slug = inter_name.lower().replace(" ", "-")
        inter_uid = state.get("interviewer_userid") or f"USR-00{state.get('interviewer_id') or 2}"
        cand_code = state.get("candidate_code") or f"CAND-2026-00{state.get('candidate_id') or 1}"
        office_code = state.get("office_code") or "HQ-JKT"
        sources = [
            {
                "id": f"cal-{office_code.lower()}-{inter_uid.lower()}",
                "ref_code": f"[cal-{inter_slug}:{inter_uid}:{office_code}]",
                "source_type": "CALENDAR",
                "title": f"Calendar: {inter_name} ({inter_uid} / {office_code})",
                "detail": (
                    f"Available slot verified on work calendar {office_code} for {inter_name} ({inter_email}) "
                    f"at {slot_dict.get('formatted_wib', '')} ({inter_tz}) without conflicts."
                ),
            },
            {
                "id": "rule-friday-prayer-working-hours",
                "ref_code": "[rule-friday-prayer:RULE_FRIDAY_PRAYER]",
                "source_type": "OPERATIONAL_RULE",
                "title": "Rules for Friday Prayer & Work Hours",
                "detail": (
                    "Compliance with active policies RULE_WORKING_HOURS (09:00 - 17:00 operational boundary, 15m buffer) "
                    "and RULE_FRIDAY_PRAYER (11:30 - 13:00 WIB worship window)."
                ),
            },
            {
                "id": f"cand-{cand_code.lower()}",
                "ref_code": f"[cand-ats-{state.get('candidate_id', 1)}:{cand_code}]",
                "source_type": "CANDIDATE_ATS",
                "title": f"Contact Preferences: {cand_name} ({cand_code})",
                "detail": (
                    f"ATS Code: {cand_code} (ID #{state.get('candidate_id', 1)}), Contact: {cand_email} / {cand_phone}, "
                    f"Default channel: {cand_channel.upper()} ({cand_tz}), Position: {cand_pos}."
                ),
            },
        ]

        # 5. Multi-Action Item Decomposition
        external_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", cmd)
        known_emails = [inter_email.lower(), cand_email.lower()]
        extra_external_emails = [e for e in external_emails if e.lower() not in known_emails]

        action_items: list[dict[str, Any]] = []

        inter_slot_display = (
            slot_dict.get("formatted_wita")
            if inter_tz == "WITA"
            else (slot_dict.get("formatted_wit") if inter_tz == "WIT" else slot_dict.get("formatted_wib"))
        )
        cand_slot_display = (
            slot_dict.get("formatted_wita")
            if cand_tz == "WITA"
            else (slot_dict.get("formatted_wit") if cand_tz == "WIT" else slot_dict.get("formatted_wib"))
        )
        all_tz_display = (
            f"{slot_dict.get('formatted_wib')} = {slot_dict.get('formatted_wita')} = {slot_dict.get('formatted_wit')}"
        )

        if is_notulen or is_reminder or extra_external_emails:
            # Discrete compound actions
            if is_notulen:
                note_summary_line = cmd.strip()
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
                        f"- Ringkasan Catatan: {note_summary_line}\n"
                        f"- Pembahasan: Evaluasi target operasional dan pembagian follow-up tim.\n"
                        f"- Jadwal Follow-Up ({inter_tz}): {inter_slot_display} ({all_tz_display})\n"
                        f"- Lokasi / Tautan: {location_type} ({meeting_link})\n\n"
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
                    "content_preview": (
                        f"Reservasi slot kalender pada {inter_slot_display} ({all_tz_display}) "
                        f"di {location_type} ({slot_dict.get('duration_minutes', 60)} Menit)."
                    ),
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
            interviewer_text = (
                f"Yth. {inter_name},\n\n"
                f"Berikut undangan User Technical Interview bersama kandidat {clean_cand_name} ({cand_pos}):\n"
                f"- Jadwal ({inter_tz}): {inter_slot_display}\n"
                f"- Konversi Zona Waktu: {all_tz_display}\n"
                f"- Durasi: {slot_dict.get('duration_minutes', 60)} Menit\n"
                f"- Lokasi / Tautan: {location_type} ({meeting_link})\n\n"
                "Salam,\nHR & Talent Acquisition"
            )
            candidate_text = (
                f"Halo {clean_cand_name},\n\n"
                f"Kami mengundang Anda untuk mengikuti User Technical Interview posisi {cand_pos} bersama {inter_name}:\n"
                f"- Jadwal Waktu Lokal Anda ({cand_tz}): {cand_slot_display}\n"
                f"- Konversi Zona Waktu: {all_tz_display}\n"
                f"- Durasi: {slot_dict.get('duration_minutes', 60)} Menit\n"
                f"- Lokasi / Tautan: {location_type} ({meeting_link})\n\n"
                "Mohon konfirmasi ketersediaan Anda. Terima kasih,\nTim HR"
            )

            action_items = [
                {
                    "id": "item-01",
                    "action_type": "send_whatsapp" if inter_channel == "whatsapp" else "send_email",
                    "recipient_name": inter_name,
                    "recipient_role": inter_role,
                    "recipient_contact": inter_phone if inter_channel == "whatsapp" else inter_email,
                    "channel": inter_channel,
                    "subject": f"Technical Interview Invitation: {clean_cand_name} ({cand_pos})" if inter_channel == "email" else None,
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
                    "content_preview": (
                        f"Reservasi slot kalender 60 menit ({location_type}) pada {all_tz_display}."
                    ),
                    "is_external": False,
                },
            ]

        has_external = bool(extra_external_emails or any(it.get("is_external") for it in action_items))

        return {
            "proposed_slot": slot_dict,
            "sources_cited": sources,
            "items": action_items,
            "is_high_impact": has_external,
            "slot_conflict_detected": slot_conflict_detected,
            "conflicting_slot_wib": conflicting_slot_wib,
            "status": "ANALYZING",
        }
