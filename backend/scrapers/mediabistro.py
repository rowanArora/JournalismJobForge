import json
import re
import time

from bs4 import BeautifulSoup
import requests
from sqlmodel import select
from tqdm import tqdm
from backend.database.models import JobDB
from backend.models.Job import Job
from backend.utils.enums import SalaryUnit
from backend.utils.scraper_utils import (
    card_passes_filters,
    parse_currency,
    parse_date_flexible,
    parse_job_type,
    parse_relative_posted,
    parse_salary_range,
    parse_salary_from_description,
    parse_salary_unit,
    strip_company_from_title,
    text,
)
from backend.utils.selenium_utils import create_driver, fetch_html
from selenium.webdriver.common.by import By
from backend.database.connection import Session, engine


BASE_URL = "https://www.mediabistro.com"
SOURCE_NAME = "mediabistro.com"


def _listing_url() -> str:
    return (
        "https://www.mediabistro.com/jobs?keyword=&location="
    )


def _split_company_location(company_location: str, fallback_company: str) -> tuple[str, str | None]:
    """Split 'Company, LLC, City, State USA' or 'Company, City, State, Country' into (company, location)."""
    if not company_location or not company_location.strip():
        return (fallback_company or "", None)
    parts = [p.strip() for p in company_location.split(",") if p.strip()]
    n = len(parts)
    if n == 0:
        return (fallback_company or "", None)
    if n == 1:
        return (parts[0] or fallback_company, None)
    if n == 2:
        return (parts[0] or fallback_company, parts[1] or None)
    # 3+ parts: treat trailing segments as location; avoid pulling "LLC"/"Inc" into location
    company_suffixes = {"llc", "inc", "ltd", "corp", "co.", "lp"}
    # "Company, Inc., Location" (n=3) or "Company, Inc., City, State USA" (n=4) -> suffix at index 1
    if n >= 3 and parts[1].upper().rstrip(".") in company_suffixes:
        company = ", ".join(parts[:2])
        location = ", ".join(parts[2:]) if n > 2 else None
        return (company.strip() or fallback_company, location.strip() if location else None)
    if n >= 4 and parts[-3].upper().rstrip(".") in company_suffixes:
        company = ", ".join(parts[:2])
        location = ", ".join(parts[2:])
    if n >= 4 and parts[-3].upper().rstrip(".") in company_suffixes:
        location = ", ".join(parts[-2:])
        company = ", ".join(parts[:-2])
    elif n >= 4:
        location = ", ".join(parts[-3:])
        company = ", ".join(parts[:-3])
    else:
        location = ", ".join(parts[-2:])
        company = parts[0]
    return (company.strip() or fallback_company, location.strip() or None)


# Pattern to extract "10 hours ago", "4 days ago", "just now", etc. from card text
_RELATIVE_POSTED_PATTERN = re.compile(
    r"\d+\s*(?:minute|hour|day|week|month|year)s?\s*ago|just now|today",
    re.I,
)


def _parse_listing_card(card) -> dict[str, str]:
    """Parse a job card on the listing page (no detail fetch). Returns title, company, location, job_type, href, posted_relative.
    The 'X hours ago' / 'X days ago' text is in a <p class="... text-muted-foreground">; use the other <p> for location."""
    raw_title = text(card.find("h4"))
    title = strip_company_from_title(raw_title)
    company = text(card.find("small"))
    time_p = card.find("p", class_=lambda c: c and "text-muted-foreground" in (c or ""))
    location = ""
    for p in card.find_all("p"):
        if p == time_p:
            continue
        location = text(p).strip()
        break
    href = card.get("href") or ""
    posted_relative = ""
    if time_p:
        time_text = text(time_p).strip()
        if _RELATIVE_POSTED_PATTERN.search(time_text):
            posted_relative = time_text
    if not posted_relative:
        card_text = card.get_text(separator=" ", strip=True) or ""
        m = _RELATIVE_POSTED_PATTERN.search(card_text)
        posted_relative = m.group(0).strip() if m else ""
    return {
        "title": title,
        "company": company,
        "location": location,
        "job_type": "",
        "href": href,
        "posted_relative": posted_relative,
    }


