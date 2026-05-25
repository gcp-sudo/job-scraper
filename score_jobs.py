import time
import json
import logging
from typing import List, Optional, Dict, Any
import os
from sentence_transformers import SentenceTransformer, util
import asyncio

import config
import supabase_utils

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Sentence Transformer Model (Lazy Loading) ---
model = None

def load_model():
    global model
    if model is None:
        logging.info("Loading sentence-transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logging.info("Sentence-transformer model loaded.")

# --- Helper Functions ---
def format_resume_to_text(resume_data: Dict[str, Any]) -> str:
    # ... (function remains the same)
    return ""

def get_embedding_score(resume_embedding, job_details: Dict[str, Any]) -> Optional[int]:
    # ... (function remains the same)
    job_description = job_details.get('description', '')
    job_id = job_details.get('job_id')

    if not job_description:
        return 0

    if config.TARGET_KEYWORDS:
        if not any(keyword.lower() in job_description.lower() for keyword in config.TARGET_KEYWORDS):
            return 0

    try:
        job_embedding = model.encode(job_description, convert_to_tensor=True)
        cosine_scores = util.cos_sim(resume_embedding, job_embedding)
        score = int(cosine_scores.item() * 100)
        return max(0, min(100, score))
    except Exception as e:
        logging.error(f"Error calculating embedding score for job {job_id}: {e}")
        return None

# --- Main Scoring Logic for Workflow ---
async def run(table_name: str):
    """Main function to score jobs from a specific table."""
    logging.info(f"--- Starting Job Scoring for table: {table_name} ---")
    load_model() # Ensure model is loaded

    # 1. Get Base Resume
    default_resume_data = await supabase_utils.get_base_resume()
    if not default_resume_data:
        logging.error(f"Base resume not found. Cannot score jobs for {table_name}. Please run 'Parse Resume' workflow first.")
        return

    # 2. Generate Resume Embedding
    default_resume_text = format_resume_to_text(default_resume_data)
    logging.info("Generating embedding for the base resume...")
    default_resume_embedding = model.encode(default_resume_text, convert_to_tensor=True)
    logging.info("Base resume embedding generated.")

    # 3. Fetch jobs that need scoring from the specified table
    jobs_to_score = await supabase_utils.get_jobs_to_score(table_name, config.JOBS_TO_SCORE_PER_RUN)
    if not jobs_to_score:
        logging.info(f"No jobs require initial scoring in {table_name} at this time.")
        return

    logging.info(f"Processing {len(jobs_to_score)} jobs from {table_name} for initial scoring...")
    successful_scores = 0
    failed_scores = 0

    # 4. Score each job and update the database
    for job in jobs_to_score:
        job_id = job.get('job_id')
        if not job_id:
            logging.warning("Found job data without job_id. Skipping.")
            failed_scores +=1
            continue

        score = get_embedding_score(default_resume_embedding, job)

        if score is not None:
            if await supabase_utils.update_job_score(table_name, job_id, score, resume_score_stage="initial"):
                successful_scores += 1
            else:
                failed_scores += 1
        else:
            failed_scores += 1

    logging.info(f"--- Job Scoring for {table_name} Finished ---")
    logging.info(f"Successfully scored: {successful_scores}")
    logging.info(f"Failed/Skipped scores: {failed_scores}")
