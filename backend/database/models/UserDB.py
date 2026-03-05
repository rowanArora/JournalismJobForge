from datetime import datetime as dt, timezone
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

class UserDB(SQLModel, table=True):
    """Database table for users."""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True, description="Database ID for this user.")

    # Core listing fields
    username: str = Field(..., description="Unique username for login/display.")
    password_hash: str = Field(
        ...,
        description="Hashed password (never store plain text passwords in the database).",
    )
    first_name: str = Field(..., description="User first name.")
    last_name: str = Field(..., description="User last name.")
    email: EmailStr = Field(..., description="User email address.")
    user_type: str = Field(
        default="Basic",
        description="Authorization tier for the user (basic/admin).",
    )

    # Salary info
    default_currency: str = Field(
        default="USD",
        description='Preferred currency code for salary display (e.g. "USD", "CAD").',
    )
    salary_display_mode: str = Field(
        default="annual",
        description='Preferred salary display format: "annual" or "hourly".',
    )

    # Job preferences
    preferred_locations: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Locations the user prefers to search/filter for.",
    )
    preferred_job_titles: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Keywords/job titles the user is interested in (for filtering/matching).",
    )
    preferred_role_types: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Preferred role types (full-time, part-time, freelance, etc.).",
    )

    # User work info
    user_skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Skills associated with the user (from profile and/or parsed resume).",
    )
    user_experience: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Experience associated with the user (from profile and/or parsed resume).",
    )
    user_education: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Education associated with the user (from profile and/or parsed resume).",
    )
    user_personal_projects: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Personal projects associated with the user (from profile and/or parsed resume).",
    )
    user_portfolio_urls: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="URLs associated with the user (from profile and/or parsed resume).",
    )

    # Other metadata
    timezone: Optional[str] = Field(
        default="UTC",
        description="IANA timezone name for the user, e.g. 'America/Toronto'.",
    )
    darkmode: Optional[bool] = Field(default=False, description="UI preference: dark mode enabled.")

    # Dates
    created_at: dt = Field(
        default_factory=lambda: dt.now(timezone.utc),
        description="When this user was created.",
    )
    updated_at: dt = Field(
        default_factory=lambda: dt.now(timezone.utc),
        description="When this user was last updated.",
    )
