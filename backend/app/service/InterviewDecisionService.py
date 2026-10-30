from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.CandidateDTO import ApplicationStatus
from app.dto.InterviewDecisionDTO import (
    AdvanceNextStage,
    DecisionActorRole,
    DecisionWorkflowStatus,
    HrDecisionDTO,
    HrDecisionRequestDTO,
)
from app.exception.CustomException import ForbiddenException, NotFoundException
from app.model.SummaryModel import HrDecision
from app.model.UserModel import User
from app.repository.InterviewDecisionRepository import InterviewDecisionRepository
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.service.AuditLogService import AuditLogService


class InterviewDecisionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.interview_repo = InterviewSessionRepository(session)
        self.decision_repo = InterviewDecisionRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _resolve_transition(
        decision: str,
        next_stage: AdvanceNextStage | None,
        profile_code: str | None,
    ) -> tuple[AdvanceNextStage | None, ApplicationStatus]:
        if decision == "REJECT":
            return None, "REJECTED"
        if decision == "HOLD":
            return None, "COMPLETED"

        resolved_stage: AdvanceNextStage
        if next_stage is not None:
            resolved_stage = next_stage
        elif profile_code and "HR" in profile_code.upper():
            resolved_stage = "NEXT_INTERVIEW"
        else:
            resolved_stage = "OFFERED"

        stage_to_status: dict[AdvanceNextStage, ApplicationStatus] = {
            "NEXT_INTERVIEW": "ESCALATED",
            "TECHNICAL_TEST": "TECHNICAL_TEST",
            "OFFERED": "OFFERED",
        }
        return resolved_stage, stage_to_status[resolved_stage]

    async def save_hr_decision(
        self,
        interview_id: str,
        dto: HrDecisionRequestDTO,
        current_user: User,
    ) -> HrDecisionDTO:
        if not interview_id.isdigit():
            raise NotFoundException(f"Interview session {interview_id} not found.")
        int_id = int(interview_id)
        interview = await self.interview_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files:
            raise NotFoundException(f"Interview job {interview_id} has not completed processing.")

        sorted_sfs = sorted(interview.source_files, key=lambda sf: sf.nid)
        if not sorted_sfs[-1].jobs:
            raise NotFoundException(f"Interview job {interview_id} has not completed processing.")

        sorted_jobs = sorted(sorted_sfs[-1].jobs, key=lambda jb: jb.nid)
        job = sorted_jobs[-1]
        existing_decisions = sorted(
            getattr(job, "hr_decisions", []) or [],
            key=lambda item: (item.ddecided_at, item.nid),
        )
        latest_decision = existing_decisions[-1] if existing_decisions else None

        # Guard 1: Anti-IDOR — INTERVIEWER can ONLY evaluate sessions assigned to them
        if current_user.vrole == "INTERVIEWER" and interview.nid_interviewer != current_user.nid:
            await self.audit_service.log_event(
                event_type="UNAUTHORIZED_INTERVIEW_ACCESS_BLOCKED",
                actor=current_user.vname,
                actor_type="HUMAN",
                title="Cross-Interviewer Decision Tampering Blocked",
                description=(
                    f"Interviewer '{current_user.vname}' (ID #{current_user.nid}) blocked while attempting to submit "
                    f"decision for session #{int_id} owned by interviewer ID #{interview.nid_interviewer}."
                ),
                metadata={
                    "interview_id": int_id,
                    "attempted_by_user_id": current_user.nid,
                    "owner_interviewer_id": interview.nid_interviewer,
                },
                job_id=job.nid,
            )
            raise ForbiddenException(
                "Access denied: You are not authorized to submit decisions for another user's interview session."
            )

        # Guard 2: Immutable Finalized Lock — Once FINALIZED, nobody can overwrite
        if latest_decision and latest_decision.vworkflow_status == "FINALIZED":
            raise ForbiddenException(
                "This interview decision has been permanently finalized and cannot be modified."
            )

        # Guard 3: Interviewer One-Way Lock — Once Interviewer submits recommendation, it is locked for Interviewer
        if current_user.vrole == "INTERVIEWER" and latest_decision is not None:
            raise ForbiddenException(
                "Your evaluation recommendation has already been submitted to HR for followup and is permanently locked."
            )

        # Guard 4: Wait for Assigned Technical/User Interviewer before HR Finalizes
        assigned_interviewer = getattr(interview, "interviewer", None)
        if (
            current_user.vrole in ("HR", "ADMIN")
            and latest_decision is None
            and interview.nid_interviewer is not None
            and assigned_interviewer is not None
            and assigned_interviewer.vrole == "INTERVIEWER"
        ):
            raise ForbiddenException(
                f"This session is assigned to interviewer '{assigned_interviewer.vname}'. "
                "Awaiting evaluation recommendation from assigned interviewer first."
            )

        now = datetime.now(UTC)
        profile_code = interview.profile.vcode if getattr(interview, "profile", None) else None

        resolved_stage, target_hr_status = self._resolve_transition(
            decision=dto.decision,
            next_stage=dto.next_stage,
            profile_code=profile_code,
        )

        actor_role: DecisionActorRole
        workflow_status: DecisionWorkflowStatus
        resulting_candidate_status: ApplicationStatus

        if current_user.vrole == "INTERVIEWER":
            actor_role = "INTERVIEWER"
            workflow_status = "PENDING_HR_FOLLOWUP"
            resulting_candidate_status = "PENDING_HR_REVIEW"
            event_type = "INTERVIEWER_RECOMMENDATION_SUBMITTED"
            stage_suffix = f" ({resolved_stage})" if resolved_stage else ""
            audit_title = f"Interviewer Recommendation: {dto.decision}{stage_suffix}"
            audit_desc = (
                f"Interviewer '{current_user.vname}' submitted evaluation recommendation for candidate "
                f"#{interview.nid_candidate} on session #{int_id}: {dto.decision}{stage_suffix} -> "
                f"Forwarded to HR followup queue ({resulting_candidate_status}). Notes: {dto.notes}"
            )
        else:
            actor_role = "HR"
            workflow_status = "FINALIZED"
            resulting_candidate_status = target_hr_status
            event_type = "HR_DECISION_FINALIZED"
            stage_suffix = f" ({resolved_stage})" if resolved_stage else ""
            audit_title = f"HR Final Decision: {dto.decision}{stage_suffix}"
            audit_desc = (
                f"HR final decision by '{current_user.vname}' for candidate #{interview.nid_candidate} "
                f"on session #{int_id}: {dto.decision}{stage_suffix} -> Candidate status officially set to "
                f"{resulting_candidate_status}. Notes: {dto.notes}"
            )

        dec = HrDecision(
            nid_job=job.nid,
            vdecision="PROCEED" if dto.decision == "ADVANCE" else dto.decision,
            vnext_stage=resolved_stage,
            vactor_role=actor_role,
            vworkflow_status=workflow_status,
            vnote=dto.notes,
            nid_decided_by=current_user.nid,
            ddecided_at=now,
        )
        self.session.add(dec)

        interview.dmodi = now
        self.session.add(interview)

        if interview.candidate:
            cand = interview.candidate
            cand.vstatus = resulting_candidate_status
            cand.dmodi = now
            self.session.add(cand)

        await self.session.commit()
        await self.session.refresh(dec)

        await self.audit_service.log_event(
            event_type=event_type,
            actor=current_user.vname,
            actor_type="HUMAN",
            title=audit_title,
            description=audit_desc,
            metadata={
                "interview_id": int_id,
                "decision": dto.decision,
                "next_stage": resolved_stage,
                "actor_role": actor_role,
                "workflow_status": workflow_status,
                "resulting_candidate_status": resulting_candidate_status,
                "decided_by_user_id": current_user.nid,
                "job_id": job.nid,
            },
            job_id=job.nid,
        )

        return HrDecisionDTO(
            decision=dto.decision,
            next_stage=resolved_stage,
            resulting_candidate_status=resulting_candidate_status,
            actor_role=actor_role,
            workflow_status=workflow_status,
            notes=dto.notes,
            decided_at=now.isoformat(),
            decided_by=current_user.vname,
            decided_by_user_id=str(current_user.nid),
        )
