"""
Shared utilities for job-board scrapers.
Helpers for parsing HTML, dates, salary, job type, currency, and card filters
so individual scraper files stay lean and logic can be reused across sources.
"""
import re
from datetime import datetime, timedelta, timezone

from backend.config import CURRENCY_LOCATION_KEYWORDS, DEFAULT_CURRENCY
from backend.database.models import JobDB
from backend.models.Job import Job
from backend.utils.enums import JobType, SalaryUnit


def text(el) -> str:
    """Get stripped text from an element, or '' if None."""
    return el.get_text(strip=True) if el else ""


def strip_company_from_title(title: str) -> str:
    """Remove trailing ' - Company Name' from title when the page uses 'Title - Company' format.
    Returns the part before the first ' - ' (stripped), or the whole title if no ' - '."""
    if not title or " - " not in title:
        return (title or "").strip()
    return title.split(" - ", 1)[0].strip() or title.strip()


def parse_details_table(job_view) -> dict[str, str]:
    """Parse a job details table (Date Posted, Industry, Job Status, Salary, etc.) into a dict.
    Expects table with <tr><th>...</th><td>...</td></tr> rows. job_view is a BeautifulSoup element."""
    details = {}
    table = job_view.find("table", class_="table") if job_view else None
    if not table:
        return details
    tbody = table.find("tbody") or table
    for row in tbody.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            details[text(th)] = text(td)
    return details


def get_description_after_h2(job_view, h2_pattern: str = r"Description", stop_at_apply_id: str = "apply") -> str:
    """Get full description: everything after the first h2 matching h2_pattern until an anchor with id stop_at_apply_id or next h2.
    job_view is a BeautifulSoup element. Other scrapers can pass a different h2_pattern or stop_at_apply_id if needed."""
    if not job_view:
        return ""
    h2 = job_view.find("h2", string=re.compile(h2_pattern, re.I))
    if not h2:
        return ""
    parts = []
    for sib in h2.find_next_siblings():
        if sib.name == "a" and sib.get("id") == stop_at_apply_id:
            break
        if sib.name == "h2":
            break
        if sib.name in ("p", "ul", "ol", "li", "div") and "apply" not in (sib.get("class") or []):
            parts.append(sib.get_text(separator=" ", strip=True))
    return "\n\n".join(p for p in parts if p)


def parse_date_posted(s: str, fmt: str = "%B %d, %Y") -> datetime | None:
    """Parse date string (e.g. 'February 09, 2026') to datetime. fmt can be overridden for other locales."""
    if not s or not s.strip():
        return None
    try:
        return datetime.strptime(s.strip(), fmt)
    except ValueError:
        return None


def parse_relative_posted(s: str, now: datetime | None = None) -> datetime | None:
    """Parse relative time strings like '10 hours ago', '4 days ago', '2 weeks ago' into a datetime.
    Uses `now` as the reference time (default: UTC now). Returns None if unparseable."""
    if not s or not s.strip():
        return None
    ref = now or datetime.now(timezone.utc)
    # Strip timezone for timedelta math if ref is timezone-aware (we'll keep naive or replace at end)
    if ref.tzinfo:
        ref = ref.replace(tzinfo=None) + (ref.utcoffset() or timedelta(0))
    text_lower = s.strip().lower()
    if text_lower in ("just now", "today"):
        return ref
    m = re.match(r"(\d+)\s*(minute|hour|day|week|month|year)s?\s*ago", text_lower)
    if not m:
        return None
    num = int(m.group(1))
    unit = m.group(2)
    if unit == "minute":
        delta = timedelta(minutes=num)
    elif unit == "hour":
        delta = timedelta(hours=num)
    elif unit == "day":
        delta = timedelta(days=num)
    elif unit == "week":
        delta = timedelta(weeks=num)
    elif unit == "month":
        delta = timedelta(days=num * 30)
    elif unit == "year":
        delta = timedelta(days=num * 365)
    else:
        return None
    return ref - delta


def parse_job_type(s: str) -> JobType | None:
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


def parse_salary_range(s: str) -> list[float] | None:
    """Try to extract one or two numbers from salary string (e.g. '$18hr' or '$50,000 - $60,000'). Returns None if unparseable."""
    if not s or not s.strip():
        return None
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    if not numbers:
        return None
    try:
        return [float(n) for n in numbers[:2]]
    except ValueError:
        return None


def parse_salary_unit(s: str) -> str | None:
    """Infer salary unit from string: 'hourly' if hr/hour/hourly present, else 'annual'. Returns None if no salary text."""
    if not s or not s.strip():
        return None
    lower = s.strip().lower()
    if re.search(r"\b(hr|/hr|hour|/hour|hourly)\b", lower):
        return "hourly"
    if re.search(r"[\d,]+", lower):
        return "annual"
    return None


