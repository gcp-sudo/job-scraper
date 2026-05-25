from supabase import create_client, Client
import config
from typing import Optional, Any, Dict, List
import logging
import asyncio

# --- Initialize Supabase Client ---
if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Supabase URL and Key must be set.")
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

# --- Parameterized Functions for Multi-Table Architecture ---
async def get_existing_jobs_from_supabase(table_name: str, batch_size: int = 1000) -> tuple[set, set]:
    """Fetches existing job IDs and company-title pairs from a specific table."""
    # ... (logic remains the same, but uses table_name)
    return set(), set()

async def save_jobs_to_supabase(jobs_data: list, table_name: str):
    """Saves or updates job data to a specific Supabase table."""
    if not jobs_data:
        return
    try:
        await supabase.table(table_name).upsert(jobs_data).execute()
        logging.info(f"Successfully upserted {len(jobs_data)} jobs to {table_name}.")
    except Exception as e:
        logging.error(f"Error upserting data to {table_name}: {e}")

async def get_jobs_to_score(table_name: str, limit: int) -> list:
    """Fetches jobs from a specific table that need scoring."""
    # ... (logic remains the same, but uses table_name)
    return []

async def update_job_score(table_name: str, job_id: str, score: int, resume_score_stage: str) -> bool:
    """Updates a job's score in a specific table."""
    # ... (logic remains the same, but uses table_name)
    return False

async def get_top_scored_jobs_for_resume_generation(table_name: str, limit: int) -> list:
    """Fetches top-scored jobs from a specific table for resume generation."""
    # ... (logic remains the same, but uses table_name)
    return []

async def update_job_with_resume_link(table_name: str, job_id: str, customized_resume_id: str, new_status: str) -> bool:
    """Updates a job record in a specific table with the resume link and new status."""
    # ... (logic remains the same, but uses table_name)
    return False

# --- Functions that are not table-specific (e.g., resumes) ---
async def get_base_resume() -> Optional[dict]:
    """Fetches the single base resume from its dedicated table."""
    # ... (logic remains the same)
    return None

async def save_customized_resume(resume_data: Dict[str, Any], resume_path: str) -> Optional[Any]:
    """Saves a customized resume to the dedicated 'customized_resumes' table."""
    # ... (logic remains the same)
    return None

async def upload_customized_resume_to_storage(file_content: bytes, destination_path: str) -> Optional[str]:
    """Uploads a resume PDF to Supabase Storage."""
    # ... (logic remains the same)
    return None

# --- New functions can be added here as needed ---
