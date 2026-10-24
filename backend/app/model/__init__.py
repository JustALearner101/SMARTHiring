"""SQLAlchemy ORM domain models for Interview Copilot (19 tables)."""

from app.model.audit import AuditLog, SystemLog
from app.model.base import (
    AppendOnlyBaseModel,
    AppendOnlyMixin,
    AuditMixin,
    Base,
    BaseModel,
    TableBaseModel,
)
from app.model.calendar import Holiday, WorkCalendar
from app.model.candidate import Candidate
from app.model.followup import ActionRecipient, FollowupPlan
from app.model.interview import Interview, SourceFile
from app.model.job import Job, TranscriptSegment
from app.model.rubric import Competency, Profile
from app.model.summary import Flag, HrDecision, SummaryEvidence, SummaryPoint
from app.model.user import Permission, User

__all__ = [
    "ActionRecipient",
    "AppendOnlyBaseModel",
    "AppendOnlyMixin",
    # 7. Audit & System Logs
    "AuditLog",
    "AuditMixin",
    "Base",
    "BaseModel",
    "Candidate",
    "Competency",
    "Flag",
    # 6. Follow-up Action Plan
    "FollowupPlan",
    "Holiday",
    "HrDecision",
    # 4. Interview & Processing
    "Interview",
    "Job",
    "Permission",
    # 2. Rubric
    "Profile",
    "SourceFile",
    "SummaryEvidence",
    # 5. Summary, Evidence & Review
    "SummaryPoint",
    "SystemLog",
    "TableBaseModel",
    "TranscriptSegment",
    # 1. User, Candidate, Permission
    "User",
    # 3. Calendar
    "WorkCalendar",
]
