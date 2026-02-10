import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from backend.config import CURRENCY_LOCATION_KEYWORDS, DEFAULT_CURRENCY
from backend.models.Job import Job
from backend.utils.enums import JobType

COUNT_PER_PAGE = 500
BASE_URL = "https://www.journalismjobs.com"
SOURCE_NAME = "journalismjobs.com"


def _listing_url(page: int) -> str:
    return (
        f"https://www.journalismjobs.com/job-listings?keywords=&location=&jobType=&date=&industries=&position=&diversity=&focuses=&salary=&company=&title=&virtual=&page={page}&count={COUNT_PER_PAGE}"
    )


def _text(el) -> str:
    """Get stripped text from an element, or '' if None."""
    return el.get_text(strip=True) if el else ""


def _parse_details_table(job_view) -> dict[str, str]:
    """Parse the job details table (Date Posted, Industry, Job Status, Salary, etc.) into a dict."""
    details = {}
    table = job_view.find("table", class_="table") if job_view else None
    if not table:
        return details
    tbody = table.find("tbody") or table
    for row in tbody.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            details[_text(th)] = _text(td)
    return details


def _get_description(job_view) -> str:
    """Get full description text: everything after the h2 'Description:' until Apply or next section."""
    if not job_view:
        return ""
    h2 = job_view.find("h2", string=re.compile(r"Description", re.I))
    if not h2:
        return ""
    parts = []
    for sib in h2.find_next_siblings():
        # Stop at Apply link or next major section
        if sib.name == "a" and sib.get("id") == "apply":
            break
        if sib.name == "h2":
            break
        if sib.name in ("p", "ul", "ol", "li", "div") and "apply" not in (sib.get("class") or []):
            parts.append(sib.get_text(separator=" ", strip=True))
    return "\n\n".join(p for p in parts if p)


def _parse_date_posted(s: str) -> datetime | None:
    """Parse date string like 'February 09, 2026' to datetime."""
    if not s or not s.strip():
        return None
    try:
        return datetime.strptime(s.strip(), "%B %d, %Y")
    except ValueError:
        return None


def _parse_job_type(s: str) -> JobType | None:
    """Map job status string from the table to JobType enum."""
    if not s or not s.strip():
        return None
    lower = s.strip().lower()
    for jt in JobType:
        if jt.value.lower() in lower or lower in jt.value.lower():
            return jt
    if "intern" in lower or "internship" in lower:
        return JobType.INTERN
    if "full" in lower and "time" in lower:
        return JobType.FULL_TIME
    if "part" in lower and "time" in lower:
        return JobType.PART_TIME
    if "freelance" in lower:
        return JobType.FREELANCE
    if "volunteer" in lower or "unpaid" in lower:
        return JobType.UNPAID
    return None


def _parse_salary_range(s: str) -> list[float] | None:
    """Try to extract one or two numbers from salary string (e.g. '$18hr' or '$50,000 - $60,000'). Returns None if unparseable."""
    if not s or not s.strip():
        return None
    # Remove $ and commas, find numbers
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    if not numbers:
        return None
    try:
        return [float(n) for n in numbers[:2]]  # at most two (min-max)
    except ValueError:
        return None


def _parse_salary_unit(s: str) -> str | None:
    """Infer salary unit from string: 'hourly' if hr/hour/hourly present, else 'annual'. Returns None if no salary text."""
    if not s or not s.strip():
        return None
    lower = s.strip().lower()
    if re.search(r"\b(hr|/hr|hour|/hour|hourly)\b", lower):
        return "hourly"
    # If we have numbers, assume annual when no hourly marker (common on job boards)
    if re.search(r"[\d,]+", lower):
        return "annual"
    return None


def _parse_currency(location: str) -> str:
    """Infer currency from job location using CURRENCY_LOCATION_KEYWORDS in config. Returns ISO-style code."""
    if not location or not location.strip():
        return DEFAULT_CURRENCY
    loc = location.strip().lower()
    for currency_code, keywords in CURRENCY_LOCATION_KEYWORDS.items():
        if any(kw in loc for kw in keywords):
            return currency_code
    return DEFAULT_CURRENCY


def _parse_listing_card(card) -> dict[str, str]:
    """Parse a job card on the listing page (no detail fetch). Returns title, company, location, job_type, href."""
    title = _text(card.find("h3", class_="job-item-title"))
    company = _text(card.find("div", class_="job-item-company"))
    details_ul = card.find("ul", class_="job-item-details")
    li = details_ul.find_all("li") if details_ul else []
    location = _text(li[0]) if len(li) > 0 else ""
    job_type = _text(li[1]) if len(li) > 1 else ""
    href = card.get("href") or ""
    return {"title": title, "company": company, "location": location, "job_type": job_type, "href": href}


def _card_passes_filters(card_data: dict[str, str], filters: dict) -> bool:
    """Return True if the card matches filters (or if no filters). All checks case-insensitive."""
    if not filters:
        return True
    location = (card_data.get("location") or "").lower()
    title = (card_data.get("title") or "").lower()
    job_type = (card_data.get("job_type") or "").lower()

    if filters.get("locations"):
        allowed = [s.lower() for s in filters["locations"] if s]
        if not any(loc in location or location in loc for loc in allowed):
            return False
    if filters.get("role_types"):
        allowed = [s.lower() for s in filters["role_types"] if s]
        if not any(rt in job_type or job_type in rt for rt in allowed):
            return False
    if filters.get("job_titles"):
        allowed = [s.lower() for s in filters["job_titles"] if s]
        if not any(kw in title for kw in allowed):
            return False
    return True


def scrape_journalism_jobs(filters: dict | None = None) -> list[Job]:
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
        job_links = results.find_all("a", class_="job-item")
        if not job_links:
            break
        for a in job_links:
            card_data = _parse_listing_card(a)
            href = (card_data.get("href") or "").strip()
            if not href:
                continue
            if filters and not _card_passes_filters(card_data, filters):
                continue
            job_url = href if href.startswith("http") else BASE_URL + href
            card_company = (card_data.get("company") or "").strip()
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
        title = _text(title_el) or "Unknown"
        h2 = container.find("h2")
        company_el = h2.find("a") if h2 else None
        company = (_text(company_el) or card_company or "").strip()
        company_url = company_el.get("href") if company_el else None
        location_el = container.find("h3")
        location = _text(location_el).strip() or None

        details = _parse_details_table(job_view)
        description = _get_description(job_view)
        date_posted = _parse_date_posted(details.get("Date Posted", ""))
        job_type = _parse_job_type(details.get("Job Status", ""))
        salary_str = details.get("Salary", "")
        salary_range = _parse_salary_range(salary_str)
        salary_unit = _parse_salary_unit(salary_str)
        industry_str = details.get("Industry", "").strip()
        industries = [industry_str] if industry_str else None
        currency = _parse_currency(location or "")

        try:
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