def _parse_mediabistro_detail(job_soup, card_company: str) -> dict | None:
    """Parse MediaBistro job detail page. Returns a dict with title, company, location, description, salary_min, salary_max, job_type, etc., or None if structure not found."""
    h1 = job_soup.find("h1", class_=lambda c: c and "font-semibold" in (c or ""))
    if not h1:
        h1 = job_soup.find("h1")
    if not h1:
        return None
    title = strip_company_from_title(text(h1) or "Unknown")

    # Company + location in one p: "Trinity Health, Fresno, CA, United States" or "Kittleman & Associates, LLC, Denver, CO USA"
    main_div = h1.find_parent("div", class_=lambda c: c and "w-full" in (c or ""))
    if not main_div:
        return None
    first_p = main_div.find("p", class_=lambda c: c and "text-base" in (c or ""))
    company_location = text(first_p) if first_p else ""
    company, location = _split_company_location(company_location, card_company)

    # Salary and duration in div with pt-4
    pt4 = main_div.find("div", class_=lambda c: c and "pt-4" in (c or ""))
    salary_min = salary_max = None
    job_type_str = None
    if pt4:
        for p in pt4.find_all("p", class_=lambda c: c and "text-base" in (c or "")):
            t = text(p)
            if "Salary min:" in t:
                nums = parse_salary_range(t)
                if nums:
                    salary_min = nums[0]
            elif "Salary max:" in t:
                nums = parse_salary_range(t)
                if nums:
                    salary_max = nums[0]
            elif "Duration:" in t:
                job_type_str = t.replace("Duration:", "").strip()

    # Description: after <hr class="my-5">
    hr = job_soup.find("hr", class_=lambda c: c and "my-5" in (c or ""))
    description = ""
    if hr:
        next_div = hr.find_next_sibling("div")
        if next_div:
            desc_inner = next_div.find("div", class_=lambda c: c and "[&" in (c or ""))
            if desc_inner:
                description = desc_inner.get_text(separator="\n", strip=True)
            else:
                description = next_div.get_text(separator="\n", strip=True)

    # Salary fallback from description when structured block had no salary
    salary_unit_str_from_desc = None
    if salary_min is None and salary_max is None and description:
        desc_salary = parse_salary_from_description(description)
        if desc_salary.get("salary_min") is not None:
            salary_min = desc_salary["salary_min"]
            salary_max = desc_salary.get("salary_max") or salary_min
        if desc_salary.get("salary_unit_str"):
            salary_unit_str_from_desc = desc_salary["salary_unit_str"]

    salary_range = None
    if salary_min is not None or salary_max is not None:
        salary_range = [salary_min or 0, salary_max or salary_min or 0]
        salary_range = [x for x in salary_range if x is not None]
    salary_unit_str = parse_salary_unit(
        f"Salary min: {salary_min} Salary max: {salary_max}" if (salary_min or salary_max) else ""
    ) or salary_unit_str_from_desc or "annual"
    job_type = parse_job_type(job_type_str or "")
    currency = parse_currency(location or "")

    # Optional: company URL (link that looks like external company site, not Apply/Save/mediabistro)
    company_url = None
    for a in (main_div or job_soup).find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or "mediabistro.com" in href or "/jobs" in href:
            continue
        link_text = text(a).lower()
        if "apply" in link_text or "save" in link_text or "signup" in href:
            continue
        if href.startswith("http"):
            company_url = href
            break
        if href.startswith("/"):
            company_url = BASE_URL.rstrip("/") + href
            break

    # Optional: date posted (search for "posted", "date posted", etc. in main content)
    date_posted = None
    full_text = (main_div.get_text(separator=" ", strip=True) if main_div else "") + " " + description
    for pattern in [r"(?:posted|date posted|published)\s*[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})", r"(?:posted|date posted)\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})"]:
        m = re.search(pattern, full_text, re.I)
        if m:
            date_posted = parse_date_flexible(m.group(1))
            if date_posted:
                break

    return {
        "title": title,
        "company": company,
        "company_url": company_url,
        "location": location,
        "description": description or None,
        "date_posted": date_posted,
        "job_type": job_type,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_range": salary_range,
        "salary_unit_str": salary_unit_str,
        "salary_unit": SalaryUnit(salary_unit_str) if salary_unit_str in ("hourly", "annual") else None,
        "industries": None,
        "currency": currency,
    }

