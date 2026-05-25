import os
from dotenv import load_dotenv

load_dotenv()

# =================================================================
# 1. CORE SYSTEM CONFIGURATION
# =================================================================

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

SUPABASE_TABLE_NAME: str = "jobs"
SUPABASE_CUSTOMIZED_RESUMES_TABLE_NAME = "customized_resumes"

SUPABASE_STORAGE_BUCKET = "personalized_resumes"
SUPABASE_RESUME_STORAGE_BUCKET = "resumes"

SUPABASE_BASE_RESUME_TABLE_NAME = "base_resume"

BASE_RESUME_PATH = "resume.json"

# API Keys
# Priority order: LLM_API_KEY → GEMINI_API_KEY → OPENAI_API_KEY → GROQ_API_KEY
LLM_API_KEY = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("GROQ_API_KEY")
)

# Provider-specific API keys (for direct provider access if needed)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# =================================================================
# 2. USER PREFERENCES
# =================================================================

# --- LLM Settings ---

# Primary LLM Model
# Examples:
# "gemini/gemini-2.5-flash-lite"
# "gemini/gemini-3.1-flash-lite-preview"
# "gpt-4o-mini"
# "groq/llama-3.3-70b-versatile"

LLM_MODEL = "gemini/gemini-2.5-flash-lite"

# LLM Fallback Models (in priority order)
# If the primary model fails or hits rate limits, the client will automatically
# attempt these fallback models in the specified order
# Priority: Gemini (primary) → OpenAI → Groq
LLM_FALLBACK_MODELS = [
    "gpt-4o-mini",  # OpenAI fallback
    "groq/llama-3.3-70b-versatile",  # Groq secondary fallback
]

# --- Job Filtering ---
# Keywords to check for in job descriptions. If a job description doesn't
# contain any of these keywords, it will be skipped for LLM scoring.
# Set to an empty list to disable keyword filtering.
TARGET_KEYWORDS = [
    "Kubernetes",
    "GCP",
    "Terraform",
    "DevOps",
    "Cloud Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",
    "SRE",
    "CI/CD",
    "Docker",
    "GKE",
    "Google Cloud",
    "DevSecOps",
    "Observability",
]

# =================================================================
# LINKEDIN SEARCH CONFIGURATION
# =================================================================

LINKEDIN_SEARCH_QUERIES = [
    "DevOps Engineer",
    "Cloud Engineer",
    "GCP Engineer",
    "GCP DevOps Engineer",
    "Google Cloud Engineer",
    "Kubernetes Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",
    "Terraform Engineer",
    "Site Reliability Engineer",
    "SRE",
    "DevSecOps Engineer",
    "CI/CD Engineer",
    "Release Engineer",
    "Cloud Platform Engineer",
    "Observability Engineer",
    "Docker Kubernetes Engineer",
    "GKE Engineer",
    "Cloud Native Engineer"
]

# Location
LINKEDIN_LOCATION = "India"

# India GEO ID
LINKEDIN_GEO_ID = 102713980

# Job Type
# F=Full-time
# C=Contract
# P=Part-time
# T=Temporary
# I=Internship

LINKEDIN_JOB_TYPE = "F"

# Date Filter
# r86400 = Past 24h
# r604800 = Past week

LINKEDIN_JOB_POSTING_DATE = "r86400"

# Work Type
# 1 = Onsite
# 2 = Remote
# 3 = Hybrid

LINKEDIN_F_WT = 2

# =================================================================
# CAREERS FUTURE SEARCH CONFIGURATION
# =================================================================

CAREERS_FUTURE_SEARCH_QUERIES = [
    "DevOps Engineer",
    "Cloud Engineer",
    "GCP Engineer",
    "Kubernetes Engineer",
    "Platform Engineer",
    "Terraform Engineer",
    "Infrastructure Engineer",
    "SRE",
    "Cloud Platform Engineer"
]

CAREERS_FUTURE_SEARCH_CATEGORIES = [
    "Information Technology"
]

CAREERS_FUTURE_SEARCH_EMPLOYMENT_TYPES = [
    "Full Time"
]

# =================================================================
# PROCESSING LIMITS
# =================================================================

SCRAPING_SOURCES = [
    "linkedin"
    # "careers_future"
]

JOBS_TO_SCORE_PER_RUN = 20

JOBS_TO_CUSTOMIZE_PER_RUN = 5

MAX_JOBS_PER_SEARCH = {
    "linkedin": 25,
    "careers_future": 10,
}

# =================================================================
# 3. ADVANCED SYSTEM SETTINGS
# =================================================================

LLM_MAX_RPM = 10

LLM_MAX_RETRIES = 3

LLM_RETRY_BASE_DELAY = 10

# 0 = unlimited
LLM_DAILY_REQUEST_BUDGET = 0

LLM_REQUEST_DELAY_SECONDS = 8

LINKEDIN_MAX_START = 1

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3

RETRY_DELAY_SECONDS = 15

JOB_EXPIRY_DAYS = 30

JOB_CHECK_DAYS = 3

JOB_DELETION_DAYS = 60

JOB_CHECK_LIMIT = 50

ACTIVE_CHECK_TIMEOUT = 20

ACTIVE_CHECK_MAX_RETRIES = 2

ACTIVE_CHECK_RETRY_DELAY = 10
