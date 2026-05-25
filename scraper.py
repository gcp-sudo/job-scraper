import httpx
import asyncio
import random
import time
from datetime import datetime, timezone
import logging
from bs4 import BeautifulSoup
from markdownify import markdownify as md

import config
import user_agents
from supabase_utils import save_jobs_to_supabase, get_existing_job_ids

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- HTML to Markdown Conversion ---
def convert_html_to_markdown(html: str) -> str:
    if not html or not html.strip():
        return ""
    return md(html, heading_style="ATX", bullets="-").strip()

# --- LinkedIn Scraping Logic ---
async def _fetch_linkedin_job_ids(client: httpx.AsyncClient, query: str, location: str, geo_id: int, date_filter: str, job_type: str, work_type: int, start: int) -> list:
    """Fetches a list of LinkedIn job IDs for a given search query."""
    list_url = f"https://www.linkedin.com/jobs-guest-query-api/jobs-search?"
    params = {
        'query': query,
        'location': location,
        'geoId': geo_id,
        'f_TPR': date_filter, # Time Posted Range (e.g., r86400 for last 24 hours)
        'f_JT': job_type, # Job Type (e.g., 'F' for full-time)
        'f_WT': work_type, # Work Type (e.g., 2 for remote)
        'start': start
    }
    headers = {'User-Agent': random.choice(user_agents.USER_AGENTS)}
    try:
        response = await client.get(list_url, params=params, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return [job.get('jobPostingId') for job in response.json().get('jobs', [])]
    except (httpx.RequestError, Exception) as e:
        logging.error(f"Error fetching LinkedIn job IDs for query '{query}': {e}")
        return []

async def _fetch_linkedin_job_details(client: httpx.AsyncClient, job_id: str) -> dict | None:
    """Fetches the detailed information for a single LinkedIn job ID."""
    detail_url = f"https://www.linkedin.com/jobs-guest-query-api/job-posting/{job_id}"
    headers = {'User-Agent': random.choice(user_agents.USER_AGENTS)}
    try:
        response = await client.get(detail_url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": job_id,
            "title": data.get('title'),
            "company": data.get('company', {}).get('name'),
            "location": data.get('formattedLocation'),
            "description_html": data.get('description', {}).get('text'),
            "description_text": convert_html_to_markdown(data.get('description', {}).get('text')),
            "url": f"https://www.linkedin.com/jobs/view/{job_id}",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "linkedin",
            "status": "new",
            "is_active": True
        }
    except (httpx.RequestError, Exception) as e:
        logging.error(f"Error fetching details for LinkedIn job ID {job_id}: {e}")
        return None

async def process_linkedin_query(source_config: dict, table_name: str) -> list:
    """Orchestrates the scraping for all queries in the linkedin source config."""
    logging.info("--- Starting LinkedIn Job Scraping ---")
    all_new_jobs = []
    max_jobs_to_scrape = source_config.get("results_to_scrape", 25)
    
    async with httpx.AsyncClient() as client:
        existing_job_ids = await get_existing_job_ids(table_name)
        
        for query in source_config.get("queries", []):
            logging.info(f"Processing LinkedIn Search Query: '{query}'")
            scraped_job_ids = []
            start = 0
            while len(scraped_job_ids) < max_jobs_to_scrape:
                job_ids = await _fetch_linkedin_job_ids(
                    client, query, 
                    source_config.get("location"), 
                    source_config.get("geo_id"),
                    source_config.get("job_posting_date"),
                    source_config.get("job_type"),
                    source_config.get("work_type"),
                    start
                )
                if not job_ids:
                    break # No more job IDs returned
                
                scraped_job_ids.extend(job_ids)
                start += 25 # LinkedIn API paginates by 25
                await asyncio.sleep(random.uniform(1, 3))

            new_job_ids = [jid for jid in scraped_job_ids if jid not in existing_job_ids][:max_jobs_to_scrape]
            logging.info(f"Found {len(new_job_ids)} new jobs for query '{query}'. Fetching details...")

            tasks = [_fetch_linkedin_job_details(client, job_id) for job_id in new_job_ids]
            job_details_list = await asyncio.gather(*tasks)
            
            new_jobs = [job for job in job_details_list if job is not None]
            if new_jobs:
                await save_jobs_to_supabase(new_jobs, table_name)
                all_new_jobs.extend(new_jobs)

    logging.info(f"LinkedIn scraping finished. Saved a total of {len(all_new_jobs)} new jobs.")
    return all_new_jobs

# --- Placeholder Scraping Functions for Other Sources ---
async def process_placeholder_query(source_name: str, source_config: dict, table_name: str) -> list:
    logging.info(f"--- Starting {source_name.capitalize()} Job Scraping (Placeholder) ---")
    logging.info(f"Scraping {source_name} jobs with config: {source_config} into table: {table_name}")
    await asyncio.sleep(1)
    return []

# --- Main Orchestration for Scraper ---
async def run(source: str, source_config: dict, table_name: str):
    """Runs the scraping process for a given source."""
    
    source_processor_map = {
        "linkedin": process_linkedin_query,
    }

    processor = source_processor_map.get(source)
    
    if processor:
        new_jobs = await processor(source_config, table_name)
    else:
        # For all other sources, use the placeholder function
        new_jobs = await process_placeholder_query(source, source_config, table_name)

    logging.info(f"Scraping for source '{source}' finished. Saved {len(new_jobs)} new jobs.")
