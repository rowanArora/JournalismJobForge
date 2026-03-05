from fastapi import APIRouter, Depends
from sqlmodel import select

from backend.apis import GetJobsRequest
from backend.database.connection import Session, get_session
from backend.database.models import JobDB
from backend.models import User
from backend.models.Job import Job
from backend.utils.scraper_utils import job_db_to_pydantic

job_router = APIRouter(prefix="/jobs", tags=["jobs"])


@job_router.get("/", response_model=list[Job])
def list_jobs(
    user: User,
    request: GetJobsRequest,
    session: Session = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
):
    """Return list of matching jobs."""
    statement = select(JobDB).order_by(JobDB.date_posted.desc())

    statement = statement.where(JobDB.salary_min >= request.min_preferred_salary and JobDB.salary_max <= request.max_preferred_salary)
    if request.include_preferred_role_types:
        statement = statement.where(JobDB.job_type in user)
    if request.source:
        statement = statement.where(JobDB.source == request.source)

    statement = statement.offset(offset).limit(limit)
    result = session.exec(statement)
    rows = result.all()
    return [job_db_to_pydantic(row) for row in rows]
