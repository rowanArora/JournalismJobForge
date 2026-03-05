from datetime import datetime as dt, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class JobDB(SQLModel, table=True):
    """Database table for job listings."""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True, description="Database ID for this job.")

    # Core listing fields
    application_url: str = Field(
        ...,
        description="Original job posting URL on the source job board.",
    )
    title: str = Field(..., description="Job title as shown on the listing.")
    company: str = Field(..., description="Company/organization name.")
    company_url: Optional[str] = Field(
        default=None,
        description="Company/organization website URL (if available on the listing).",
    )
    description: Optional[str] = Field(
        default=None,
        description="Full job description text (best-effort extraction).",
    )
    location: Optional[str] = Field(
        default=None,
        description="Job location string from the listing (e.g. city/region/remote).",
    )

    # Store job type as string (enum value)
    job_type: Optional[str] = Field(
        default=None,
        description="Job type string, e.g. 'full-time', 'internship'.",
    )

    # Salary info
    salary_min: Optional[float] = Field(
        default=None,
        description="Minimum salary value (from salary_range[0] if available).",
    )
    salary_max: Optional[float] = Field(
        default=None,
        description="Maximum salary value (from salary_range[1] if available).",
    )
    salary_unit: Optional[str] = Field(
        default=None,
        description='Unit for salary: "hourly" or "annual" (inferred from salary text).',
    )
    currency: str = Field(
        default="USD",
        description='Currency code for salary (e.g. "USD", "CAD"). Inferred from location when possible.',
    )

    # Other metadata
    industries: Optional[str] = Field(
        default=None,
        description="Industries/tags associated with the role (stored as comma-separated string).",
    )
    source: Optional[str] = Field(
        default=None,
        description="Job board source identifier (e.g. 'journalismjobs.com').",
    )

    # Dates
    date_posted: Optional[dt] = Field(
        default=None,
        description="Date the job was posted on the job board (if available).",
    )
    application_deadline: Optional[dt] = Field(
        default=None,
        description="Deadline to apply (if the source listing provides it).",
    )
    created_at: dt = Field(
        default_factory=lambda: dt.now(timezone.utc),
        description="When this job listing was scraped/created in the database.",
    )
