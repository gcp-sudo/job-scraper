
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Supabase Configuration ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# --- Database & Storage Names ---
TABLE_MAP = {
    "linkedin": "jobs_linkedin",
    "gulf": "jobs_gulf",
    "startup": "jobs_startup",
    "freelance": "jobs_freelance",
    "fresher": "jobs_fresher",
}
CUSTOMIZED_RESUMES_TABLE = "customized_resumes"
BASE_RESUME_TABLE = "base_resume"
PERSONALIZED_RESUMES_BUCKET = "personalized_resumes"

# --- Scraping Configuration ---
SCRAPING_SOURCES = ["linkedin", "gulf", "startup", "freelance", "fresher"]

# Detailed search configuration for each source
SEARCH_CONFIG = {
    "linkedin": {
        "queries": ["DevOps Engineer", "Cloud Engineer", "SRE"],
        "location": "India",
        "results_to_scrape": 50, # Max jobs to scrape per query
        # --- LinkedIn Specific Filters (see README for details) ---
        "geo_id": 102713980, # Geo ID for India
        "job_posting_date": "r86400", # Last 24 hours
        "job_type": "F", # Full-time
        "work_type": 2 # Remote
    },
    "gulf": {
        "queries": ["DevOps Engineer", "Cloud Engineer"], 
        "location": "United Arab Emirates"
    },
    "startup": {
        "queries": ["Founding Engineer", "Early-stage startup"], 
        "location": "Global"
    },
    "freelance": {
        "queries": ["Freelance DevOps", "Cloud Consultant"], 
        "location": "Remote"
    },
    "fresher": {
        "queries": ["Junior DevOps", "Graduate Cloud Engineer"], 
        "location": "India"
    },
}

# --- Job Processing Limits ---
JOBS_TO_SCORE_PER_RUN = 50
JOBS_TO_CUSTOMIZE_PER_RUN = 10
MINIMUM_SCORE_FOR_AUTOGENERATE = 7 # Score out of 10

# --- Job Maintenance Settings ---
JOB_EXPIRY_DAYS = 30
JOB_CHECK_DAYS = 3
JOB_DELETION_DAYS = 60 # Archive jobs older than this
JOB_CHECK_LIMIT = 50

# --- LLM Configuration ---
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()

LLM_CONFIG = {
    "gemini": {
        "model": "gemini/gemini-1.5-flash-latest",
        "fallback_models": ["gpt-4o-mini", "groq/llama3-70b-8192"],
    },
    "openai": {
        "model": "gpt-4o-mini",
        "fallback_models": ["gemini/gemini-1.5-flash-latest", "groq/llama3-70b-8192"],
    },
    "groq": {
        "model": "groq/llama3-70b-8192",
        "fallback_models": ["gemini/gemini-1.5-flash-latest", "gpt-4o-mini"],
    }
}
