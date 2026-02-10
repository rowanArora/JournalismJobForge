MODES = ["local", "debug", "production"]

# Default currency when location-based inference fails (e.g. empty or unknown).
DEFAULT_CURRENCY = "USD"

# How to display salary in the app: "hourly" or "annual". Jobs store salary_unit per listing;
# this setting is the preferred display (e.g. convert hourly to annual for display when set to "annual").
SALARY_DISPLAY_MODE = "annual"

# Location keywords used to infer salary currency. Check order: GBP -> CAD -> USD -> EUR.
# Each key is the currency code; value is list of substrings to match in job location (case-insensitive).
CURRENCY_LOCATION_KEYWORDS = {
    "GBP": [
        "united kingdom", " u.k.", " uk,", " london", " england", " scotland",
        " wales", " northern ireland",
    ],
    "CAD": [
        "canada", " ontario", " toronto", " quebec", " montreal", " vancouver",
        " british columbia", " alberta", " manitoba", " saskatchewan", " nova scotia", " new brunswick",
    ],
    "USD": [
        "united states", " u.s.", " usa", " usa,", " america", " remote",
        " alabama", " alaska", " arizona", " arkansas", " california", " colorado", " connecticut",
        " delaware", " florida", " georgia", " hawaii", " idaho", " illinois", " indiana", " iowa",
        " kansas", " kentucky", " louisiana", " maine", " maryland", " massachusetts", " michigan",
        " minnesota", " mississippi", " missouri", " montana", " nebraska", " nevada", " new hampshire",
        " new jersey", " new mexico", " new york", " north carolina", " north dakota", " ohio",
        " oklahoma", " oregon", " pennsylvania", " rhode island", " south carolina", " south dakota",
        " tennessee", " texas", " utah", " vermont", " virginia", " washington", " west virginia",
        " wisconsin", " wyoming", " district of columbia",
    ],
    "EUR": [
        " germany", " france", " spain", " italy", " netherlands", " ireland",
        " belgium", " austria", " portugal", " europe", " euro",
    ],
}

# PREFERRED_LOCATIONS = [
#     "San Francisco",
#     "Santa Cruz",
#     "Los Angeles",
#     "California",
#     "Seattle",
#     "Washington",
#     "Chicago",
#     "Illinois",
#     "New York City",
#     "New York",
#     "New Jersey",
#     "Toronto",
#     "Ontario",
#     "Montreal",
#     "Quebec",
#     "Vancouver",
#     "British Columbia",
#     "Canada",
#     "London, United Kingdom",
#     "United Kingdom",
#     "UK",
#     "Remote",
# ]

# JOB_TITLES = [
#     "reporter",
#     "editor",
#     "video editor",
#     "social media",
#     "editing",
#     "news",
#     "audio",
#     "correspondent",
#     "investigative",
#     "multimedia",
#     "producer",
#     "copy editor",
#     "copy editing",
#     "digital content",
#     "content strategist",
#     "growth strategist",
#     "documentary",
#     "fact-check",
#     "content creator",
#     "associate producer",
#     "news producer",
#     "video producer",
# ]

# ROLE_TYPES = [
#     "full-time",
#     "part-time",
#     "freelance",
#     "intern",
#     "unpaid",
# ]

# SKILLS = [
#     "digital content management",
#     "content analytics",
#     "copy editing",
#     "editorial strategy",
#     "investigative research",
#     "multimedia storytelling",
#     "audio editing",
#     "video editing",
#     "seo",
#     "cp style",
#     "canadian press style",
#     "final cut pro",
#     "premiere pro",
#     "adobe premiere",
#     "adobe audition",
#     "avid media composer",
#     "google analytics",
#     "wordpress",
#     "youtube analytics",
#     "instagram",
#     "youtube",
#     "tiktok",
#     "x",
#     "twitter",
#     "reddit",
#     "documentaries",
#     "mini-documentaries",
#     "mini-docs",
#     "mini-docuseries",
#     "interviews",
#     "social justice",
#     "civic",
#     "fact-check",
#     "fact-checking",
#     "short-form",
#     "long-form",
#     "analytics",
#     "open-source intelligence",
#     "osint",
#     "google news initiative",
# ]
