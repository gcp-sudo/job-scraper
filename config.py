import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Provider Selection ---
# Determine the primary LLM provider. Default to 'gemini' if not set.
# This allows for easy switching between providers like 'gemini', 'openai', or 'groq'.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()

# --- API Keys ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Supabase Configuration ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# --- Database Table and Storage Mapping ---
# Maps job sources to their corresponding table names in Supabase
SUPABASE_TABLE_MAP = {
    "linkedin": "jobs_linkedin",
    "gulf": "jobs_gulf",
    "startup": "jobs_startup",
    "freelance": "jobs_freelance",
    "fresher": "jobs_fresher",
}

# Names for other tables and storage buckets
SUPABASE_CUSTOMIZED_RESUMES_TABLE_NAME = "customized_resumes"
SUPABASE_BASE_RESUME_TABLE_NAME = "base_resume"
SUPABASE_STORAGE_BUCKET = "personalized_resumes"
SUPABASE_RESUME_STORAGE_BUCKET = "resumes"

# --- Search & Scraping Configuration ---
# Enable or disable scraping for each source
SCRAPING_SOURCES = ["linkedin", "gulf", "startup", "freelance", "fresher"]

# Search parameters for each job source
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
    },
    "startup": {
        "search_queries": ["Founding Engineer", "Early-stage startup"],
        "location": "Global",
    },
    "freelance": {
        "search_queries": ["Freelance DevOps", "Cloud Consultant"],
        "location": "Remote",
    },
    "fresher": {
        "search_queries": ["Junior DevOps", "Graduate Cloud Engineer"],
        "location": "India",
    },
}

# Maximum number of jobs to scrape per search query for each source
MAX_JOBS_PER_SEARCH = {
    "linkedin": 25,
    "gulf": 15,
    "startup": 10,
    "freelance": 20,
    "fresher": 10,
}

# --- Job Processing Limits ---
JOBS_TO_SCORE_PER_RUN = 20
JOBS_TO_CUSTOMIZE_PER_RUN = 5

# --- Job Maintenance Settings ---
JOB_EXPIRY_DAYS = 30
JOB_CHECK_DAYS = 3
JOB_DELETION_DAYS = 60
JOB_CHECK_LIMIT = 50

# --- LLM & Request Settings ---
LLM_MODEL = "gemini/gemini-1.5-flash-latest"
LLM_FALLBACK_MODELS = ["gpt-4o-mini", "groq/llama3-70b-8192"]
LLM_MAX_RPM = 10
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 10
LLM_REQUEST_DELAY_SECONDS = 8

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 15

ACTIVE_CHECK_TIMEOUT = 20
ACTIVE_CHECK_MAX_RETRIES = 2
ACTIVE_CHECK_RETRY_DELAY = 10

# --- Function to Get Primary LLM Client ---
# This function centralizes the instantiation of the LLM client,
# preventing circular dependencies and making it easy to switch providers.
def get_primary_llm_client():
    """Initializes and returns the primary LLM client based on the provider specified in the config."""
    # Local import to prevent circular dependency issues
    from llm_client import GeminiClient, OpenAIClient, GroqClient

    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        return GeminiClient(api_key=GEMINI_API_KEY)
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        return OpenAIClient(api_key=OPENAI_API_KEY)
    elif LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set.")
        return GroqClient(api_key=GROQ_API_KEY)
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
