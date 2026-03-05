from enum import Enum


class JobType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    FREELANCE = "freelance"
    INTERN = "internship"
    UNPAID = "unpaid/volunteer"


class SalaryUnit(Enum):
    """Unit for salary: hourly (e.g. $18/hr) or annual (e.g. $70,000/year)."""
    HOURLY = "hourly"
    ANNUAL = "annual"


class Currency(Enum):
    USD = "USD"
    CAD = "CAD"
    GBP = "GBP"
    EUR = "EUR"


class UserTypes(Enum):
    BASIC = "Basic"
    ADMIN = "Admin"
    SUPER_ADMIN = "SuperAdmin"


class JobStatus(Enum):
    NOT_APPLIED = "NA"
    APPLIED = "Applied"
    REJECTED = "Rejected"
    INTERVIEW = "Interview"
    OFFER = "Job Offered"
    ACCEPTED = "Accepted"
