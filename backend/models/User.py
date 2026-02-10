from datetime import datetime as dt
from pydantic import BaseModel, EmailStr, Field

from backend.models.Resume import Resume
from backend.models.CoverLetter import CoverLetter
from backend.utils.enums import JobType, UserTypes


class User(BaseModel):
    """A user profile plus job-search preferences (DB-backed later)."""

    id: int | None = Field(default=None, description="Database ID for this user.")

    username: str = Field(..., description="Unique username for login/display.")
    password: str = Field(
        ...,
        description="User password (note: in a real DB this should be stored as a hash, not plain text).",
    )
    first_name: str = Field(..., description="User first name.")
    last_name: str = Field(..., description="User last name.")
    email: EmailStr = Field(..., description="User email address.")

    user_type: UserTypes = Field(
        default=UserTypes.BASIC,
        description="Authorization tier for the user (basic/admin).",
    )
    timezone: dt.timezone | None = Field(
        default=None,
        description="User timezone for reminders/deadlines (optional).",
    )
    darkmode: bool = Field(default=False, description="UI preference: dark mode enabled.")

    resumes: list[Resume] | None = Field(
        default=None,
        description="Resumes owned by the user (optional nested objects for API responses).",
    )
    cover_letters: list[CoverLetter] | None = Field(
        default=None,
        description="Cover letters owned by the user (optional nested objects for API responses).",
    )

    default_currency: str = Field(
        default="USD",
        description='Preferred currency code for salary display (e.g. "USD", "CAD").',
    )
    salary_display_mode: str = Field(
        default="annual",
        description='Preferred salary display format: "annual" or "hourly".',
    )

    preferred_locations: list[str] | None = Field(
        default=None,
        description="Locations the user prefers to search/filter for.",
    )
    preferred_job_titles: list[str] | None = Field(
        default=None,
        description="Keywords/job titles the user is interested in (for filtering/matching).",
    )
    preferred_role_types: list[JobType] | None = Field(
        default=None,
        description="Preferred role types (full-time, part-time, freelance, etc.).",
    )
    user_skills: list[str] | None = Field(
        default=None,
        description="Skills associated with the user (from profile and/or parsed resume).",
    )
