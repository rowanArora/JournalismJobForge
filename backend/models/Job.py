from datetime import datetime as dt
from typing import Literal

from pydantic import BaseModel

from backend.utils.enums import JobType

# Unit for salary_range: "hourly" (e.g. $18/hr) or "annual" (e.g. $70,000/year).
SalaryUnit = Literal["hourly", "annual"]


class Job(BaseModel):
    application_url: str                        # Job board URL for the job
    title: str                                  # Job title
    company: str                                # Company where the job is
    company_url: str | None = None              # Company's URL
    description: str | None = None              # Job description
    location: str | None = None                 # Job location
    job_type: JobType | None = None             # Type of job (e.g. full-time, part-time, freelance, internship, unpaid)
    salary_range: list[float] | None = None     # Salary numbers; interpret using salary_unit
    salary_unit: SalaryUnit | None = None       # "hourly" or "annual" (from listing); use config SALARY_DISPLAY_MODE to show
    currency: str = "CAD"                       # Salary currency
    date_posted: dt | None = None               # Date the job was posted on the job board
    application_deadline: dt | None = None      # Deadline to apply for the job
    deadline_passed: bool = False               # If the deadline to apply for the job has passed
    industries: list[str] | None = None         # Industries the job is a part of
    source: str | None = None                   # Which job site the job came from
    date_applied: dt | None = None              # Date user applied to the job
    applied_resume: str = ""                    # Path to resume used to apply to job in DB
    applied_cv: str = ""                        # Path to CV used to apply to job in DB
