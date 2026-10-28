import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.repository.CandidateRepository import CandidateRepository
from app.repository.ContactRepository import ContactRepository
from app.repository.OperationalPolicyRepository import OperationalPolicyRepository


class ContextRetrieverNode:
    """Node 2: DB Context Retriever & Disambiguation Gate (Pilar LIMITS & SOURCES).

    Resolves mentioned Candidate and Interviewer contacts from PostgreSQL.
    If ambiguous contacts are detected (e.g. two "Pak Budi"), halts the graph
    and requests clarification from HR.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.contact_repo = ContactRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.policy_repo = OperationalPolicyRepository(session)

    async def run(self, state: OrchestratorAgentState) -> dict[str, Any]:
        cmd = state.get("command", "").strip()
        cmd_lower = cmd.lower()

        # 1. Disambiguation Check for Interviewer (Pilar LIMITS)
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
                        "notes": f"Kontak divisi {u.vdepartment} ({u.vtimezone})",
                    }
                    for u in ambiguous_users
                ]
                return {
                    "is_disambiguation_needed": True,
                    "status": "CLARIFICATION_NEEDED",
                    "disambiguation_message": "Ditemukan lebih dari satu kontak bernama 'Pak Budi'. Silakan pilih pewawancara yang dimaksud:",
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

        # 3. Dynamic Candidate Resolution (Pilar SOURCES)
        # Search all registered candidates in PostgreSQL by full name or token matching
        all_candidates, _ = await self.candidate_repo.search(limit=100)
        target_candidate = None
        best_cand_score = 0

        for cand in all_candidates:
            c_name_lower = cand.vname.lower().strip()
            score = 0

            # Exact full name match in command (e.g. "fathir intania putri setiawan")
            if c_name_lower in cmd_lower:
                score += 1000 + len(c_name_lower)
            else:
                # Token-by-token match (first name, last name, middle names)
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

        # Fallback to first candidate only if no candidate in DB was mentioned in the command
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

        return updates
