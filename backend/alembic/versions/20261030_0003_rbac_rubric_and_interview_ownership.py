"""rbac 3 roles, rubric ownership, and interview two-tier decision handoff

Revision ID: 20261030_0003
Revises: 20261029_0002
Create Date: 2026-10-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261030_0003"
down_revision: str | None = "20261029_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Normalize User & Permission roles -> ('HR', 'ADMIN', 'INTERVIEWER')
    op.execute("ALTER TABLE tblm_user DROP CONSTRAINT IF EXISTS ck_tblm_user_ck_tblm_user_vrole")
    op.execute("ALTER TABLE tblm_user DROP CONSTRAINT IF EXISTS ck_tblm_user_vrole")
    op.execute("ALTER TABLE tblm_permission DROP CONSTRAINT IF EXISTS ck_tblm_permission_ck_tblm_permission_vrole")
    op.execute("ALTER TABLE tblm_permission DROP CONSTRAINT IF EXISTS ck_tblm_permission_vrole")

    op.execute(
        "UPDATE tblm_user SET vrole = 'INTERVIEWER' "
        "WHERE vrole IN ('USER_INTERVIEWER', 'TECH_INTERVIEWER')"
    )
    op.execute("UPDATE tblm_user SET vrole = 'ADMIN' WHERE vrole = 'AUDITOR'")

    op.execute("DELETE FROM tblm_permission WHERE vrole = 'TECH_INTERVIEWER'")
    op.execute("UPDATE tblm_permission SET vrole = 'INTERVIEWER' WHERE vrole = 'USER_INTERVIEWER'")
    op.execute("UPDATE tblm_permission SET vrole = 'ADMIN' WHERE vrole = 'AUDITOR'")

    op.create_check_constraint(
        op.f("ck_tblm_user_ck_tblm_user_vrole"),
        "tblm_user",
        "vrole IN ('HR', 'ADMIN', 'INTERVIEWER')",
    )
    op.create_check_constraint(
        op.f("ck_tblm_permission_ck_tblm_permission_vrole"),
        "tblm_permission",
        "vrole IN ('HR', 'ADMIN', 'INTERVIEWER')",
    )

    # 2. Candidate status: add PENDING_HR_REVIEW
    op.execute("ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_ck_tblm_candidate_vstatus")
    op.execute("ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_vstatus")
    op.create_check_constraint(
        op.f("ck_tblm_candidate_ck_tblm_candidate_vstatus"),
        "tblm_candidate",
        "vstatus IN ('SCREENING', 'ESCALATED', 'INTERVIEW_SCHEDULED', 'PENDING_HR_REVIEW', 'TECHNICAL_TEST', 'COMPLETED', 'OFFERED', 'REJECTED')",
    )

    # 3. Rubric Profile ownership & target role
    op.add_column(
        "tblm_profile",
        sa.Column("vtarget_role", sa.String(length=50), nullable=False, server_default="HR"),
    )
    op.add_column("tblm_profile", sa.Column("vdepartment", sa.String(length=100), nullable=True))
    op.add_column("tblm_profile", sa.Column("nid_owner_user", sa.BigInteger(), nullable=True))
    op.create_index("ix_tblm_profile_nid_owner_user", "tblm_profile", ["nid_owner_user"])
    op.create_foreign_key(
        "fk_tblm_profile_nid_owner_user_tblm_user",
        "tblm_profile",
        "tblm_user",
        ["nid_owner_user"],
        ["nid"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_tblm_profile_target_role",
        "tblm_profile",
        "vtarget_role IN ('HR', 'INTERVIEWER')",
    )

    op.execute(
        "UPDATE tblm_profile SET vtarget_role = 'INTERVIEWER', vdepartment = 'Engineering', "
        "nid_owner_user = (SELECT nid FROM tblm_user WHERE vrole = 'INTERVIEWER' ORDER BY nid ASC LIMIT 1) "
        "WHERE UPPER(vcode) LIKE '%TECH%'"
    )
    op.execute(
        "UPDATE tblm_profile SET vtarget_role = 'HR', vdepartment = 'Human Resources', "
        "nid_owner_user = (SELECT nid FROM tblm_user WHERE vrole = 'HR' ORDER BY nid ASC LIMIT 1) "
        "WHERE UPPER(vcode) NOT LIKE '%TECH%'"
    )

    # 4. Interview Session interviewer ownership
    op.add_column("tblt_interview", sa.Column("nid_interviewer", sa.BigInteger(), nullable=True))
    op.create_index("ix_tblt_interview_nid_interviewer", "tblt_interview", ["nid_interviewer"])
    op.create_foreign_key(
        "fk_tblt_interview_nid_interviewer_tblm_user",
        "tblt_interview",
        "tblm_user",
        ["nid_interviewer"],
        ["nid"],
        ondelete="SET NULL",
    )
    op.execute(
        "UPDATE tblt_interview i SET nid_interviewer = p.nid_owner_user "
        "FROM tblm_profile p WHERE i.nid_profile = p.nid AND i.nid_interviewer IS NULL"
    )

    # 5. HrDecision two-tier handoff columns
    op.add_column(
        "tblt_hr_decision",
        sa.Column("vactor_role", sa.String(length=30), nullable=False, server_default="HR"),
    )
    op.add_column(
        "tblt_hr_decision",
        sa.Column("vworkflow_status", sa.String(length=30), nullable=False, server_default="FINALIZED"),
    )
    op.create_check_constraint(
        "ck_tblt_hr_decision_actor_role",
        "tblt_hr_decision",
        "vactor_role IN ('INTERVIEWER', 'HR')",
    )
    op.create_check_constraint(
        "ck_tblt_hr_decision_workflow_status",
        "tblt_hr_decision",
        "vworkflow_status IN ('PENDING_HR_FOLLOWUP', 'FINALIZED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tblt_hr_decision_workflow_status", "tblt_hr_decision", type_="check")
    op.drop_constraint("ck_tblt_hr_decision_actor_role", "tblt_hr_decision", type_="check")
    op.drop_column("tblt_hr_decision", "vworkflow_status")
    op.drop_column("tblt_hr_decision", "vactor_role")

    op.drop_constraint("fk_tblt_interview_nid_interviewer_tblm_user", "tblt_interview", type_="foreignkey")
    op.drop_index("ix_tblt_interview_nid_interviewer", table_name="tblt_interview")
    op.drop_column("tblt_interview", "nid_interviewer")

    op.drop_constraint("ck_tblm_profile_target_role", "tblm_profile", type_="check")
    op.drop_constraint("fk_tblm_profile_nid_owner_user_tblm_user", "tblm_profile", type_="foreignkey")
    op.drop_index("ix_tblm_profile_nid_owner_user", table_name="tblm_profile")
    op.drop_column("tblm_profile", "nid_owner_user")
    op.drop_column("tblm_profile", "vdepartment")
    op.drop_column("tblm_profile", "vtarget_role")

    op.execute("ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_ck_tblm_candidate_vstatus")
    op.execute("ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_vstatus")
    op.execute("UPDATE tblm_candidate SET vstatus = 'COMPLETED' WHERE vstatus = 'PENDING_HR_REVIEW'")
    op.create_check_constraint(
        op.f("ck_tblm_candidate_ck_tblm_candidate_vstatus"),
        "tblm_candidate",
        "vstatus IN ('SCREENING', 'ESCALATED', 'INTERVIEW_SCHEDULED', 'TECHNICAL_TEST', 'COMPLETED', 'OFFERED', 'REJECTED')",
    )

    op.execute("ALTER TABLE tblm_user DROP CONSTRAINT IF EXISTS ck_tblm_user_ck_tblm_user_vrole")
    op.execute("ALTER TABLE tblm_user DROP CONSTRAINT IF EXISTS ck_tblm_user_vrole")
    op.execute("ALTER TABLE tblm_permission DROP CONSTRAINT IF EXISTS ck_tblm_permission_ck_tblm_permission_vrole")
    op.execute("ALTER TABLE tblm_permission DROP CONSTRAINT IF EXISTS ck_tblm_permission_vrole")
    op.execute("UPDATE tblm_user SET vrole = 'USER_INTERVIEWER' WHERE vrole = 'INTERVIEWER'")
    op.execute("UPDATE tblm_user SET vrole = 'AUDITOR' WHERE vrole = 'ADMIN'")
    op.execute("UPDATE tblm_permission SET vrole = 'USER_INTERVIEWER' WHERE vrole = 'INTERVIEWER'")
    op.execute("UPDATE tblm_permission SET vrole = 'AUDITOR' WHERE vrole = 'ADMIN'")
    op.create_check_constraint(
        "ck_tblm_user_vrole",
        "tblm_user",
        "vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')",
    )
    op.create_check_constraint(
        "ck_tblm_permission_vrole",
        "tblm_permission",
        "vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')",
    )
