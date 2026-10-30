"""add_candidate_lifecycle_and_reapply_fields

Revision ID: 20261029_0002
Revises: 03eb74740880
Create Date: 2026-10-29 20:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261029_0002"
down_revision: str | None = "03eb74740880"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tblm_candidate",
        sa.Column("napplication_cycle", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "tblm_candidate",
        sa.Column("nid_previous_application", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        op.f("ix_tblm_candidate_vemail"),
        "tblm_candidate",
        ["vemail"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tblm_candidate_nid_previous_application"),
        "tblm_candidate",
        ["nid_previous_application"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_tblm_candidate_nid_previous_application_tblm_candidate"),
        "tblm_candidate",
        "tblm_candidate",
        ["nid_previous_application"],
        ["nid"],
        ondelete="SET NULL",
    )

    # Refresh status check constraint safely on PostgreSQL
    op.execute(
        "ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_ck_tblm_candidate_vstatus"
    )
    op.execute("ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_vstatus")
    op.create_check_constraint(
        op.f("ck_tblm_candidate_ck_tblm_candidate_vstatus"),
        "tblm_candidate",
        "vstatus IN ('SCREENING', 'ESCALATED', 'INTERVIEW_SCHEDULED', 'TECHNICAL_TEST', 'COMPLETED', 'OFFERED', 'REJECTED')",
    )

    op.add_column(
        "tblt_hr_decision",
        sa.Column("vnext_stage", sa.String(length=50), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_tblt_hr_decision_ck_tblt_hr_decision_next_stage"),
        "tblt_hr_decision",
        "vnext_stage IS NULL OR vnext_stage IN ('NEXT_INTERVIEW', 'TECHNICAL_TEST', 'OFFERED')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_tblt_hr_decision_ck_tblt_hr_decision_next_stage"),
        "tblt_hr_decision",
        type_="check",
    )
    op.drop_column("tblt_hr_decision", "vnext_stage")

    op.execute(
        "ALTER TABLE tblm_candidate DROP CONSTRAINT IF EXISTS ck_tblm_candidate_ck_tblm_candidate_vstatus"
    )
    op.execute(
        "UPDATE tblm_candidate SET vstatus = 'ESCALATED' WHERE vstatus = 'TECHNICAL_TEST'"
    )
    op.create_check_constraint(
        op.f("ck_tblm_candidate_ck_tblm_candidate_vstatus"),
        "tblm_candidate",
        "vstatus IN ('SCREENING', 'ESCALATED', 'INTERVIEW_SCHEDULED', 'COMPLETED', 'OFFERED', 'REJECTED')",
    )

    op.drop_constraint(
        op.f("fk_tblm_candidate_nid_previous_application_tblm_candidate"),
        "tblm_candidate",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_tblm_candidate_nid_previous_application"), table_name="tblm_candidate")
    op.drop_index(op.f("ix_tblm_candidate_vemail"), table_name="tblm_candidate")
    op.drop_column("tblm_candidate", "nid_previous_application")
    op.drop_column("tblm_candidate", "napplication_cycle")

