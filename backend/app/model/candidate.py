from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import TableBaseModel


class Candidate(TableBaseModel):
    """Job applicant data with pseudonymization code (tblm_candidate)."""

    __tablename__ = "tblm_candidate"

    vcandidate_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vemail: Mapped[str] = mapped_column(String(255), nullable=False)
    vphone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vjob_position: Mapped[str] = mapped_column(String(100), nullable=False)
    ncurrent_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    nexpected_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
