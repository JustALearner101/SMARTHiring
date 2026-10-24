"""create interview copilot schema v2

Revision ID: 20261023_0001
Revises: 
Create Date: 2026-10-23 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20261023_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. tblm_profile
    op.create_table(
        'tblm_profile',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vcode', sa.String(length=50), nullable=False),
        sa.Column('vname', sa.String(length=255), nullable=False),
        sa.Column('vversion_no', sa.String(length=50), nullable=False),
        sa.Column('vsummary_format', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_profile')),
        sa.UniqueConstraint('vcode', 'vversion_no', name='uq_tblm_profile_code_version')
    )
    op.create_index(op.f('ix_tblm_profile_nid'), 'tblm_profile', ['nid'], unique=False)
    op.create_index(op.f('ix_tblm_profile_vcode'), 'tblm_profile', ['vcode'], unique=False)

    # 2. tblm_competency
    op.create_table(
        'tblm_competency',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vvisibility_class', sa.String(length=50), nullable=False),
        sa.Column('vcode', sa.String(length=50), nullable=False),
        sa.Column('vname', sa.String(length=255), nullable=False),
        sa.Column('nsort_order', sa.Integer(), nullable=False),
        sa.Column('vreference_question', sa.Text(), nullable=True),
        sa.Column('nid_profile', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "vvisibility_class IN ('GENERAL', 'HR_ONLY', 'SALARY', 'SENSITIVE_FLAG', 'AUDIT_LOG')",
            name='ck_tblm_competency_vvisibility_class'
        ),
        sa.ForeignKeyConstraint(['nid_profile'], ['tblm_profile.nid'], name=op.f('fk_tblm_competency_nid_profile_tblm_profile'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_competency')),
        sa.UniqueConstraint('nid_profile', 'vcode', name='uq_tblm_competency_profile_code')
    )
    op.create_index(op.f('ix_tblm_competency_nid'), 'tblm_competency', ['nid'], unique=False)
    op.create_index(op.f('ix_tblm_competency_nid_profile'), 'tblm_competency', ['nid_profile'], unique=False)

    # 3. tblm_user
    op.create_table(
        'tblm_user',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vuserid', sa.String(length=50), nullable=False),
        sa.Column('vname', sa.String(length=255), nullable=False),
        sa.Column('vusername', sa.String(length=100), nullable=False),
        sa.Column('vemail', sa.String(length=255), nullable=False),
        sa.Column('vpassword_hash', sa.String(length=255), nullable=False),
        sa.Column('vposition', sa.String(length=100), nullable=True),
        sa.Column('vdepartment', sa.String(length=100), nullable=True),
        sa.Column('vrole', sa.String(length=50), nullable=False),
        sa.Column('vtimezone', sa.String(length=10), nullable=False),
        sa.Column('vstatus', sa.String(length=20), nullable=False),
        sa.Column('vuser_token', sa.String(length=500), nullable=True),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')", name='ck_tblm_user_vrole'),
        sa.CheckConstraint("vstatus IN ('ACTIVE', 'INACTIVE')", name='ck_tblm_user_vstatus'),
        sa.CheckConstraint("vtimezone IN ('WIB', 'WITA', 'WIT')", name='ck_tblm_user_vtimezone'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_user')),
        sa.UniqueConstraint('vemail', name=op.f('uq_tblm_user_vemail')),
        sa.UniqueConstraint('vuserid', name=op.f('uq_tblm_user_vuserid')),
        sa.UniqueConstraint('vusername', name=op.f('uq_tblm_user_vusername'))
    )
    op.create_index(op.f('ix_tblm_user_nid'), 'tblm_user', ['nid'], unique=False)
    op.create_index(op.f('ix_tblm_user_vemail'), 'tblm_user', ['vemail'], unique=True)
    op.create_index(op.f('ix_tblm_user_vuserid'), 'tblm_user', ['vuserid'], unique=True)
    op.create_index(op.f('ix_tblm_user_vusername'), 'tblm_user', ['vusername'], unique=True)

    # 4. tblm_permission
    op.create_table(
        'tblm_permission',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vrole', sa.String(length=50), nullable=False),
        sa.Column('vvisibility_class', sa.String(length=50), nullable=False),
        sa.Column('vaccess_level', sa.String(length=20), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vaccess_level IN ('READ', 'WRITE', 'NONE')", name='ck_tblm_permission_vaccess_level'),
        sa.CheckConstraint("vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')", name='ck_tblm_permission_vrole'),
        sa.CheckConstraint("vvisibility_class IN ('GENERAL', 'HR_ONLY', 'SALARY', 'SENSITIVE_FLAG', 'AUDIT_LOG')", name='ck_tblm_permission_vvisibility_class'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_permission')),
        sa.UniqueConstraint('vrole', 'vvisibility_class', name='uq_tblm_permission_role_visibility')
    )
    op.create_index(op.f('ix_tblm_permission_nid'), 'tblm_permission', ['nid'], unique=False)

    # 5. tblm_candidate
    op.create_table(
        'tblm_candidate',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vcandidate_code', sa.String(length=50), nullable=False),
        sa.Column('vname', sa.String(length=255), nullable=False),
        sa.Column('vemail', sa.String(length=255), nullable=False),
        sa.Column('vphone_number', sa.String(length=50), nullable=False),
        sa.Column('vjob_position', sa.String(length=100), nullable=False),
        sa.Column('ncurrent_salary', sa.BigInteger(), nullable=True),
        sa.Column('nexpected_salary', sa.BigInteger(), nullable=True),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_candidate')),
        sa.UniqueConstraint('vcandidate_code', name=op.f('uq_tblm_candidate_vcandidate_code'))
    )
    op.create_index(op.f('ix_tblm_candidate_nid'), 'tblm_candidate', ['nid'], unique=False)
    op.create_index(op.f('ix_tblm_candidate_vcandidate_code'), 'tblm_candidate', ['vcandidate_code'], unique=True)

    # 6. tblm_work_calendar
    op.create_table(
        'tblm_work_calendar',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('voffice_code', sa.String(length=50), nullable=False),
        sa.Column('vtimezone', sa.String(length=10), nullable=False),
        sa.Column('twork_start', sa.Time(), nullable=False),
        sa.Column('twork_end', sa.Time(), nullable=False),
        sa.Column('tfriday_prayer_start', sa.Time(), nullable=False),
        sa.Column('tfriday_prayer_end', sa.Time(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vtimezone IN ('WIB', 'WITA', 'WIT')", name='ck_tblm_work_calendar_vtimezone'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_work_calendar')),
        sa.UniqueConstraint('voffice_code', name=op.f('uq_tblm_work_calendar_voffice_code'))
    )
    op.create_index(op.f('ix_tblm_work_calendar_nid'), 'tblm_work_calendar', ['nid'], unique=False)
    op.create_index(op.f('ix_tblm_work_calendar_voffice_code'), 'tblm_work_calendar', ['voffice_code'], unique=True)

    # 7. tblm_holiday
    op.create_table(
        'tblm_holiday',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dholiday_date', sa.Date(), nullable=False),
        sa.Column('vname', sa.String(length=255), nullable=False),
        sa.Column('vtype', sa.String(length=50), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vtype IN ('NATIONAL_HOLIDAY', 'COLLECTIVE_LEAVE')", name='ck_tblm_holiday_vtype'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblm_holiday')),
        sa.UniqueConstraint('dholiday_date', name=op.f('uq_tblm_holiday_dholiday_date'))
    )
    op.create_index(op.f('ix_tblm_holiday_dholiday_date'), 'tblm_holiday', ['dholiday_date'], unique=True)
    op.create_index(op.f('ix_tblm_holiday_nid'), 'tblm_holiday', ['nid'], unique=False)

    # 8. tblt_interview
    op.create_table(
        'tblt_interview',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vconsent_status', sa.String(length=50), nullable=False),
        sa.Column('dconsent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vconsent_notice_version', sa.String(length=50), nullable=True),
        sa.Column('nid_profile', sa.BigInteger(), nullable=False),
        sa.Column('nid_candidate', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vconsent_status IN ('GRANTED', 'NOT_GRANTED', 'WITHDRAWN')", name='ck_tblt_interview_vconsent_status'),
        sa.ForeignKeyConstraint(['nid_candidate'], ['tblm_candidate.nid'], name=op.f('fk_tblt_interview_nid_candidate_tblm_candidate'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_profile'], ['tblm_profile.nid'], name=op.f('fk_tblt_interview_nid_profile_tblm_profile'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_interview'))
    )
    op.create_index(op.f('ix_tblt_interview_nid'), 'tblt_interview', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_interview_nid_candidate'), 'tblt_interview', ['nid_candidate'], unique=False)
    op.create_index(op.f('ix_tblt_interview_nid_profile'), 'tblt_interview', ['nid_profile'], unique=False)

    # 9. tblt_source_file
    op.create_table(
        'tblt_source_file',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vtype', sa.String(length=50), nullable=False),
        sa.Column('vurl', sa.String(length=1000), nullable=False),
        sa.Column('vduration', sa.String(length=50), nullable=True),
        sa.Column('nid_interview', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vtype IN ('AUDIO', 'VIDEO', 'TRANSCRIPT_TEXT', 'MANUAL_NOTE')", name='ck_tblt_source_file_vtype'),
        sa.ForeignKeyConstraint(['nid_interview'], ['tblt_interview.nid'], name=op.f('fk_tblt_source_file_nid_interview_tblt_interview'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_source_file'))
    )
    op.create_index(op.f('ix_tblt_source_file_nid'), 'tblt_source_file', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_source_file_nid_interview'), 'tblt_source_file', ['nid_interview'], unique=False)

    # 10. tblt_job
    op.create_table(
        'tblt_job',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vasr_engine', sa.String(length=100), nullable=True),
        sa.Column('vasr_model_version', sa.String(length=100), nullable=True),
        sa.Column('vlanguage_code', sa.String(length=20), nullable=False),
        sa.Column('nstatus', sa.Integer(), nullable=False),
        sa.Column('nid_source', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('nstatus IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 90, 91, 92, 93)', name='ck_tblt_job_nstatus'),
        sa.ForeignKeyConstraint(['nid_source'], ['tblt_source_file.nid'], name=op.f('fk_tblt_job_nid_source_tblt_source_file'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_job'))
    )
    op.create_index(op.f('ix_tblt_job_nid'), 'tblt_job', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_job_nid_source'), 'tblt_job', ['nid_source'], unique=False)
    op.create_index(op.f('ix_tblt_job_nstatus'), 'tblt_job', ['nstatus'], unique=False)

    # 11. tblt_transcript_segment
    op.create_table(
        'tblt_transcript_segment',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nsegment_no', sa.Integer(), nullable=False),
        sa.Column('nstart_ms', sa.Integer(), nullable=False),
        sa.Column('nend_ms', sa.Integer(), nullable=False),
        sa.Column('vspeaker_label', sa.String(length=50), nullable=True),
        sa.Column('vspeaker_type', sa.String(length=50), nullable=False),
        sa.Column('vtext', sa.Text(), nullable=False),
        sa.Column('fconfidence', sa.Float(), nullable=False),
        sa.Column('nis_uncertain', sa.Integer(), nullable=False),
        sa.Column('nid_job', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('fconfidence >= 0.0 AND fconfidence <= 1.0', name='ck_tblt_transcript_segment_confidence'),
        sa.CheckConstraint('nend_ms >= nstart_ms', name='ck_tblt_transcript_segment_times'),
        sa.CheckConstraint("vspeaker_type IN ('CANDIDATE', 'INTERVIEWER', 'UNKNOWN')", name='ck_tblt_transcript_segment_speaker_type'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_transcript_segment_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_transcript_segment')),
        sa.UniqueConstraint('nid_job', 'nsegment_no', name='uq_tblt_transcript_segment_job_no')
    )
    op.create_index(op.f('ix_tblt_transcript_segment_nid'), 'tblt_transcript_segment', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_transcript_segment_nid_job'), 'tblt_transcript_segment', ['nid_job'], unique=False)
    op.create_index(op.f('ix_tblt_transcript_segment_nstart_ms'), 'tblt_transcript_segment', ['nstart_ms'], unique=False)

    # 12. tblt_summary_point
    op.create_table(
        'tblt_summary_point',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vcoverage_status', sa.String(length=50), nullable=False),
        sa.Column('vcontent', sa.Text(), nullable=False),
        sa.Column('vverification_status', sa.String(length=50), nullable=False),
        sa.Column('nid_competency', sa.BigInteger(), nullable=False),
        sa.Column('nid_job', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vcoverage_status IN ('COVERED', 'PARTIAL', 'NOT_DISCUSSED')", name='ck_tblt_summary_point_coverage'),
        sa.CheckConstraint("vverification_status IN ('VERIFIED', 'UNVERIFIED', 'NOT_APPLICABLE')", name='ck_tblt_summary_point_verification'),
        sa.ForeignKeyConstraint(['nid_competency'], ['tblm_competency.nid'], name=op.f('fk_tblt_summary_point_nid_competency_tblm_competency'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_summary_point_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_summary_point'))
    )
    op.create_index(op.f('ix_tblt_summary_point_nid'), 'tblt_summary_point', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_summary_point_nid_competency'), 'tblt_summary_point', ['nid_competency'], unique=False)
    op.create_index(op.f('ix_tblt_summary_point_nid_job'), 'tblt_summary_point', ['nid_job'], unique=False)

    # 13. tblt_summary_evidence
    op.create_table(
        'tblt_summary_evidence',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vquote', sa.Text(), nullable=False),
        sa.Column('nid_transcript', sa.BigInteger(), nullable=False),
        sa.Column('nid_summary_point', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['nid_summary_point'], ['tblt_summary_point.nid'], name=op.f('fk_tblt_summary_evidence_nid_summary_point_tblt_summary_point'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_transcript'], ['tblt_transcript_segment.nid'], name=op.f('fk_tblt_summary_evidence_nid_transcript_tblt_transcript_segment'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_summary_evidence'))
    )
    op.create_index(op.f('ix_tblt_summary_evidence_nid'), 'tblt_summary_evidence', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_summary_evidence_nid_summary_point'), 'tblt_summary_evidence', ['nid_summary_point'], unique=False)
    op.create_index(op.f('ix_tblt_summary_evidence_nid_transcript'), 'tblt_summary_evidence', ['nid_transcript'], unique=False)

    # 14. tblt_flag
    op.create_table(
        'tblt_flag',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vflag_type', sa.String(length=50), nullable=False),
        sa.Column('vneutral_text', sa.Text(), nullable=False),
        sa.Column('vstatus', sa.String(length=50), nullable=False),
        sa.Column('nid_job', sa.BigInteger(), nullable=False),
        sa.Column('nid_transcript', sa.BigInteger(), nullable=True),
        sa.Column('nid_reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('dreviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vflag_type IN ('NEEDS_CLARIFICATION', 'SENSITIVE_ATTRIBUTE', 'UNCERTAIN_SEGMENT', 'EMBEDDED_INSTRUCTION')", name='ck_tblt_flag_type'),
        sa.CheckConstraint("vstatus IN ('OPEN', 'REVIEWED')", name='ck_tblt_flag_status'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_flag_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_reviewed_by'], ['tblm_user.nid'], name=op.f('fk_tblt_flag_nid_reviewed_by_tblm_user'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_transcript'], ['tblt_transcript_segment.nid'], name=op.f('fk_tblt_flag_nid_transcript_tblt_transcript_segment'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_flag'))
    )
    op.create_index(op.f('ix_tblt_flag_nid'), 'tblt_flag', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_flag_nid_job'), 'tblt_flag', ['nid_job'], unique=False)
    op.create_index(op.f('ix_tblt_flag_nid_reviewed_by'), 'tblt_flag', ['nid_reviewed_by'], unique=False)
    op.create_index(op.f('ix_tblt_flag_nid_transcript'), 'tblt_flag', ['nid_transcript'], unique=False)

    # 15. tblt_hr_decision
    op.create_table(
        'tblt_hr_decision',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vdecision', sa.String(length=50), nullable=False),
        sa.Column('vnote', sa.Text(), nullable=True),
        sa.Column('vsummary_hash', sa.String(length=255), nullable=True),
        sa.Column('nid_job', sa.BigInteger(), nullable=False),
        sa.Column('nid_decided_by', sa.BigInteger(), nullable=False),
        sa.Column('ddecided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vdecision IN ('PROCEED', 'HOLD', 'REJECT')", name='ck_tblt_hr_decision_val'),
        sa.ForeignKeyConstraint(['nid_decided_by'], ['tblm_user.nid'], name=op.f('fk_tblt_hr_decision_nid_decided_by_tblm_user'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_hr_decision_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_hr_decision'))
    )
    op.create_index(op.f('ix_tblt_hr_decision_nid'), 'tblt_hr_decision', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_hr_decision_nid_decided_by'), 'tblt_hr_decision', ['nid_decided_by'], unique=False)
    op.create_index(op.f('ix_tblt_hr_decision_nid_job'), 'tblt_hr_decision', ['nid_job'], unique=False)

    # 16. tblt_followup_plan
    op.create_table(
        'tblt_followup_plan',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vplan', sa.Text(), nullable=False),
        sa.Column('vaction_type', sa.String(length=50), nullable=False),
        sa.Column('dscheduled_start_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dscheduled_end_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vlocation', sa.String(length=255), nullable=True),
        sa.Column('vimpact_level', sa.String(length=50), nullable=False),
        sa.Column('vapproval_status', sa.String(length=50), nullable=False),
        sa.Column('vplan_hash', sa.String(length=255), nullable=True),
        sa.Column('vapproval_token', sa.String(length=255), nullable=True),
        sa.Column('nid_approved_by', sa.BigInteger(), nullable=True),
        sa.Column('dapproved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vmock_result_id', sa.String(length=100), nullable=True),
        sa.Column('dexecuted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dundo_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('nid_job', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vaction_type IN ('EMAIL', 'CALENDAR', 'TASK')", name='ck_tblt_followup_plan_action_type'),
        sa.CheckConstraint("vapproval_status IN ('DRAFT', 'AWAITING_CLARIFICATION', 'AWAITING_APPROVAL', 'APPROVED', 'REJECTED', 'INVALIDATED', 'EXECUTED', 'UNDONE')", name='ck_tblt_followup_plan_approval_status'),
        sa.CheckConstraint("vapproval_status <> 'EXECUTED' OR vapproval_token IS NOT NULL", name='ck_tblt_followup_plan_execution_token'),
        sa.CheckConstraint("vimpact_level IN ('NORMAL', 'HIGH')", name='ck_tblt_followup_plan_impact_level'),
        sa.CheckConstraint('dscheduled_end_utc IS NULL OR dscheduled_start_utc IS NULL OR dscheduled_end_utc >= dscheduled_start_utc', name='ck_tblt_followup_plan_schedule_times'),
        sa.ForeignKeyConstraint(['nid_approved_by'], ['tblm_user.nid'], name=op.f('fk_tblt_followup_plan_nid_approved_by_tblm_user'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_followup_plan_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_followup_plan'))
    )
    op.create_index(op.f('ix_tblt_followup_plan_nid'), 'tblt_followup_plan', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_followup_plan_nid_approved_by'), 'tblt_followup_plan', ['nid_approved_by'], unique=False)
    op.create_index(op.f('ix_tblt_followup_plan_nid_job'), 'tblt_followup_plan', ['nid_job'], unique=False)
    op.create_index(op.f('ix_tblt_followup_plan_vapproval_status'), 'tblt_followup_plan', ['vapproval_status'], unique=False)

    # 17. tblr_action_recipient
    op.create_table(
        'tblr_action_recipient',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nid_candidate', sa.BigInteger(), nullable=True),
        sa.Column('nid_user', sa.BigInteger(), nullable=True),
        sa.Column('vexternal_email', sa.String(length=255), nullable=True),
        sa.Column('vrecipient_role', sa.String(length=50), nullable=False),
        sa.Column('nid_followup_plan', sa.BigInteger(), nullable=False),
        sa.Column('vcrea', sa.String(length=100), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('vmodi', sa.String(length=100), nullable=True),
        sa.Column('dmodi', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "((CASE WHEN nid_user IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN nid_candidate IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN vexternal_email IS NOT NULL THEN 1 ELSE 0 END)) = 1",
            name='ck_tblr_action_recipient_single_target'
        ),
        sa.CheckConstraint("vrecipient_role IN ('TO', 'CC', 'ATTENDEE')", name='ck_tblr_action_recipient_role'),
        sa.ForeignKeyConstraint(['nid_candidate'], ['tblm_candidate.nid'], name=op.f('fk_tblr_action_recipient_nid_candidate_tblm_candidate'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_followup_plan'], ['tblt_followup_plan.nid'], name=op.f('fk_tblr_action_recipient_nid_followup_plan_tblt_followup_plan'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nid_user'], ['tblm_user.nid'], name=op.f('fk_tblr_action_recipient_nid_user_tblm_user'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblr_action_recipient'))
    )
    op.create_index(op.f('ix_tblr_action_recipient_nid'), 'tblr_action_recipient', ['nid'], unique=False)
    op.create_index(op.f('ix_tblr_action_recipient_nid_candidate'), 'tblr_action_recipient', ['nid_candidate'], unique=False)
    op.create_index(op.f('ix_tblr_action_recipient_nid_followup_plan'), 'tblr_action_recipient', ['nid_followup_plan'], unique=False)
    op.create_index(op.f('ix_tblr_action_recipient_nid_user'), 'tblr_action_recipient', ['nid_user'], unique=False)

    # 18. tblt_audit_log
    op.create_table(
        'tblt_audit_log',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nid_job', sa.BigInteger(), nullable=True),
        sa.Column('vactor_type', sa.String(length=50), nullable=False),
        sa.Column('vactor_id', sa.String(length=100), nullable=False),
        sa.Column('vevent_type', sa.String(length=100), nullable=False),
        sa.Column('vpayload_hash', sa.String(length=255), nullable=False),
        sa.Column('vmasked_detail', sa.Text(), nullable=False),
        sa.Column('vprev_hash', sa.String(length=255), nullable=True),
        sa.Column('vhash', sa.String(length=255), nullable=False),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("vactor_type IN ('ORCHESTRATOR', 'AGENT', 'HUMAN')", name='ck_tblt_audit_log_actor_type'),
        sa.ForeignKeyConstraint(['nid_job'], ['tblt_job.nid'], name=op.f('fk_tblt_audit_log_nid_job_tblt_job'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tblt_audit_log'))
    )
    op.create_index(op.f('ix_tblt_audit_log_nid'), 'tblt_audit_log', ['nid'], unique=False)
    op.create_index(op.f('ix_tblt_audit_log_nid_job'), 'tblt_audit_log', ['nid_job'], unique=False)
    op.create_index(op.f('ix_tblt_audit_log_vevent_type'), 'tblt_audit_log', ['vevent_type'], unique=False)
    op.create_index(op.f('ix_tblt_audit_log_vhash'), 'tblt_audit_log', ['vhash'], unique=False)

    # 19. tbl_log_system
    op.create_table(
        'tbl_log_system',
        sa.Column('nid', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vlog_level', sa.String(length=20), nullable=False),
        sa.Column('vlog_message', sa.Text(), nullable=False),
        sa.Column('vlog_stacktrace', sa.Text(), nullable=True),
        sa.Column('vlog_source', sa.String(length=100), nullable=True),
        sa.Column('vlog_path', sa.String(length=255), nullable=True),
        sa.Column('vlog_method', sa.String(length=20), nullable=True),
        sa.Column('vlog_status_code', sa.String(length=20), nullable=True),
        sa.Column('dcrea', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("vlog_level IN ('INFO', 'WARN', 'ERROR')", name='ck_tbl_log_system_level'),
        sa.PrimaryKeyConstraint('nid', name=op.f('pk_tbl_log_system'))
    )
    op.create_index(op.f('ix_tbl_log_system_nid'), 'tbl_log_system', ['nid'], unique=False)


def downgrade() -> None:
    # Drop in exact reverse order
    op.drop_table('tbl_log_system')
    op.drop_table('tblt_audit_log')
    op.drop_table('tblr_action_recipient')
    op.drop_table('tblt_followup_plan')
    op.drop_table('tblt_hr_decision')
    op.drop_table('tblt_flag')
    op.drop_table('tblt_summary_evidence')
    op.drop_table('tblt_summary_point')
    op.drop_table('tblt_transcript_segment')
    op.drop_table('tblt_job')
    op.drop_table('tblt_source_file')
    op.drop_table('tblt_interview')
    op.drop_table('tblm_holiday')
    op.drop_table('tblm_work_calendar')
    op.drop_table('tblm_candidate')
    op.drop_table('tblm_permission')
    op.drop_table('tblm_user')
    op.drop_table('tblm_competency')
    op.drop_table('tblm_profile')
