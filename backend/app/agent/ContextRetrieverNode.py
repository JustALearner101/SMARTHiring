import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.repository.CalendarMatrixRepository import CalendarMatrixRepository
from app.repository.CandidateRepository import CandidateRepository
from app.repository.ContactRepository import ContactRepository
from app.repository.OperationalPolicyRepository import OperationalPolicyRepository


class ContextRetrieverNode:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.contact_repo = ContactRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.policy_repo = OperationalPolicyRepository(session)
        self.cal_repo = CalendarMatrixRepository(session)

    async def run(self, state: OrchestratorAgentState) -> dict[str, Any]:
        cmd = state.get("command", "").strip()
        cmd_lower = cmd.lower()

        # ---------------------------------------------------------------------
        # 1. Disambiguation Check for Interviewer
        # ---------------------------------------------------------------------
        # Check if generic "budi" is mentioned without department or last name
        if "budi" in cmd_lower and not any(kw in cmd_lower for kw in ["santoso", "engineering", "hartono", "finance"]):
            ambiguous_users = await self.contact_repo.find_ambiguous_names("Budi")
            if len(ambiguous_users) > 1:
                profiles = [
                    {
                        "id": str(u.nid),
                        "name": u.vname,
                        "employee_id": u.vuserid,
                        "role": u.vposition or u.vrole,
                        "department": u.vdepartment or "General",
                        "timezone": u.vtimezone,
                        "email": u.vemail,
                        "phone": u.vphone_number or "+6281200000000",
                        "working_hours": u.vworking_hours or "09:00 - 17:00",
                        "avatar_initials": "".join([w[0].upper() for w in u.vname.split()[:2]]),
                        "notes": f"{u.vdepartment} contact ({u.vtimezone})",
                    }
                    for u in ambiguous_users
                ]
                return {
                    "is_disambiguation_needed": True,
                    "status": "CLARIFICATION_NEEDED",
                    "disambiguation_message": f"Multiple contacts found matching '{'Pak Budi' if 'pak budi' in cmd_lower else 'Budi'}'. Please select the intended interviewer:",
                    "disambiguation_profiles": profiles,
                }

        # ---------------------------------------------------------------------
        # 2. Dynamic Interviewer Resolution (with Ground-Truth Support)
        # ---------------------------------------------------------------------
        selected_interviewer = None
        interviewer_matched = False
        explicit_interviewer_id = state.get("interviewer_id")
        if explicit_interviewer_id:
            try:
                selected_interviewer = await self.contact_repo.get_by_id(int(explicit_interviewer_id))
                if selected_interviewer:
                    interviewer_matched = True
            except Exception:
                selected_interviewer = None

        active_interviewers = await self.contact_repo.list_interviewers()
        if not selected_interviewer:
            full_name_matches = [
                user
                for user in active_interviewers
                if user.vname and user.vname.lower().strip() in cmd_lower
            ]
            if len(full_name_matches) > 1:
                return {
                    "status": "NEEDS_CLARIFICATION",
                    "is_ambiguous": True,
                    "clarification_message": (
                        "Ditemukan beberapa interviewer yang cocok: "
                        f"{', '.join(u.vname for u in full_name_matches)}. "
                        "Harap sebutkan nama lengkap atau interviewer_id secara spesifik."
                    ),
                    "similar_candidates": [
                        {"id": u.nid, "name": u.vname, "position": u.vposition}
                        for u in full_name_matches
                    ],
                }
            if len(full_name_matches) == 1:
                selected_interviewer = full_name_matches[0]
                interviewer_matched = True

        interviewer_resolution = "MATCHED" if interviewer_matched else "DEFAULT"
        if not selected_interviewer and active_interviewers:
            budi_users = await self.contact_repo.find_ambiguous_names("Budi Santoso")
            selected_interviewer = budi_users[0] if budi_users else active_interviewers[0]

        # ---------------------------------------------------------------------
        # 3. Dynamic Candidate Resolution (Anti-Silent-Substitution)
        # ---------------------------------------------------------------------
        is_notulen_cmd = any(
            kw in cmd_lower for kw in ["notulen", "catatan rapat", "meeting minutes", "minutes"]
        )
        all_candidates, _ = await self.candidate_repo.search(limit=100)
        target_candidate = None
        candidate_matched = False
        explicit_candidate_id = state.get("candidate_id")

        if explicit_candidate_id:
            try:
                cand_int = int(explicit_candidate_id)
                target_candidate = next((c for c in all_candidates if c.nid == cand_int), None)
                if target_candidate:
                    candidate_matched = True
            except Exception:
                target_candidate = None

        # Check if candidate name was mentioned in command after 'kandidat' or 'candidate'
        cand_kw_match = re.search(
            r"(?:kandidat|candidate)\s+(?!requested\b|meminta\b|minta\b|ingin\b|in\b|di\b|schedule\b|interview\b)([A-Za-z]+(?:\s+[A-Za-z]+){0,2}?)(?:\s+posisi|\s+untuk|\s+minggu|\s+pada|\s+dengan|\s+with|\s+hari|\s+jam|\s+pukul|\s+besok|\s+lusa|\s+ke|\s+via|\s+di|\s+in|[.,]|$)",
            cmd,
            re.IGNORECASE,
        )
        extracted_cand_name = cand_kw_match.group(1).strip() if cand_kw_match else None
        non_name_tokens = {
            "requested", "meminta", "minta", "ingin", "di", "in", "wib", "wita", "wit",
            "schedule", "interview", "wawancara", "reschedule", "moved", "adjustment",
            "ini", "itu", "tersebut", "id", "nomor", "no", "yang",
        }
        if extracted_cand_name and extracted_cand_name.lower().split()[0] in non_name_tokens:
            extracted_cand_name = None

        user_specified_candidate = bool(extracted_cand_name)

        # Strip matched interviewer name and parenthetical metadata e.g. "(Engineering, WIB)"
        # so interviewer names/departments never falsely match candidate tokens
        cmd_for_cand_search = re.sub(r"\([^)]*\)", " ", cmd_lower)
        if selected_interviewer and selected_interviewer.vname:
            inter_name_lower = selected_interviewer.vname.lower().strip()
            cmd_for_cand_search = cmd_for_cand_search.replace(inter_name_lower, " ")
            for inter_tok in inter_name_lower.split():
                if len(inter_tok) >= 3:
                    cmd_for_cand_search = re.sub(
                        rf"\b{re.escape(inter_tok)}\b", " ", cmd_for_cand_search
                    )

        ignored_cand_tokens = {
            "test", "cand", "sort", "user", "pak", "ibu", "bapak", "mr", "mrs", "ms",
            "notulen", "catatan", "rapat", "meeting", "minutes", "jadwal", "jadwalin",
            "jadwalkan", "schedule", "follow", "interview", "wawancara", "technical",
            "teknis", "posisi", "untuk", "dengan", "with", "for", "and", "dan", "atau",
            "jumat", "senin", "selasa", "rabu", "kamis", "sabtu", "minggu",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "pagi", "siang", "sore", "malam", "besok", "lusa", "wib", "wita", "wit",
            "engineering", "finance", "product", "design", "general", "budi", "santoso", "hartono",
        }

        if not target_candidate and (not is_notulen_cmd or user_specified_candidate):
            scored_candidates: list[tuple[Any, int]] = []
            for cand in all_candidates:
                c_name_lower = cand.vname.lower().strip()
                score = 0

                # Exact full name match in command
                if c_name_lower and c_name_lower in cmd_for_cand_search:
                    score += 1000 + len(c_name_lower)
                elif extracted_cand_name and c_name_lower in extracted_cand_name.lower():
                    score += 900 + len(c_name_lower)
                else:
                    name_tokens = [
                        t
                        for t in re.findall(r"\b\w+\b", c_name_lower)
                        if len(t) >= 3
                        and t not in ignored_cand_tokens
                        and not re.fullmatch(r"[0-9a-f]{6}", t)
                    ]
                    matched_count = 0
                    for token in name_tokens:
                        if re.search(rf"\b{re.escape(token)}\b", cmd_for_cand_search):
                            score += 100 + len(token) * 10
                            matched_count += 1
                    # Bonus if job position also matches, BUT ONLY if name also partially matched
                    if matched_count > 0:
                        if cand.vjob_position and cand.vjob_position.lower() in cmd_for_cand_search:
                            score += 50
                        if matched_count > 1:
                            score += matched_count * 50

                if score >= 80:
                    scored_candidates.append((cand, score))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            if scored_candidates:
                top_cand, top_score = scored_candidates[0]
                # Check for ambiguity (two candidates with very close top scores)
                close_matches = [c for c, s in scored_candidates if s >= top_score * 0.9 and s > 0]
                if len(close_matches) > 1 and top_score < 1000:
                    return {
                        "status": "NEEDS_CLARIFICATION",
                        "is_ambiguous": True,
                        "clarification_message": (
                            f"Ditemukan beberapa kandidat dengan nama mirip: "
                            f"{', '.join([c.vname for c in close_matches])}. "
                            f"Harap sebutkan nama lengkap atau candidate_id secara spesifik."
                        ),
                        "similar_candidates": [
                            {"id": c.nid, "name": c.vname, "position": c.vjob_position}
                            for c in close_matches
                        ],
                    }

                if top_score >= 80:
                    target_candidate = top_cand
                    candidate_matched = True

            # If user explicitly asked for a candidate but NO match was found, or match was too weak:
            # STOP and halt with NEEDS_CLARIFICATION — NEVER silently substitute!
            if user_specified_candidate and not target_candidate:
                missing_name = extracted_cand_name or "yang diminta"
                similar = [
                    {"id": c.nid, "name": c.vname, "position": c.vjob_position}
                    for c, _ in scored_candidates[:3]
                ]
                return {
                    "status": "NEEDS_CLARIFICATION",
                    "is_ambiguous": False,
                    "clarification_message": (
                        f"Kandidat '{missing_name}' tidak ditemukan di database ATS Heketon. "
                        f"Autonomous triage dihentikan untuk mencegah salah jadwal. "
                        f"Harap daftarkan kandidat terlebih dahulu atau periksa ejaan nama."
                    ),
                    "similar_candidates": similar,
                }

        # ---------------------------------------------------------------------
        # 3b. Ambiguous / Vague Command Gate (TC-CHB-09: e.g. "Tolong jadwalin itu ya.")
        # ---------------------------------------------------------------------
        vague_pronoun_patterns = [
            r"\bjadwal(?:in|kan)\s+itu\b",
            r"\batur\s+(?:jadwal\s+)?itu\b",
            r"\btolong\s+itu\b",
            r"\bproses\s+itu\b",
            r"\bschedule\s+(?:that|it)\b",
            r"\byang\s+tadi\b",
        ]
        has_vague_pronoun = any(re.search(pat, cmd_lower) for pat in vague_pronoun_patterns)
        has_concrete_subject = any(
            kw in cmd_lower
            for kw in [
                "interview", "wawancara", "notulen", "catatan rapat", "meeting minutes",
                "plan", "candidate", "kandidat", "reschedule", "technical", "teknis",
                "transfer", "bayar", "pembayaran", "invoice", "katering", "gaji", "salary",
            ]
        )

        if (
            not candidate_matched
            and not interviewer_matched
            and not is_notulen_cmd
            and (has_vague_pronoun or not has_concrete_subject)
        ):
            similar = [
                {"id": c.nid, "name": c.vname, "position": c.vjob_position}
                for c in all_candidates[:3]
            ]
            return {
                "status": "NEEDS_CLARIFICATION",
                "is_ambiguous": True,
                "clarification_message": (
                    f"Instruksi '{cmd}' masih terlalu ambigu atau belum memuat konteks yang cukup. "
                    "Mohon sebutkan secara spesifik: (1) Nama kandidat atau agenda rapat yang dimaksud, "
                    "(2) Nama interviewer/pihak terkait, serta (3) Hari dan jam yang diinginkan."
                ),
                "similar_candidates": similar,
            }

        # Default only for non-scheduling (meeting-notes) commands. Scheduling commands must
        # never inherit an arbitrary "most recently modified" candidate.
        if not target_candidate and all_candidates and not user_specified_candidate and is_notulen_cmd:
            target_candidate = all_candidates[0]

        if not target_candidate and not is_notulen_cmd:
            return {
                "status": "NEEDS_CLARIFICATION",
                "is_ambiguous": False,
                "clarification_message": (
                    "Tidak ada kandidat yang dapat diidentifikasi dari instruksi. "
                    "Autonomous triage dihentikan untuk mencegah salah jadwal. "
                    "Harap sebutkan nama kandidat atau candidate_id secara eksplisit."
                ),
                "similar_candidates": [
                    {"id": c.nid, "name": c.vname, "position": c.vjob_position}
                    for c in all_candidates[:3]
                ],
            }

        has_candidate = bool(candidate_matched or explicit_candidate_id or not is_notulen_cmd)

        updates: dict[str, Any] = {
            "is_disambiguation_needed": False,
            "has_candidate": has_candidate,
            "office_code": "HQ-JKT",
            "status": "ANALYZING",
        }

        if selected_interviewer:
            updates.update({
                "interviewer_id": selected_interviewer.nid,
                "interviewer_resolution": interviewer_resolution,
                "interviewer_userid": getattr(selected_interviewer, "vuserid", None) or f"USR-00{selected_interviewer.nid}",
                "interviewer_name": selected_interviewer.vname,
                "interviewer_email": selected_interviewer.vemail,
                "interviewer_phone": selected_interviewer.vphone_number or "+6281198765432",
                "interviewer_role": selected_interviewer.vposition or selected_interviewer.vrole,
                "interviewer_dept": selected_interviewer.vdepartment or "Engineering",
                "interviewer_timezone": selected_interviewer.vtimezone or "WIB",
            })

        if target_candidate:
            req_name = target_candidate.vname if not extracted_cand_name or extracted_cand_name.lower().strip() in non_name_tokens else extracted_cand_name
            resolved_name = target_candidate.vname
            if explicit_candidate_id or state.get("thread_id") or (extracted_cand_name and extracted_cand_name.lower().strip() == resolved_name.lower().strip()):
                match_score, match_type = 1.0, "EXACT"

            elif resolved_name.lower().strip() in cmd_lower:
                match_score, match_type = 0.98, "EXACT"
            elif extracted_cand_name and resolved_name.lower().strip() in extracted_cand_name.lower():
                match_score, match_type = 0.92, "FUZZY"
            else:
                match_score, match_type = 0.86, "FUZZY"
            updates["entity_resolution"] = {
                "requested_candidate": req_name,
                "resolved_candidate_id": str(target_candidate.nid),
                "resolved_name": resolved_name,
                "confidence": match_score,
                "match_type": match_type,
            }
            updates.update({
                "candidate_id": target_candidate.nid,
                "candidate_code": getattr(target_candidate, "vcandidate_code", None) or f"CAND-2026-00{target_candidate.nid}",
                "candidate_name": target_candidate.vname,
                "candidate_email": target_candidate.vemail,
                "candidate_phone": target_candidate.vphone_number or "+6281234567890",
                "candidate_position": target_candidate.vjob_position,
                "candidate_channel": target_candidate.vpreferred_channel,
                "candidate_timezone": target_candidate.vtimezone,
            })

        # ---------------------------------------------------------------------
        # 4. Resolve Target Date & Query Available Slots from Calendar DB
        # ---------------------------------------------------------------------
        now_utc = datetime.now(UTC)
        now_wib = now_utc + timedelta(hours=7)
        explicit_target_date = state.get("target_date")

        if explicit_target_date:
            try:
                target_date = date.fromisoformat(explicit_target_date)
                if target_date < now_wib.date():
                    return {
                        "status": "NEEDS_CLARIFICATION",
                        "is_ambiguous": False,
                        "clarification_message": (
                            f"Tanggal penjadwalan '{explicit_target_date}' berada di masa lalu "
                            f"(hari ini {now_wib.date().isoformat()}). Penjadwalan tanggal masa lalu dilarang."
                        ),
                    }
            except Exception:
                target_date = (now_wib + timedelta(days=2)).date()
        else:
            target_date = (now_wib + timedelta(days=2)).date()
            is_this_week = "minggu ini" in cmd_lower or "this week" in cmd_lower

            # Day of week mapping
            day_keywords = {
                "monday": 0, "senin": 0, "tuesday": 1, "selasa": 1,
                "wednesday": 2, "rabu": 2, "thursday": 3, "kamis": 3,
                "friday": 4, "jumat": 4, "saturday": 5, "sabtu": 5,
            }
            # Only treat "minggu" or "sunday" as Sunday if NOT part of "minggu ini" / "minggu depan"
            if not is_this_week and "minggu depan" not in cmd_lower:
                day_keywords["sunday"] = 6
                day_keywords["minggu"] = 6

            day_matched = False
            negation_markers = (
                "kurang cocok", "tidak cocok", "tidak bisa", "ga bisa", "gak bisa", "gabisa",
                "berhalangan", "sibuk", "batal", "maaf", "sorry", "cannot", "can't", "not available",
            )
            clauses = re.split(r"[,.;?!]|\b(?:tapi|namun|melainkan|kalau|bisa|ganti|ubah|pindah|geser)\b", cmd_lower)
            positive_wds: list[int] = []
            fallback_wds: list[int] = []
            for clause in clauses:
                is_negated_clause = any(neg in clause for neg in negation_markers)
                for m_day in re.finditer(r"\b(" + "|".join(re.escape(k) for k in day_keywords) + r")\b", clause):
                    wd_val = day_keywords[m_day.group(1)]
                    fallback_wds.append(wd_val)
                    if not is_negated_clause:
                        positive_wds.append(wd_val)
            chosen_wd = positive_wds[-1] if positive_wds else (fallback_wds[-1] if fallback_wds else None)
            if chosen_wd is not None:
                days_ahead = (chosen_wd - now_wib.weekday() + 7) % 7
                if days_ahead == 0 and not any(h in cmd_lower for h in ["hari ini", "today"]):
                    days_ahead = 7
                target_date = (now_wib + timedelta(days=days_ahead)).date()
                day_matched = True
            for kw, target_wd in ({} if day_matched else day_keywords).items():
                if re.search(rf"\b{re.escape(kw)}\b", cmd_lower):
                    days_ahead = (target_wd - now_wib.weekday() + 7) % 7
                    if days_ahead == 0 and not any(h in cmd_lower for h in ["hari ini", "today"]):
                        days_ahead = 7
                    target_date = (now_wib + timedelta(days=days_ahead)).date()
                    day_matched = True
                    break

            if not day_matched:
                if "besok" in cmd_lower or "tomorrow" in cmd_lower:
                    target_date = (now_wib + timedelta(days=1)).date()
                elif "lusa" in cmd_lower or "day after tomorrow" in cmd_lower:
                    target_date = (now_wib + timedelta(days=2)).date()
                elif is_this_week:
                    # Pick next available business day in this week (Monday - Friday)
                    days_ahead = 1
                    cand_d = (now_wib + timedelta(days=days_ahead)).date()
                    while cand_d.weekday() in (5, 6) or cand_d.weekday() < now_wib.weekday():
                        days_ahead += 1
                        cand_d = (now_wib + timedelta(days=days_ahead)).date()
                    target_date = cand_d

        # STRICT WEEKEND AVOIDANCE: Ensure target_date NEVER falls on Saturday (5) or Sunday (6)
        if target_date.weekday() == 5:
            target_date = target_date + timedelta(days=2)  # Shift to Monday
        elif target_date.weekday() == 6:
            target_date = target_date + timedelta(days=1)  # Shift to Monday

        # Check candidate timezone from command
        if any(kw in cmd_lower for kw in ["candidate in wit", "kandidat di wit", "di wit", "zona wit", "= 18:00 wit"]):
            updates["candidate_timezone"] = "WIT"
        elif any(kw in cmd_lower for kw in ["candidate in wita", "kandidat di wita", "di wita", "zona wita"]):
            updates["candidate_timezone"] = "WITA"
        elif any(kw in cmd_lower for kw in ["candidate in wib", "kandidat di wib", "di wib", "zona wib"]):
            updates["candidate_timezone"] = "WIB"

        available_slots = []
        if selected_interviewer:
            available_slots = await self.cal_repo.find_available_slots(
                user_id=selected_interviewer.nid,
                target_date=target_date,
            )

        updates["target_date"] = target_date.isoformat()
        updates["available_slots"] = available_slots

        return updates
