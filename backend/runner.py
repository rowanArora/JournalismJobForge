"""
Central entry point to run scrapers.

When running all scrapers (default), they run in parallel using threads so
JournalismJobs.com and MediaBistro.com are scraped at the same time. Use
--sequential to run one after the other (e.g. for debugging).

Examples:
  python -m backend.runner                 # both scrapers in parallel
  python -m backend.runner --sequential   # both scrapers one after the other
  python -m backend.runner --only journalismjobs
  python -m backend.runner --only mediabistro
  python -m backend.runner --clear-db     # clear JobDB (and dependents) then run pipeline
  python -m backend.utils.clear_jobs      # clear JobDB only (standalone)
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.scrapers.journalismjobs import scrape_journalism_jobs
from backend.scrapers.mediabistro import scrape_media_bistro
from backend.utils.clear_jobs import clear_jobdb


def _run_journalism_jobs(filters: dict | None = None):
    print("\n--- JournalismJobs.com ---")
    start = time.perf_counter()
    jobs = scrape_journalism_jobs(filters=filters)
    elapsed = time.perf_counter() - start
    print(f"Done. Scraped {len(jobs)} jobs in {elapsed:.1f}s.")
    return jobs


def _run_media_bistro(filters: dict | None = None):
    print("\n--- MediaBistro.com ---")
    start = time.perf_counter()
    jobs = scrape_media_bistro(filters=filters)
    elapsed = time.perf_counter() - start
    print(f"Done. Scraped {len(jobs)} jobs in {elapsed:.1f}s.")
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run job scrapers and/or company URL backfill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--only",
        choices=["journalismjobs", "mediabistro"],
        default=None,
        help="Run only this scraper (default: run both in parallel).",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run scrapers one after the other (default: run both in parallel when applicable).",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Clear JobDB (and applications / cover-letter links) before running.",
    )
    args = parser.parse_args()

    filters = None  # TODO: build from user prefs when User/DB is connected

    if args.clear_db:
        a, c, j = clear_jobdb()
        print(f"Cleared: {j} job(s), {a} application(s), {c} cover letter(s) unlinked.")

    if args.only == "journalismjobs":
        _run_journalism_jobs(filters)
        return

    if args.only == "mediabistro":
        _run_media_bistro(filters)
        return

    # Default: run both scrapers (parallel unless --sequential)
    if args.sequential:
        _run_journalism_jobs(filters)
        _run_media_bistro(filters)
    else:
        print("\nRunning scrapers in parallel...")
        overall_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as executor:
            fj = executor.submit(_run_journalism_jobs, filters)
            fm = executor.submit(_run_media_bistro, filters)
            for fut in as_completed([fj, fm]):
                fut.result()  # raise any exception from the thread
        print(f"\nBoth scrapers finished in {time.perf_counter() - overall_start:.1f}s.")
    print("\nAll done.")


if __name__ == "__main__":
    main()
