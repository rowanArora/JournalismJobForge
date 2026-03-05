"""
Clear the JobDB table (and dependent rows so the delete succeeds).

Deletes all ApplicationDB rows (they reference jobs), sets CoverLetterDB.job_id
to NULL where present, then deletes all JobDB rows. Safe to run before a
full re-scrape.
"""

from sqlmodel import select

from backend.database.connection import Session, engine
from backend.database.models import ApplicationDB, CoverLetterDB, JobDB


def clear_jobdb() -> tuple[int, int, int]:
    """
    Clear all jobs and dependent data. Returns (applications_deleted, cover_letters_unlinked, jobs_deleted).
    """
    with Session(engine) as session:
        # Delete applications (they reference jobs)
        apps = list(session.exec(select(ApplicationDB)).all())
        for a in apps:
            session.delete(a)
        applications_deleted = len(apps)

        # Unlink cover letters from jobs (so we can delete jobs)
        cover_letters = list(
            session.exec(select(CoverLetterDB).where(CoverLetterDB.job_id.isnot(None))).all()
        )
        for cl in cover_letters:
            cl.job_id = None
        cover_letters_unlinked = len(cover_letters)

        # Delete all jobs
        jobs = list(session.exec(select(JobDB)).all())
        for j in jobs:
            session.delete(j)
        jobs_deleted = len(jobs)

        session.commit()
    return applications_deleted, cover_letters_unlinked, jobs_deleted


def main() -> None:
    a, c, j = clear_jobdb()
    print(f"Cleared jobdb: {j} job(s) deleted, {a} application(s) deleted, {c} cover letter(s) unlinked from jobs.")


if __name__ == "__main__":
    main()
