
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# Centralized API key management. The LLM client will pick the correct one.
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
RESUMES_BUCKET = "resumes"
PERSONALIZED_RESUMES_BUCKET = "personalized_resumes"

# --- Scraping Configuration ---
SCRAPING_SOURCES = ["linkedin", "gulf", "startup", "freelance", "fresher"]
SEARCH_CONFIG = {
    "linkedin": {"queries": ["DevOps Engineer", "Cloud Engineer", "SRE"], "location": "India"},
    "gulf": {"queries": ["DevOps Engineer", "Cloud Engineer"], "location": "United Arab Emirates"},
    "startup": {"queries": ["Founding Engineer", "Early-stage startup"], "location": "Global"},
    "freelance": {"queries": ["Freelance DevOps", "Cloud Consultant"], "location": "Remote"},
    "fresher": {"queries": ["Junior DevOps", "Graduate Cloud Engineer"], "location": "India"},
}
MAX_JOBS_PER_SEARCH = 15

# --- Job Processing Limits ---
JOBS_TO_SCORE_PER_RUN = 20
JOBS_TO_CUSTOMIZE_PER_RUN = 5

# --- Job Maintenance Settings ---
JOB_EXPIRY_DAYS = 30
JOB_CHECK_DAYS = 3
JOB_DELETION_DAYS = 60
JOB_CHECK_LIMIT = 50

# --- LLM Configuration ---
# Select your primary provider: "gemini", "openai", or "groq"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()

# Define models and settings for each provider
LLM_CONFIG = {
    "gemini": {
        "model": "gemini/gemini-1.5-flash-latest",
        "fallback_models": ["gpt-4o-mini", "groq/llama3-70b-8192"],
        "max_rpm": 10,
        "max_retries": 3,
        "daily_budget": 0, # No limit
        "retry_base_delay": 10,
        "request_delay": 5,
    },
    "openai": {
        "model": "gpt-4o-mini",
        "fallback_models": ["gemini/gemini-1.5-flash-latest", "groq/llama3-70b-8192"],
        "max_rpm": 15,
        "max_retries": 3,
        "daily_budget": 0,
        "retry_base_delay": 10,
        "request_delay": 3,
    },
    "groq": {
        "model": "groq/llama3-70b-8192",
        "fallback_models": ["gemini/gemini-1.5-flash-latest", "gpt-4o-mini"],
        "max_rpm": 25,
        "max_retries": 2,
        "daily_budget": 0,
        "retry_base_delay": 5,
        "request_delay": 2,
    }
}
