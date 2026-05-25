
import asyncio
import logging
from typing import Any, Dict, List, Optional

import config
from supabase import Client, create_client

# --- Initialize Supabase Client ---
if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Supabase URL and Key must be set in config.py or environment variables.")
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

# --- Resume Handling ---

async def download_resume_from_storage(file_path: str) -> Optional[bytes]:
    """Downloads a file from the 'resumes' Supabase Storage bucket."""
    try:
        bucket_name = config.RESUMES_BUCKET
        response = await supabase.storage.from_(bucket_name).download(file_path)
        logging.info(f"Successfully downloaded {file_path} from storage bucket {bucket_name}.")
        return response
    except Exception as e:
        if "The resource was not found" in str(e):
            logging.error(f"Resume file '{file_path}' not found in storage bucket '{bucket_name}'. Please upload your resume.")
        else:
            logging.error(f"Error downloading {file_path} from storage: {e}")
        return None

async def save_base_resume(resume_data: Dict[str, Any]) -> bool:
    """Saves the parsed base resume data, ensuring only one record exists."""
    try:
        # Delete all existing records to ensure only one base resume exists.
        await supabase.table(config.BASE_RESUME_TABLE).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute() # Delete all
        
        # Insert the new base resume.
        response = await supabase.table(config.BASE_RESUME_TABLE).insert(resume_data).execute()
        
        if response.data:
            logging.info("Successfully saved base resume to the database.")
            return True
        return False
    except Exception as e:
        logging.error(f"Error saving base resume to the database: {e}")
        return False

async def get_base_resume() -> Optional[Dict[str, Any]]:
    """Fetches the single base resume from its dedicated table."""
    try:
        response = await supabase.table(config.BASE_RESUME_TABLE).select('*').limit(1).single().execute()
        return response.data if response.data else None
    except Exception as e:
        logging.error(f"Error fetching base resume: {e}")
        return None

async def save_customized_resume(resume_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Saves a customized resume to the dedicated 'customized_resumes' table."""
    try:
        response = await supabase.table(config.CUSTOMIZED_RESUMES_TABLE).insert(resume_data).execute()
        if response.data:
            logging.info(f"Saved customized resume for job ID {resume_data.get('job_id')}")
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error saving customized resume: {e}")
        return None

async def upload_customized_resume_to_storage(file_content: bytes, destination_path: str) -> Optional[str]:
    """Uploads a resume PDF to Supabase Storage and returns its public URL."""
    try:
        bucket_name = config.PERSONALIZED_RESUMES_BUCKET
        await supabase.storage.from_(bucket_name).upload(
            path=destination_path, 
            file=file_content, 
            file_options={'content-type': 'application/pdf', 'upsert': 'true'}
        )
        response = supabase.storage.from_(bucket_name).get_public_url(destination_path)
        public_url = response
        logging.info(f"Uploaded resume to {public_url}")
        return public_url
    except Exception as e:
        logging.error(f"Error uploading file to Supabase Storage: {e}")
        if 'Duplicate' in str(e):
            logging.warning(f"File at {destination_path} already exists. Retrieving public URL.")
            try:
                return supabase.storage.from_(config.PERSONALIZED_RESUMES_BUCKET).get_public_url(destination_path)
            except Exception as url_e:
                logging.error(f"Could not retrieve URL for existing file: {url_e}")
        return None

# --- Job Data Handling ---

async def get_existing_job_ids(table_name: str, batch_size: int = 1000) -> set:
    """Fetches all existing job IDs from a specific table for quick lookups."""
    job_ids = set()
    start_index = 0
    while True:
        try:
            response = await supabase.table(table_name).select('id').range(start_index, start_index + batch_size - 1).execute()
            if not response.data:
                break
            for item in response.data:
                job_ids.add(item['id'])
            if len(response.data) < batch_size:
                break
            start_index += batch_size
        except Exception as e:
            logging.error(f"Error fetching existing job IDs from {table_name}: {e}")
            break
    logging.info(f"Found {len(job_ids)} existing job IDs in {table_name}.")
    return job_ids

async def save_jobs_to_supabase(jobs_data: List[Dict[str, Any]], table_name: str):
    """Saves or updates job data to a specific Supabase table."""
    if not jobs_data:
        return
    try:
        await supabase.table(table_name).upsert(jobs_data).execute()
        logging.info(f"Successfully upserted {len(jobs_data)} jobs to {table_name}.")
    except Exception as e:
        logging.error(f"Error upserting data to {table_name}: {e}")

async def get_jobs_to_score(table_name: str, limit: int) -> List[Dict[str, Any]]:
    """Fetches jobs from a specific table that need scoring (status 'new')."""
    try:
        response = await supabase.table(table_name).select('*').eq('status', 'new').limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error fetching jobs to score from {table_name}: {e}")
        return []

async def update_job_score(table_name: str, job_id: str, score: int, resume_score_stage: str) -> bool:
    """Updates a job's score and status in a specific table."""
    try:
        await supabase.table(table_name).update({'score': score, 'status': 'scored', 'resume_score_stage': resume_score_stage}).eq('id', job_id).execute()
        logging.info(f"Updated score for job {job_id} in {table_name}.")
        return True
    except Exception as e:
        logging.error(f"Error updating score for job {job_id} in {table_name}: {e}")
        return False

async def get_top_scored_jobs_for_resume_generation(table_name: str, limit: int) -> List[Dict[str, Any]]:
    """Fetches top-scored jobs from a specific table for resume generation."""
    try:
        min_score = config.MINIMUM_SCORE_FOR_AUTOGENERATE
        response = await supabase.table(table_name).select('*').eq('status', 'scored').gt('score', min_score).order('score', desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error fetching top jobs from {table_name}: {e}")
        return []

async def update_job_with_resume_link(table_name: str, job_id: str, customized_resume_id: str, new_status: str) -> bool:
    """Updates a job record in a specific table with the resume link and new status."""
    try:
        await supabase.table(table_name).update({'customized_resume_id': customized_resume_id, 'status': new_status}).eq('id', job_id).execute()
        logging.info(f"Updated job {job_id} in {table_name} with resume ID and status '{new_status}'.")
        return True
    except Exception as e:
        logging.error(f"Error updating job {job_id} in {table_name} with resume link: {e}")
        return False
