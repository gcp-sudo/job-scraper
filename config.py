import os
from dotenv import load_dotenv

load_dotenv()

# =================================================================
# 1. CORE SYSTEM CONFIGURATION
# =================================================================

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# --- Multi-table Mapping ---
SUPABASE_TABLE_MAP = {
    "linkedin": "jobs_linkedin",
    "gulf": "jobs_gulf",
    "startup": "jobs_startup",
    "freelance": "jobs_freelance",
    "fresher": "jobs_fresher",
}

SUPABASE_CUSTOMIZED_RESUMES_TABLE_NAME = "customized_resumes"
SUPABASE_STORAGE_BUCKET = "personalized_resumes"
SUPABASE_RESUME_STORAGE_BUCKET = "resumes"
SUPABASE_BASE_RESUME_TABLE_NAME = "base_resume"
BASE_RESUME_PATH = "resume.json"

# --- API Keys ---
LLM_API_KEY = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("GROQ_API_KEY")
)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# =================================================================
# 2. USER PREFERENCES
# =================================================================

# --- LLM Settings ---
LLM_MODEL = "gemini/gemini-2.5-flash-lite"
LLM_FALLBACK_MODELS = [
    "gpt-4o-mini",
    "groq/llama-3.3-70b-versatile",
]

# --- Job Filtering ---
TARGET_KEYWORDS = [
    "Kubernetes", "GCP", "Terraform", "DevOps", "Cloud Engineer",
    "Platform Engineer", "Infrastructure Engineer", "SRE", "CI/CD",
    "Docker", "GKE", "Google Cloud", "DevSecOps", "Observability",
]

# =================================================================
# 3. SEARCH CONFIGURATION
# =================================================================

# --- Enabled Scraping Sources ---
SCRAPING_SOURCES = [
    "linkedin",
    "gulf",
    "startup",
    "freelance",
    "fresher"
]

# --- Search Parameters for Each Source ---
SEARCH_CONFIG = {
    "linkedin": {
        "search_queries": ["DevOps Engineer", "Cloud Engineer", "SRE"],
        "location": "India",
        "geo_id": 102713980,
        "job_type": "F",
        "job_posting_date": "r86400",
        "work_type": 2,
    },
    "gulf": {
        "search_queries": ["DevOps Engineer", "Cloud Engineer"],
        "location": "United Arab Emirates",
        "job_type": "Full Time",
    },
    "startup": {
        "search_queries": ["Founding Engineer", "Early-stage startup"],
        "location": "Global",
        "job_type": "Full Time",
    },
     "freelance": {
        "search_queries": ["Freelance DevOps", "Cloud Consultant"],
        "location": "Remote",
    },
    "fresher": {
        "search_queries": ["Junior DevOps", "Graduate Cloud Engineer"],
        "location": "India",
    }
}


# =================================================================
# 4. PROCESSING LIMITS
# =================================================================

JOBS_TO_SCORE_PER_RUN = 20
JOBS_TO_CUSTOMIZE_PER_RUN = 5

MAX_JOBS_PER_SEARCH = {
    "linkedin": 25,
    "gulf": 15,
    "startup": 10,
    "freelance": 20,
    "fresher": 10,
}


# =================================================================
# 5. ADVANCED SYSTEM SETTINGS
# =================================================================

LLM_MAX_RPM = 10
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 10
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
