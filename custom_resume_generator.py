import logging
import io
import supabase_utils
import config
from pydantic import ValidationError
from typing import List, Dict, Any
import json
import pdf_generator
import re
import asyncio
from llm_client import primary_client
from models import Resume, SummaryOutput
import time
import os

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Keyword-based Skill Personalization ---
def personalize_skills_with_keyword_injection(base_skills: List[str], job_description: str) -> List[str]:
    # ... (function remains the same)
    return []

# --- LLM Personalization Function (Summary only) ---
async def personalize_summary_with_llm(summary_content: str, full_resume: Resume, job_details: Dict[str, Any]) -> str:
    # ... (function remains the same)
    return ""

# --- Job Processing Logic ---
async def process_job(job_details: Dict[str, Any], base_resume_details: Resume, table_name: str):
    """Processes a single job: personalizes resume, generates PDF, uploads, updates status in the correct table."""
    job_id = job_details.get("job_id")
    if not job_id:
        logging.error("Job details missing job_id.")
        return

    logging.info(f"--- Starting processing for job_id: {job_id} from table {table_name} ---")

    try:
        personalized_resume_data = base_resume_details.model_copy(deep=True)

        # 1. Personalize Summary & Skills
        # ... (summary and skills personalization logic remains the same)

        # 2. Generate PDF
        pdf_bytes = pdf_generator.create_resume_pdf(personalized_resume_data)
        if not pdf_bytes:
            raise ValueError("PDF generation returned empty bytes.")

        # 3. Upload PDF to Storage
        destination_path = f"resume_{job_id}.pdf"
        resume_path = await supabase_utils.upload_customized_resume_to_storage(pdf_bytes, destination_path)
        if not resume_path:
            raise ValueError("Failed to upload resume PDF.")

        # 4. Save Customized Resume data
        customized_resume_id = await supabase_utils.save_customized_resume(personalized_resume_data, resume_path)

        # 5. Update Job Record in the correct table
        update_success = await supabase_utils.update_job_with_resume_link(table_name, job_id, customized_resume_id, new_status="resume_generated")
        if not update_success:
            logging.error(f"Failed to update job record for job_id: {job_id} in table {table_name}")

        logging.info(f"--- Finished processing for job_id: {job_id} ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred while processing job_id {job_id}: {e}", exc_info=True)

# --- Main Orchestration for Resume Generation ---
async def run(table_name: str):
    """Fetches top jobs from a specific table and processes them."""
    logging.info(f"--- Starting Custom Resume Generation for table: {table_name} ---")

    # 1. Get Base Resume
    raw_resume_details = await supabase_utils.get_base_resume()
    if not raw_resume_details:
        logging.error(f"Base resume not found. Cannot generate resumes for {table_name}. Please run 'Parse Resume' workflow first.")
        return

    try:
        base_resume_details = Resume(**raw_resume_details)
    except Exception as e:
        logging.error(f"Error parsing base resume details: {e}")
        return

    # 2. Fetch Top Scored Jobs from the specified table
    jobs_to_process = await supabase_utils.get_top_scored_jobs_for_resume_generation(table_name, limit=config.JOBS_TO_CUSTOMIZE_PER_RUN)
    if not jobs_to_process:
        logging.info(f"No new jobs found to process in {table_name} for this cycle.")
        return

    logging.info(f"Found {len(jobs_to_process)} jobs to process in {table_name}.")

    # 3. Process Each Job
    for job_details in jobs_to_process:
        await process_job(job_details, base_resume_details, table_name)
        logging.info(f"Waiting for {config.LLM_REQUEST_DELAY_SECONDS} seconds before processing next job.")
        await asyncio.sleep(config.LLM_REQUEST_DELAY_SECONDS)

    logging.info(f"--- Finished Custom Resume Generation for table: {table_name} ---")
