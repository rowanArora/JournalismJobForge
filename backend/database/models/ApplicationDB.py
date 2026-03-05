from datetime import datetime as dt, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class ApplicationDB(SQLModel, table=True):
    """Database table for job applications."""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True, description="Database ID for this application.")

    # Foreign keys
    user_id: int = Field(
        foreign_key="userdb.id",
        description="User ID (foreign key to users).",
    )
    job_id: int = Field(
        foreign_key="jobdb.id",
        description="Job ID (foreign key to jobs).",
    )
    resume_id: Optional[int] = Field(
        default=None,
        foreign_key="resumedb.id",
        description="Resume ID used for this application (optional).",
    )
    cover_letter_id: Optional[int] = Field(
        default=None,
        foreign_key="coverletterdb.id",
        description="Cover letter ID used for this application (optional).",
    )

    # Other metadata
    date_applied: Optional[dt] = Field(
        default=None,
        description="When the user applied (optional until the user applies).",
    )
    status: str = Field(
        default="NA",
        description="Application status (applied/interview/rejected/offer/etc.).",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free-form notes about the application (optional).",
    )

    # Dates
    created_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this application was created.")
    updated_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this application was last updated.")