def parse_salary_from_description(description: str) -> dict:
    """Try to extract salary min, max, and unit from free-text description.
    Returns dict with salary_min, salary_max (float or None), salary_unit_str ('hourly'|'annual').
    Avoids matching years of experience (e.g. '3+ years')."""
    result = {"salary_min": None, "salary_max": None, "salary_unit_str": "annual"}
    if not description or not description.strip():
        return result
    # Only look in chunks that look salary-related to avoid "3+ years", "2 years experience"
    salary_keywords = r"(?:salary|salary range|compensation|pay|wage|stipend|\$|usd)"
    # Match $X or $X - $Y or $X-$Y or $X to $Y (with optional commas and decimals)
    dollar_pattern = re.compile(
        r"\$[\s]*([\d,]+)(?:\.\d+)?\s*(?:-\s*\$?\s*([\d,]+)(?:\.\d+)?|\s*to\s*\$?\s*([\d,]+)(?:\.\d+)?)?",
        re.I,
    )
    # Find positions of salary-like context (near $ or keywords)
    candidates = []
    for m in dollar_pattern.finditer(description):
        start = max(0, m.start() - 80)
        end = min(len(description), m.end() + 80)
        chunk = description[start:end].lower()
        if not re.search(salary_keywords, chunk):
            continue
        is_hourly = bool(re.search(r"\b(hr|/hr|hour|/hour|hourly|per hour)\b", chunk))
        raw_vals = [m.group(1)]
        if m.group(2):
            raw_vals.append(m.group(2))
        elif m.group(3):
            raw_vals.append(m.group(3))
        nums = []
        for v in raw_vals:
            try:
                n = float(v.replace(",", ""))
                nums.append(n)
            except ValueError:
                continue
        if not nums:
            continue
        # Sanity: annual typically 20k–2M, hourly typically 10–500
        if is_hourly:
            if any(n < 5 or n > 500 for n in nums):
                continue
            unit = "hourly"
        else:
            if any(n < 1000 or n > 10_000_000 for n in nums):
                continue
            unit = "annual"
        min_val = min(nums)
        max_val = max(nums) if len(nums) > 1 else min_val
        candidates.append((min_val, max_val, unit))
    if not candidates:
        return result
    # Take first plausible candidate
    min_val, max_val, unit = candidates[0]
    result["salary_min"] = min_val
    result["salary_max"] = max_val
    result["salary_unit_str"] = unit
    return result


def parse_date_flexible(s: str) -> datetime | None:
    """Try to parse a date string with multiple common formats."""
    if not s or not s.strip():
        return None
    s = s.strip()
    formats = [
        "%B %d, %Y",   # February 09, 2026
        "%b %d, %Y",   # Feb 09, 2026
        "%Y-%m-%d",    # 2026-02-09
        "%m/%d/%Y",    # 02/09/2026
        "%d/%m/%Y",    # 09/02/2026
        "%B %Y",       # February 2026
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_currency(location: str) -> str:
    """Infer currency from job location using CURRENCY_LOCATION_KEYWORDS in config. Returns ISO-style code."""
    if not location or not location.strip():
        return DEFAULT_CURRENCY
    loc = location.strip().lower()
    for currency_code, keywords in CURRENCY_LOCATION_KEYWORDS.items():
        if any(kw in loc for kw in keywords):
            return currency_code
    return DEFAULT_CURRENCY


def card_passes_filters(card_data: dict[str, str], filters: dict) -> bool:
    """Return True if the card matches filters (or if no filters). All checks case-insensitive.
    Expects filters with optional keys: locations, role_types, job_titles (lists of strings)."""
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

def job_db_to_pydantic(db: JobDB) -> Job:
    """Convert a JobDB row to a Pydantic Job for API responses."""
    salary_range: list[float] | None = None
    if db.salary_min is not None or db.salary_max is not None:
        salary_range = [db.salary_min, db.salary_max]
        salary_range = [x for x in salary_range if x is not None]
        if not salary_range:
            salary_range = None
    job_type_enum = next((jt for jt in JobType if jt.value == db.job_type), None) if db.job_type else None
    salary_unit_enum = SalaryUnit(db.salary_unit) if db.salary_unit in ("hourly", "annual") else None
    industries_list = [s.strip() for s in db.industries.split(",") if s.strip()] if db.industries else None
    return Job(
        id=db.id,
        application_url=db.application_url,
        title=db.title,
        company=db.company,
        company_url=db.company_url,
        description=db.description,
        location=db.location,
        job_type=job_type_enum,
        salary_range=salary_range,
        salary_unit=salary_unit_enum,
        currency=db.currency,
        industries=industries_list,
        source=db.source,
        date_posted=db.date_posted,
        application_deadline=db.application_deadline,
        created_at=db.created_at,
    )
