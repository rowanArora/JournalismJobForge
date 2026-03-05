from datetime import datetime as dt

from pydantic import BaseModel, Field

from backend.utils.enums import JobType, SalaryUnit


class Job(BaseModel):
    """A single job listing from an external job board."""

    id: int | None = Field(default=None, description="Database ID for this job.")

    application_url: str = Field(
        ...,
        description="Original job posting URL on the source job board.",
    )
    title: str = Field(..., description="Job title as shown on the listing.")
    company: str = Field(..., description="Company/organization name.")
    company_url: str | None = Field(
        default=None,
        description="Company/organization website URL (if available on the listing).",
    )
    description: str | None = Field(
        default=None,
        description="Full job description text (best-effort extraction).",
    )
    location: str | None = Field(
        default=None,
        description="Job location string from the listing (e.g. city/region/remote).",
    )
    job_type: JobType | None = Field(
        default=None,
        description="Type of job (full-time, part-time, freelance, internship, unpaid).",
    )

    salary_range: list[float] | None = Field(
        default=None,
        description="One or two salary numbers parsed from the listing (e.g. [50000, 60000]).",
    )
    salary_unit: SalaryUnit | None = Field(
        default=None,
        description='Unit for salary_range: "hourly" or "annual" (inferred from salary text).',
    )
    currency: str = Field(
        default="USD",
        description='Currency code for salary (e.g. "USD", "CAD"). Inferred from location when possible.',
    )

    industries: list[str] | None = Field(
        default=None,
        description="Industries/tags associated with the role (source-dependent).",
    )
    source: str | None = Field(
        default=None,
        description="Job board source identifier (e.g. 'journalismjobs.com').",
    )

    date_posted: dt | None = Field(
        default=None,
        description="Date the job was posted on the job board (if available).",
    )
    application_deadline: dt | None = Field(
        default=None,
        description="Deadline to apply (if the source listing provides it).",
    )
    created_at: dt | None = Field(
        default=None,
        description="Job posting created at.",
    )
