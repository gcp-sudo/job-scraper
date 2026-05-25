import asyncio
import httpx
import random
import time
from datetime import datetime, timedelta, timezone
import logging

import config
import user_agents
from supabase_utils import supabase

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---
def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

def get_past_date(days: int) -> datetime:
    return get_utc_now() - timedelta(days=days)

async def _check_single_linkedin_job_active(job_id: str, client: httpx.AsyncClient) -> bool | None:
    # This function remains the same as it is LinkedIn specific
    return None # Placeholder

# --- Maintenance Tasks (Parameterized) ---
async def mark_expired_jobs(table_name: str):
    """Marks old jobs in a given table as expired."""
    logging.info(f"--- Starting Task: Mark Expired Jobs for {table_name} ---")
    expiry_date_str = get_past_date(config.JOB_EXPIRY_DAYS).isoformat()
    excluded_statuses = ['applied', 'offer', 'interview', 'archived']

    try:
        # REMOVED await - .execute() is not awaitable in this library version
        response = supabase.table(table_name)\
            .update({"status": "expired", "is_active": False})\
            .lt("scraped_at", expiry_date_str)\
            .not_.in_("status", excluded_statuses)\
            .eq("is_active", True)\
            .execute()
        
        logging.info(f"Marked expired jobs in {table_name}.")

    except Exception as e:
        logging.error(f"Error marking expired jobs in {table_name}: {e}")

async def check_linkedin_job_activity(table_name: str):
    """Checks if active LinkedIn jobs are still available."""
    logging.info(f"--- Starting Task: Check LinkedIn Job Activity for {table_name} ---")
    # This task is specific to LinkedIn and will only be called for the LinkedIn table.
    pass # Placeholder for the full implementation

async def archive_old_jobs(table_name: str):
    """Archives very old, inactive jobs instead of deleting them."""
    logging.info(f"--- Starting Task: Archive Old Jobs for {table_name} ---")
    archive_older_than_date_str = get_past_date(config.JOB_DELETION_DAYS).isoformat()
    inactive_statuses = ['expired', 'removed']

    try:
        # REMOVED await - .execute() is not awaitable
        response = supabase.table(table_name)\
            .update({"status": "archived"})\
            .in_("status", inactive_statuses)\
            .lt("scraped_at", archive_older_than_date_str)\
            .execute()

        logging.info(f"Archived old jobs in {table_name}.")

    except Exception as e:
        logging.error(f"Error archiving old jobs in {table_name}: {e}")

# --- Main Orchestration for Job Manager ---
async def run(table_name: str):
    """Runs the job management tasks for a specific table."""
    logging.info(f"--- Starting Job Management for table: {table_name} ---")
    
    await mark_expired_jobs(table_name)
    
    # FIXED config.SUPABASE_TABLE_MAP to config.TABLE_MAP
    if table_name == config.TABLE_MAP.get("linkedin"):
        await check_linkedin_job_activity(table_name)
    else:
        logging.info(f"Skipping activity check for non-LinkedIn source: {table_name}")
        
    await archive_old_jobs(table_name)
    
    logging.info(f"--- Finished Job Management for table: {table_name} ---")
