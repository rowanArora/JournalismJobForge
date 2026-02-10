from datetime import datetime as dt
from pydantic import BaseModel, Field

from backend.utils.enums import JobStatus


class Application(BaseModel):
    """A user's application to a specific job."""

    id: int | None = Field(default=None, description="Database ID for this application.")

    user_id: int | None = Field(
        default=None,
        description="User ID (foreign key to users).",
    )
    job_id: int | None = Field(
        default=None,
        description="Job ID (foreign key to jobs).",
    )

    date_applied: dt | None = Field(
        default=None,
        description="When the user applied (optional until the user applies).",
    )
    status: JobStatus = Field(
        default=JobStatus.NOT_APPLIED,
        description="Application status (applied/interview/rejected/offer/etc.).",
    )

    resume_id: int | None = Field(
        default=None,
        description="Resume ID used for this application (optional).",
    )
    cover_letter_id: int | None = Field(
        default=None,
        description="Cover letter ID used for this application (optional).",
    )

    notes: str | None = Field(
        default=None,
        description="Free-form notes about the application (optional).",
    )
