from datetime import datetime as dt
from pydantic import BaseModel, Field


class Resume(BaseModel):
    """A user resume (file metadata plus optional parsed content)."""

    id: int | None = Field(default=None, description="Database ID for this resume.")
    user_id: int | None = Field(
        default=None,
        description="Owner user ID (foreign key to users).",
    )

    file_path: str | None = Field(
        default=None,
        description="Local path or storage URL to the resume file.",
    )
    title: str | None = Field(
        default=None,
        description="Friendly label for the resume (e.g. 'Reporting Resume v2').",
    )

    created_at: dt | None = Field(default=None, description="When this resume was created.")
    updated_at: dt | None = Field(default=None, description="When this resume was last updated.")

    raw_text: str | None = Field(
        default=None,
        description="Extracted text from the resume file (for search/AI).",
    )
    skills: list[str] | None = Field(
        default=None,
        description="Parsed skills/keywords extracted from the resume (optional).",
    )
    experience: list[str] | None = Field(
        default=None,
        description="Parsed experience bullets or roles extracted from the resume (optional).",
    )
    education: list[str] | None = Field(
        default=None,
        description="Parsed education entries extracted from the resume (optional).",
    )
    personal_projects: list[str] | None = Field(
        default=None,
        description="Parsed personal projects extracted from the resume (optional).",
    )
    portfolio_url: str | None = Field(
        default=None,
        description="Link to portfolio/website (optional).",
    )
