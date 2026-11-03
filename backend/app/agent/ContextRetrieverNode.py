import re
from datetime import UTC, datetime, timedelta
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

        # 1. Disambiguation Check for Interviewer
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

        # 2. Dynamic Interviewer Resolution
        active_interviewers = await self.contact_repo.list_interviewers()
        selected_interviewer = None

        if "hartono" in cmd_lower or "finance" in cmd_lower:
            cand_users = await self.contact_repo.find_ambiguous_names("Budi Hartono")
            selected_interviewer = cand_users[0] if cand_users else None
        elif "santoso" in cmd_lower or "engineering" in cmd_lower:
            cand_users = await self.contact_repo.find_ambiguous_names("Budi Santoso")
            selected_interviewer = cand_users[0] if cand_users else None
        else:
            best_inter_score = 0
            for user in active_interviewers:
                u_name_lower = user.vname.lower().strip()
                score = 0
                if u_name_lower in cmd_lower:
                    score += 1000 + len(u_name_lower)
                else:
                    name_tokens = [t for t in re.findall(r"\b\w+\b", u_name_lower) if len(t) >= 3]
                    for token in name_tokens:
                        if re.search(rf"\b{re.escape(token)}\b", cmd_lower):
                            score += len(token) * 10
                if score > best_inter_score:
                    best_inter_score = score
                    selected_interviewer = user

        if not selected_interviewer and active_interviewers:
            budi_users = await self.contact_repo.find_ambiguous_names("Budi Santoso")
            selected_interviewer = budi_users[0] if budi_users else active_interviewers[0]

        # 3. Dynamic Candidate Resolution
        all_candidates, _ = await self.candidate_repo.search(limit=100)
        target_candidate = None
        best_cand_score = 0

        for cand in all_candidates:
            c_name_lower = cand.vname.lower().strip()
            score = 0

            # Exact full name match in command
            if c_name_lower in cmd_lower:
                score += 1000 + len(c_name_lower)
            else:
                name_tokens = [t for t in re.findall(r"\b\w+\b", c_name_lower) if len(t) >= 3]
                matched_count = 0
                for token in name_tokens:
                    if re.search(rf"\b{re.escape(token)}\b", cmd_lower):
                        score += len(token) * 10
                        matched_count += 1
                if matched_count > 1:
                    score += matched_count * 50

            if score > best_cand_score:
                best_cand_score = score
                target_candidate = cand

        if not target_candidate and all_candidates:
            target_candidate = all_candidates[0]

        updates: dict[str, Any] = {
            "is_disambiguation_needed": False,
            "status": "ANALYZING",
        }

        if selected_interviewer:
            updates.update({
                "interviewer_id": selected_interviewer.nid,
                "interviewer_name": selected_interviewer.vname,
                "interviewer_email": selected_interviewer.vemail,
                "interviewer_phone": selected_interviewer.vphone_number or "+6281198765432",
                "interviewer_role": selected_interviewer.vposition or selected_interviewer.vrole,
                "interviewer_dept": selected_interviewer.vdepartment or "Engineering",
                "interviewer_timezone": selected_interviewer.vtimezone or "WIB",
            })

        if target_candidate:
            updates.update({
                "candidate_id": target_candidate.nid,
                "candidate_name": target_candidate.vname,
                "candidate_email": target_candidate.vemail,
                "candidate_phone": target_candidate.vphone_number or "+6281234567890",
                "candidate_position": target_candidate.vjob_position,
                "candidate_channel": target_candidate.vpreferred_channel,
                "candidate_timezone": target_candidate.vtimezone,
            })

        # 4. Resolve Target Date & Query Available Slots from Calendar DB
        # Reference local Indonesian time (WIB = UTC+7) to avoid off-by-one day calculation
        now_utc = datetime.now(UTC)
        now_wib = now_utc + timedelta(hours=7)
        target_date = (now_wib + timedelta(days=2)).date()
        day_explicitly_requested = False

        day_keywords = {
            "monday": 0, "senin": 0, "tuesday": 1, "selasa": 1,
            "wednesday": 2, "rabu": 2, "thursday": 3, "kamis": 3,
            "friday": 4, "jumat": 4, "saturday": 5, "sabtu": 5,
            "sunday": 6, "minggu": 6,
        }
        for kw, target_wd in day_keywords.items():
            if kw in cmd_lower:
                day_explicitly_requested = True
                days_ahead = (target_wd - now_wib.weekday() + 7) % 7
                if days_ahead == 0 and not any(h in cmd_lower for h in ["hari ini", "today"]):
                    days_ahead = 7
                target_date = (now_wib + timedelta(days=days_ahead)).date()
                break

        if "besok" in cmd_lower or "tomorrow" in cmd_lower:
            day_explicitly_requested = True
            target_date = (now_wib + timedelta(days=1)).date()
        elif "lusa" in cmd_lower or "day after tomorrow" in cmd_lower:
            day_explicitly_requested = True
            target_date = (now_wib + timedelta(days=2)).date()

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
                duration_minutes=60,
                timezone_str=selected_interviewer.vtimezone or "WIB",
            )
            # Only search next day if day was NOT explicitly requested and no slots found
            if not available_slots and not day_explicitly_requested:
                next_day = target_date + timedelta(days=1)
                available_slots = await self.cal_repo.find_available_slots(
                    user_id=selected_interviewer.nid,
                    target_date=next_day,
                    duration_minutes=60,
                    timezone_str=selected_interviewer.vtimezone or "WIB",
                )

        updates["target_date_hint"] = target_date.isoformat()
        updates["available_slots"] = available_slots

        return updates
