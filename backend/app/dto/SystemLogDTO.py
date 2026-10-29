from datetime import datetime

from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class SystemLogDTO(BaseDTO):
    nid: int = Field(...)
    vlog_level: str = Field(...)
    vlog_message: str = Field(...)
    vlog_stacktrace: str | None = Field(None,)
    vlog_source: str | None = Field(None,)
    vlog_path: str | None = Field(None,)
    vlog_method: str | None = Field(None,)
    vlog_status_code: str | None = Field(None,)
    dcrea: datetime = Field(...)


class SystemLogFilterParams(BaseDTO):
    level: str | None = Field(None)
    source: str | None = Field(None)
    search: str | None = Field(None)
