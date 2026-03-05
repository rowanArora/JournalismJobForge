from datetime import datetime as dt, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class CoverLetterDB(SQLModel, table=True):
    """Database table for cover letters."""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True, description="Database ID for this cover letter.")

    # Foreign keys
    user_id: int = Field(
        foreign_key="userdb.id",
        description="Owner user ID (foreign key to users).",
    )
    job_id: Optional[int] = Field(
        default=None,
        foreign_key="jobdb.id",
        description="Job ID if this cover letter is tailored to a specific job (optional).",
    )
    application_id: Optional[int] = Field(
        default=None,
        foreign_key="applicationdb.id",
        description="Application ID if this cover letter is tied to a specific application (optional).",
    )

    # Storage info
    file_path: str | None = Field(
        default=None,
        description="Local path or storage URL if stored as a file (optional).",
    )
    title: str | None = Field(
        default=None,
        description="Friendly label for the cover letter (e.g. 'General Producer Template').",
    )
    body: str | None = Field(
        default=None,
        description="Cover letter text content (for editing/AI rewriting).",
    )

    # Dates
    created_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this cover letter was created.")
    updated_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this cover letter was last updated.")
