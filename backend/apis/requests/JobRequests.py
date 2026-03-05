from pydantic import BaseModel



class GetJobsRequest(BaseModel):
    min_preferred_salary: float = 0
    max_preferred_salary: float = 1000000
    include_preferred_locations: bool = False
    include_preferred_job_titles: bool = False
    include_preferred_role_types: bool = False
    source: str | None = None
