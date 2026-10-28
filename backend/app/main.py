from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controller import (
    action_plan_router,
    audit_log_router,
    auth_router,
    calendar_matrix_router,
    candidate_router,
    contact_router,
    holiday_router,
    interview_decision_router,
    interview_session_router,
    interview_transcript_router,
    negotiation_thread_router,
    operational_policy_router,
    orchestrator_command_router,
    rubric_router,
    simulator_email_router,
    simulator_whatsapp_router,
    slot_conflict_checker_router,
)
from app.core.AppConfig import settings
from app.db.DatabaseSession import engine
from app.exception import register_exception_handlers

from app.middleware.SystemLogMiddleware import SystemLogMiddleware
from app.controller import system_log_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


TAGS_METADATA = [
    {"name": "Authentication", "description": "Internal user login, JWT tokens, and demo role switching."},
    {"name": "CandidateManagement", "description": "Candidate profile management, ATS codes, and application status."},
    {"name": "ContactsDirectory", "description": "Interviewer contacts directory, department filters, and working profiles."},
    {"name": "NationalHolidays", "description": "National holidays and collective leaves (cuti bersama) calendar."},
    {"name": "OperationalPolicies", "description": "Working hours, Friday prayer blackout policies, and safety thresholds."},
    {"name": "AssessmentRubrics", "description": "Evaluation rubrics, round competencies, and scoring weights."},
    {"name": "OrchestratorCommands", "description": "Natural language command execution, triage dispatch, and scenario presets."},
    {"name": "ActionPlans", "description": "Generated interview action plans, human approval gates, and 60-second undo countdowns."},
    {"name": "NegotiationThreads", "description": "Candidate rescheduling loop, multi-round triage, and WhatsApp/Email message thread logs."},
    {"name": "SimulatorEmail", "description": "Webmail simulator client for interviewer meeting invitations and confirmations."},
    {"name": "SimulatorWhatsApp", "description": "WhatsApp chat simulator for candidate negotiation threads and quick presets."},
    {"name": "InterviewSessions", "description": "Interview audio recordings, pipeline status, and session summaries."},
    {"name": "InterviewTranscripts", "description": "Audio transcription segments, quote citations, and confidence scores."},
    {"name": "InterviewDecisions", "description": "Final HR decision gates (ADVANCE / HOLD / REJECT) with permanent audit stamping."},
    {"name": "CalendarMatrix", "description": "Interviewer calendar matrix and cross-timezone slot availability."},
    {"name": "SlotConflictChecker", "description": "Pre-flight slot conflict detection, prayer blackout checks, and 15-minute buffer enforcement."},
    {"name": "AuditLogs", "description": "Immutable SHA-256 hash-chained system audit logs and chain-of-custody tracking."},
    {"name": "SystemLogs", "description": "Technical system access, error stacktraces, and mutation logs."} 
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(SystemLogMiddleware) 
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register uniform global exception handlers
register_exception_handlers(app)


# Health endpoint (root)
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}


# Mount all 18 modular API v1 domain routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(candidate_router, prefix=settings.API_V1_STR)
app.include_router(contact_router, prefix=settings.API_V1_STR)
app.include_router(holiday_router, prefix=settings.API_V1_STR)
app.include_router(operational_policy_router, prefix=settings.API_V1_STR)
app.include_router(rubric_router, prefix=settings.API_V1_STR)
app.include_router(orchestrator_command_router, prefix=settings.API_V1_STR)
app.include_router(action_plan_router, prefix=settings.API_V1_STR)
app.include_router(negotiation_thread_router, prefix=settings.API_V1_STR)
app.include_router(simulator_email_router, prefix=settings.API_V1_STR)
app.include_router(simulator_whatsapp_router, prefix=settings.API_V1_STR)
app.include_router(interview_session_router, prefix=settings.API_V1_STR)
app.include_router(interview_transcript_router, prefix=settings.API_V1_STR)
app.include_router(interview_decision_router, prefix=settings.API_V1_STR)
app.include_router(calendar_matrix_router, prefix=settings.API_V1_STR)
app.include_router(slot_conflict_checker_router, prefix=settings.API_V1_STR)
app.include_router(audit_log_router, prefix=settings.API_V1_STR)
app.include_router(system_log_router, prefix=settings.API_V1_STR)
