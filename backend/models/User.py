from datetime import datetime as dt
from pydantic import BaseModel, EmailStr

from backend.utils.enums import JobType, UserTypes


class User(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: EmailStr
    user_type: UserTypes = UserTypes.BASIC
    timezone: dt.timezone | None = None
    darkmode: bool = False
    resumes: list[str] | None = None
    cvs: list[str] | None = None
    default_currency: str = "USD"
    salary_display_mode: str = "annual"
    preferred_locations: list[str] | None = None
    preferred_job_titles: list[str] | None = None
    preferred_role_types: list[JobType] | None = None
    user_skills: list[str] | None = None
