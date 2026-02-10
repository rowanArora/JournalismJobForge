from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
def list_jobs():
    """Return list of matching jobs (placeholder until scraper/DB wired up)."""
    return []
