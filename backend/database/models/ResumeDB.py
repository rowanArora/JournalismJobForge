from datetime import datetime as dt, timezone
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ResumeDB(SQLModel, table=True):
    """Database table for resumes."""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True, description="Database ID for this resume.")

    # Foreign keys
    user_id: int = Field(
        foreign_key="userdb.id",
        description="Owner user ID (foreign key to users).",
    )

    # Storage info
    file_path: str | None = Field(
        default=None,
        description="Local path or storage URL to the resume file.",
    )
    title: str | None = Field(
        default=None,
        description="Friendly label for the resume (e.g. 'Reporting Resume v2').",
    )

    # User work info
    raw_text: str | None = Field(
        default=None,
        description="Extracted text from the resume file (for search/AI).",
    )
    skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Parsed skills/keywords extracted from the resume (optional).",
    )
    experience: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Parsed experience bullets or roles extracted from the resume (optional).",
    )
    education: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Parsed education entries extracted from the resume (optional).",
    )
    personal_projects: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Parsed personal projects extracted from the resume (optional).",
    )
    portfolio_urls: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Link to portfolio/website/social media (optional).",
    )

    # Dates
    created_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this resume was created.")
    updated_at: dt = Field(default_factory=lambda: dt.now(timezone.utc), description="When this resume was last updated.")
