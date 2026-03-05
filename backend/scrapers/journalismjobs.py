import json
import time

import requests
from bs4 import BeautifulSoup
from sqlmodel import select
from tqdm import tqdm

from backend.database.connection import Session, engine
from backend.database.models import JobDB
from backend.models.Job import Job
from backend.utils.enums import SalaryUnit
from backend.utils.scraper_utils import (
    card_passes_filters,
    get_description_after_h2,
    parse_currency,
    parse_date_posted,
    parse_details_table,
    parse_job_type,
    parse_salary_range,
    parse_salary_unit,
    text,
)

COUNT_PER_PAGE = 500
BASE_URL = "https://www.journalismjobs.com"
SOURCE_NAME = "journalismjobs.com"


def _listing_url(page: int) -> str:
    return (
        f"https://www.journalismjobs.com/job-listings?keywords=&location=&jobType=&date=&industries=&position=&diversity=&focuses=&salary=&company=&title=&virtual=&page={page}&count={COUNT_PER_PAGE}"
    )


def _parse_listing_card(card) -> dict[str, str]:
    """Parse a job card on the listing page (no detail fetch). Returns title, company, location, job_type, href."""
    title = text(card.find("h3", class_="job-item-title"))
    company = text(card.find("div", class_="job-item-company"))
    details_ul = card.find("ul", class_="job-item-details")
    li = details_ul.find_all("li") if details_ul else []
    location = text(li[0]) if len(li) > 0 else ""
    job_type = text(li[1]) if len(li) > 1 else ""
    href = card.get("href") or ""
    return {"title": title, "company": company, "location": location, "job_type": job_type, "href": href}


def scrape_journalism_jobs(filters: dict | None = None) -> list[Job]:
    with Session(engine) as session:
        # Phase 1: collect job URLs that pass filters (from listing pages only); keep card company for fallback
        to_fetch: list[tuple[str, str]] = []
        page = 1
        while True:
            resp = requests.get(_listing_url(page))
            resp.raise_for_status()

            dashboard_soup = BeautifulSoup(resp.content, "html.parser")

            results = dashboard_soup.find(id="jobs")
            if not results:
                break

            job_cards = results.find_all("a", class_="job-item")
            if not job_cards:
                break

            for job_card in job_cards:
                card_data = _parse_listing_card(job_card)

                href = (card_data.get("href") or "").strip()
                if not href:
                    continue

                if filters and not card_passes_filters(card_data, filters):
                    continue

                job_url = href if href.startswith("http") else BASE_URL + href
                card_company = (card_data.get("company") or "").strip()

                statement = select(JobDB).where(JobDB.application_url == job_url)
                result = session.exec(statement)
                exists = result.first()
                if not exists:
                    to_fetch.append((job_url, card_company))
            page += 1

        # Phase 2: fetch each job detail with progress bar
        jobs_list: list[Job] = []
        for job_url, card_company in tqdm(to_fetch, desc="Scraping jobs", unit=" job"):
            try:
                page_resp = requests.get(job_url)
                page_resp.raise_for_status()
            except requests.RequestException:
                continue

            job_soup = BeautifulSoup(page_resp.content, "html.parser")
            job_view = job_soup.find("div", id="job-view")
            if not job_view:
                continue

            job_header = job_view.find("div", class_="job-header")
            container = job_header or job_view
            title_el = container.find("h1")
            title = text(title_el) or "Unknown"
            h2 = container.find("h2")
            company_el = h2.find("a") if h2 else None
            company = (text(company_el) or card_company or "").strip()
            company_url = company_el.get("href") if company_el else None
            location_el = container.find("h3")
            location = text(location_el).strip() or None

            details = parse_details_table(job_view)
            description = get_description_after_h2(job_view)
            date_posted = parse_date_posted(details.get("Date Posted", ""))
            job_type = parse_job_type(details.get("Job Status", ""))
            salary_str = details.get("Salary", "")
            salary_range = parse_salary_range(salary_str)
            salary_min = salary_range[0] if salary_range and len(salary_range) > 0 else None
            salary_max = salary_range[1] if salary_range and len(salary_range) > 1 else salary_min
            salary_unit_str = parse_salary_unit(salary_str)
            salary_unit = SalaryUnit(salary_unit_str) if salary_unit_str in ("hourly", "annual") else None
            industry_str = details.get("Industry", "").strip()
            industries = [industry_str] if industry_str else None
            currency = parse_currency(location or "")

            try:
                db_job = JobDB(
                    application_url=job_url,
                    title=title,
                    company=company,
                    company_url=company_url,
                    description=description or None,
                    location=location or None,
                    job_type=job_type.value if job_type else None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_unit=salary_unit_str,
                    currency=currency,
                    industries=", ".join(industries) if industries else None,
                    source=SOURCE_NAME,
                    date_posted=date_posted or None,
                    application_deadline=None, # don't have application deadline yet from this site it seems
                )
                session.add(db_job)

                job = Job(
                    application_url=job_url,
                    title=title,
                    company=company,
                    company_url=company_url,
                    description=description or None,
                    location=location,
                    job_type=job_type,
                    salary_range=salary_range,
                    salary_unit=salary_unit,
                    currency=currency,
                    date_posted=date_posted,
                    industries=industries,
                    source=SOURCE_NAME,
                )
                jobs_list.append(job)
            except Exception:
                continue
            time.sleep(0.5)  # be polite to the server

        session.commit()
    return jobs_list


if __name__ == "__main__":
    # No filters: scrape all jobs. When User/DB is connected, build filters from user
    # (e.g. user.preferred_locations, user.preferred_job_titles, [jt.value for jt in user.preferred_role_types]).
    filters = None
    print("Scraping JournalismJobs.com (no filters)...")
    start = time.perf_counter()
    jobs = scrape_journalism_jobs(filters=filters)
    elapsed = time.perf_counter() - start
    print(f"Done. Scraped {len(jobs)} jobs in {elapsed:.1f}s ({elapsed / 60:.1f} min).")
    if jobs:
        print("\nFirst job (sample):")
        print(jobs[0].model_dump(mode="json"))
        out_path = "scraped_jobs.json"
        with open(out_path, "w") as f:
            json.dump([j.model_dump(mode="json") for j in jobs], f, indent=2)
        print(f"\nAll jobs written to {out_path}")
    else:
        print("No jobs found.")
