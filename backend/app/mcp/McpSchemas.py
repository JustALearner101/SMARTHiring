from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class McpCallerContext(BaseModel):
    """Caller context resolved from headers or override arguments."""

    actor_id: str
    role: str
    client_name: str = "WorkBuddyAI"


class CandidateProfileResponse(BaseModel):
    """Output schema for get_candidate_profile tool."""

    id: str
    name: str
    position: str
    email: str | None = None
    phone: str | None = None
    timezone: str = "WIB"
    expected_salary: str = "[CONFIDENTIAL_SALARY_LOCKED]"
    caller_role: str


class ContactSearchItem(BaseModel):
    id: str
    name: str
    employee_id: str
    role: str
    department: str
    timezone: str
    email: str
    phone: str | None = None
    working_hours: str


class ContactSearchResponse(BaseModel):
    """Output schema for search_contacts tool."""

    query: str
    total: int
    is_ambiguous: bool
    ambiguity_message: str | None = None
    contacts: list[ContactSearchItem] = Field(default_factory=list)


class OperationalRulesMcpResponse(BaseModel):
    """Output schema for get_operational_rules tool."""

    working_hours: str
    friday_prayer_blackout: str
    weekend_blackout: str
    buffer_minutes: int
    max_negotiation_rounds: int
    supported_timezones: list[str] = Field(default_factory=list)
    rules: list[dict[str, str]] = Field(default_factory=list)


class NationalHolidayItem(BaseModel):
    date: str
    name: str
    type: str
    rule_code: str = "RULE_NATIONAL_HOLIDAY"


class NationalHolidaysMcpResponse(BaseModel):
    """Output schema for list_national_holidays tool."""

    year: int
    total: int
    holidays: list[NationalHolidayItem] = Field(default_factory=list)


class SlotConflictCheckMcpResponse(BaseModel):
    """Output schema for check_slot_conflict tool."""

    is_available: bool
    status: str
    message: str
    rule_code: str | None = None
    conflicting_event: str | None = None
    suggested_alternatives: list[str] = Field(default_factory=list)
    suggested_alternative_slots: list[dict[str, Any]] = Field(default_factory=list)
    calculated_end_time: str | None = None
    calculated_end_utc: str | None = None


class AuditChainVerificationMcpResponse(BaseModel):
    """Output schema for verify_audit_chain tool."""

    is_valid: bool
    total_blocks: int
    head_hash: str
    verified_at: str


class ActionPlanApprovalMcpResponse(BaseModel):
    """Output schema for approve_action_plan tool."""

    plan_id: str
    status: str
    approval_ticket: str
    approved_by: str
    approved_at: str
    undo_buffer_seconds: int = 60
    is_high_impact: bool = True
    executed_actions_count: int


class ActionPlanUndoMcpResponse(BaseModel):
    """Output schema for undo_action_plan tool."""

    plan_id: str
    status: str
    reverted_at: str
    reverted_by: str
    reason: str
    audit_event_logged: bool = True


class ActionPlanRejectMcpResponse(BaseModel):
    """Output schema for reject_action_plan tool."""

    plan_id: str
    status: str
    rejected_at: str
    rejected_by: str
    reason: str


class InterviewDecisionMcpResponse(BaseModel):
    """Output schema for record_interview_decision tool."""

    session_id: str
    candidate_id: str
    role_evaluated_by: str
    decision_status: str
    interviewer_recommendation: str | None = None
    hr_final_decision: str | None = None
    salary_lock_status: str = "LOCKED_FINANCIAL_CONFIDENTIAL"
