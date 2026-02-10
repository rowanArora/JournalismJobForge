# JournalismJobForge

A job-finding platform for people who want to build a career in **journalism, media, and the arts**. It scrapes relevant job listings, lets you track applications, and (coming soon) will offer swipe-style matching, deadline reminders, and AI help for resumes and cover letters.

---

## Who it's for

JournalismJobForge is built first and foremost for **students and early-career folks** aiming to work in:

- **Journalism** — reporting, editing, producing, fact-checking
- **Media & content** — digital content, social media, video, audio
- **The arts** — documentary, multimedia storytelling, creative roles

If you're looking for full-time, part-time, freelance, or internship roles in these areas and want one place to discover jobs, stay on top of deadlines, and manage applications, this project is for you.

---

## What it does (current & planned)

| Feature | Status |
|--------|--------|
| Scrape journalism/media jobs from job boards | ✅ Working |
| Filter by location, job title, role type | ✅ (filters will be per-user once DB is connected) |
| Salary parsing (hourly vs annual) and currency inference | ✅ |
| FastAPI backend with `/jobs` placeholder | ✅ |
| User model (preferences, resume/CV paths, display settings) | ✅ In code; DB not yet connected |
| Swipe-style job matching | 🔜 Planned |
| Deadline & calendar reminders | 🔜 Planned |
| AI recommendations, resume/cover letter help | 🔜 Planned |
| Application tracking & email digests | 🔜 Planned |

---

## Project structure

```
JournalismJobForge/
├── backend/
│   ├── app.py              # FastAPI app
│   ├── config.py           # App config (currency, salary display, location→currency mapping)
│   ├── apis/
│   │   └── routes.py       # API routes (e.g. GET /jobs)
│   ├── database/           # DB connection (to be wired up)
│   ├── models/
│   │   ├── Job.py          # Job model (title, company, salary, location, etc.)
│   │   └── User.py         # User model (preferences, resumes, display settings)
│   ├── scrapers/
│   │   └── journalismjobs.py   # JournalismJobs.com scraper
│   └── utils/
│       └── enums.py        # JobType, Currency, UserTypes
├── requirements.txt
├── requirements-dev.txt   # pre-commit, ruff (optional)
├── .pre-commit-config.yaml
├── README.md
└── .gitignore
```

---

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/JournalismJobForge.git
   cd JournalismJobForge
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Pre-commit (optional)** — run checks before each commit (lint, format, trailing whitespace, etc.):
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```
   Before committing, you can run all hooks on the repo: `pre-commit run --all-files`.

---

## Running the app

### Backend API

From the project root:

```bash
uvicorn backend.app:app --reload
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

### Scraper (JournalismJobs.com)

From the project root, with your venv activated:

```bash
python -m backend.scrapers.journalismjobs
```

- Fetches job listings from JournalismJobs.com.
- With no filters, it scrapes all listed jobs and writes them to `scraped_jobs.json` in the project root.
- When the database and user accounts are connected, filters (locations, job titles, role types) will be driven by each user’s preferences.

---

## Config & user preferences

- **App config** (`backend/config.py`) holds environment-agnostic settings: default currency, salary display mode (hourly vs annual), and location→currency mapping. User-specific preferences (e.g. preferred locations, job titles, role types, skills) are defined on the **User** model and will be stored in the database once it’s connected.

---

## License

See [LICENSE](LICENSE).