def scrape_media_bistro(filters: dict | None = None) -> list[Job]:
    driver = None
    try:
        # Wait for at least one job posting to be present.
        driver = create_driver(headless=True, logging=False)
        url = _listing_url()
        locator = (By.CLASS_NAME, "contents")
        fetch_html(driver, url, locator)

        # Count the current number of cards
        prev_count = len(driver.find_elements(By.CLASS_NAME, "contents"))
        max_scrolls = 100
        scroll_sleep = 1

        while True:
            # Scroll down to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for the new content to load
            time.sleep(scroll_sleep)

            # Count the current number of cards
            curr_count = len(driver.find_elements(By.CLASS_NAME, "contents"))

            # If the current number of cards is the same as before then exit the loop as there are no more jobs to load
            if curr_count == prev_count:
                break

            prev_count = curr_count
            max_scrolls -= 1
            if max_scrolls <= 0:
                break

        page_source = driver.page_source
    finally:
        if driver is not None:
            driver.quit()

    # All jobs have been loaded (or capacity was hit) so we can use BeautifulSoup now to parse the HTML
    with Session(engine) as session:
        # Phase 1: collect job URLs that pass filters (from listing pages only); keep card company and posted_relative
        to_fetch: list[tuple[str, str, str]] = []
        dashboard_soup = BeautifulSoup(page_source, "html.parser")

        results = dashboard_soup.find_all(class_="contents")
        if not results:
            return []

        for job_card in results:
            a = job_card.find("a")
            if not a:
                continue
            card_data = _parse_listing_card(a)

            href = (card_data.get("href") or "").strip()
            if not href:
                continue

            if filters and not card_passes_filters(card_data, filters):
                continue

            job_url = href if href.startswith("http") else BASE_URL + href
            card_company = (card_data.get("company") or "").strip()
            posted_relative = (card_data.get("posted_relative") or "").strip()

            statement = select(JobDB).where(JobDB.application_url == job_url)
            result = session.exec(statement)
            exists = result.first()
            if not exists:
                to_fetch.append((job_url, card_company, posted_relative))

        # Phase 2: fetch each job detail with progress bar
        jobs_list: list[Job] = []
        for job_url, card_company, posted_relative in tqdm(to_fetch, desc="Scraping jobs", unit=" job"):
            try:
                page_resp = requests.get(job_url)
                page_resp.raise_for_status()
            except requests.RequestException:
                continue

            job_soup = BeautifulSoup(page_resp.content, "html.parser")
            parsed = _parse_mediabistro_detail(job_soup, card_company)
            if parsed:
                try:
                    date_posted = parse_relative_posted(posted_relative) or parsed.get("date_posted")

                    db_job = JobDB(
                        application_url=job_url,
                        title=parsed["title"],
                        company=parsed["company"],
                        company_url=parsed.get("company_url"),
                        description=parsed["description"] or None,
                        location=parsed.get("location") or None,
                        job_type=parsed["job_type"].value if parsed.get("job_type") else None,
                        salary_min=parsed.get("salary_min"),
                        salary_max=parsed.get("salary_max"),
                        salary_unit=parsed.get("salary_unit_str"),
                        currency=parsed["currency"],
                        industries=", ".join(parsed["industries"]) if parsed.get("industries") else None,
                        source=SOURCE_NAME,
                        date_posted=date_posted,
                        application_deadline=None,
                    )
                    session.add(db_job)

                    job = Job(
                        application_url=job_url,
                        title=parsed["title"],
                        company=parsed["company"],
                        company_url=parsed.get("company_url"),
                        description=parsed["description"] or None,
                        location=parsed.get("location"),
                        job_type=parsed.get("job_type"),
                        salary_range=parsed.get("salary_range"),
                        salary_unit=parsed.get("salary_unit"),
                        currency=parsed["currency"],
                        date_posted=date_posted,
                        industries=parsed.get("industries"),
                        source=SOURCE_NAME,
                    )
                    jobs_list.append(job)
                except Exception:
                    continue
                time.sleep(0.5)  # be polite to the server
            else:
                continue

        session.commit()
    return jobs_list



if __name__ == "__main__":
    # No filters: scrape all jobs. When User/DB is connected, build filters from user
    # (e.g. user.preferred_locations, user.preferred_job_titles, [jt.value for jt in user.preferred_role_types]).
    filters = None
    print("Scraping MediaBistro.com (no filters)...")
    start = time.perf_counter()
    jobs = scrape_media_bistro(filters=filters)
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
