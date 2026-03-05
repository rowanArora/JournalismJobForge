from datetime import datetime as dt
from pydantic import BaseModel, Field


class CoverLetter(BaseModel):
    """A cover letter template or job-specific draft."""

    id: int | None = Field(default=None, description="Database ID for this cover letter.")

    user_id: int | None = Field(
        default=None,
        description="Owner user ID (foreign key to users).",
    )
    job_id: int | None = Field(
        default=None,
        description="Job ID if this cover letter is tailored to a specific job (optional).",
    )
    application_id: int | None = Field(
        default=None,
        description="Application ID if this cover letter is tied to a specific application (optional).",
    )

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

    created_at: dt | None = Field(default=None, description="When this cover letter was created.")
    updated_at: dt | None = Field(default=None, description="When this cover letter was last updated.")
