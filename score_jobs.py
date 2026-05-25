import time
import json
import logging
from typing import List, Optional, Dict, Any
import requests
import io
import pdfplumber
import os
from sentence_transformers import SentenceTransformer, util

import config
import supabase_utils

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Sentence Transformer Model ---
logging.info("Loading sentence-transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
logging.info("Sentence-transformer model loaded.")

# --- Helper Functions ---

def format_resume_to_text(resume_data: Dict[str, Any]) -> str:
    """
    Formats the structured resume data dictionary into a plain text string.
    """
    if not resume_data:
        return "Resume data is not available."

    lines = []

    # Basic Info
    lines.append(f"Name: {resume_data.get('name', 'N/A')}")
    lines.append(f"Email: {resume_data.get('email', 'N/A')}")
    if resume_data.get('phone'): lines.append(f"Phone: {resume_data['phone']}")
    if resume_data.get('location'): lines.append(f"Location: {resume_data['location']}")
    if resume_data.get('links'):
        links_str = ", ".join(f"{k}: {v}" for k, v in resume_data['links'].items() if v)
        if links_str: lines.append(f"Links: {links_str}")
    lines.append("\n---\n")

    # Summary
    if resume_data.get('summary'):
        lines.append("Summary:")
        lines.append(resume_data['summary'])
        lines.append("\n---\n")

    # Skills
    if resume_data.get('skills'):
        lines.append("Skills:")
        lines.append(", ".join(resume_data['skills']))
        lines.append("\n---\n")

    # Experience
    if resume_data.get('experience'):
        lines.append("Experience:")
        for exp in resume_data['experience']:
            lines.append(f"\n* {exp.get('job_title', 'N/A')} at {exp.get('company', 'N/A')}")
            if exp.get('location'): lines.append(f"  Location: {exp['location']}")
            date_range = f"{exp.get('start_date', '?')} - {exp.get('end_date', 'Present')}"
            lines.append(f"  Dates: {date_range}")
            if exp.get('description'):
                lines.append("  Description:")
                # Indent description lines
                desc_lines = exp['description'].split('\n')
                lines.extend([f"    - {line.strip()}" for line in desc_lines if line.strip()])
        lines.append("\n---\n")

    # Education
    if resume_data.get('education'):
        lines.append("Education:")
        for edu in resume_data['education']:
            degree_info = f"{edu.get('degree', 'N/A')}"
            if edu.get('field_of_study'): degree_info += f", {edu['field_of_study']}"
            lines.append(f"\n* {degree_info} from {edu.get('institution', 'N/A')}")
            year_range = f"{edu.get('start_year', '?')} - {edu.get('end_year', 'Present')}"
            lines.append(f"  Years: {year_range}")
        lines.append("\n---\n")

    # Projects
    if resume_data.get('projects'):
        lines.append("Projects:")
        for proj in resume_data['projects']:
            lines.append(f"\n* {proj.get('name', 'N/A')}")
            if proj.get('description'): lines.append(f"  Description: {proj['description']}")
            if proj.get('technologies'): lines.append(f"  Technologies: {', '.join(proj['technologies'])}")
        lines.append("\n---\n")

    # Certifications
    if resume_data.get('certifications'):
        lines.append("Certifications:")
        for cert in resume_data['certifications']:
            cert_info = f"{cert.get('name', 'N/A')}"
            if cert.get('issuer'): cert_info += f" ({cert['issuer']})"
            if cert.get('year'): cert_info += f" - {cert['year']}"
            lines.append(f"* {cert_info}")
        lines.append("\n---\n")

    # Languages
    if resume_data.get('languages'):
        lines.append("Languages:")
        lines.append(", ".join(resume_data['languages']))
        lines.append("\n---\n")

    return "\n".join(lines)

def get_embedding_score(resume_embedding, job_details: Dict[str, Any]) -> Optional[int]:
    """
    Calculates the similarity score between a resume embedding and a job description.
    """
    job_description = job_details.get('description', '')
    job_id = job_details.get('job_id')

    if not job_description:
        logging.warning(f"Job {job_id} has no description. Skipping scoring.")
        return 0

    # --- Keyword Pre-filter ---
    if config.TARGET_KEYWORDS:
        if not any(keyword.lower() in job_description.lower() for keyword in config.TARGET_KEYWORDS):
            logging.info(f"Job {job_id} does not contain any target keywords. Assigning score of 0.")
            return 0

    try:
        job_embedding = model.encode(job_description, convert_to_tensor=True)
        cosine_scores = util.cos_sim(resume_embedding, job_embedding)
        score = int(cosine_scores.item() * 100)
        score = max(0, min(100, score))
        logging.info(f"Job {job_id} received embedding score: {score}")
        return score
    except Exception as e:
        logging.error(f"Error calculating embedding score for job {job_id}: {e}")
        return None

def extract_text_from_pdf_url(pdf_url: str) -> Optional[str]:
    """
    Downloads a PDF from a URL and extracts text from it.
    """
    if not pdf_url:
        logging.warning("No PDF URL provided for text extraction.")
        return None
    try:
        logging.info(f"Downloading PDF from URL: {pdf_url}")
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()

        logging.info(f"Successfully downloaded PDF. Extracting text...")
        text = ""
        with io.BytesIO(response.content) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        if not text.strip():
            logging.warning(f"Extracted no text from PDF at {pdf_url}. The PDF might be image-based or empty.")
            return None
            
        logging.info(f"Successfully extracted text from PDF URL: {pdf_url[:70]}...")
        return text.strip()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading PDF from {pdf_url}: {e}")
        return None
    except pdfplumber.exceptions.PDFSyntaxError:
        logging.error(f"Error: Could not open PDF from {pdf_url}. It might be corrupted or not a PDF.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while extracting text from PDF URL {pdf_url}: {e}")
        return None

def main():
    """Main function to score jobs based on the target resume."""
    logging.info("--- Starting Job Scoring Script ---")
    overall_start_time = time.time()

    # --- Phase 1: Initial Scoring with Default Resume ---
    logging.info("--- Phase 1: Initial Scoring with Default Resume ---")
    initial_score_start_time = time.time()
    
    resume_path = getattr(config, 'BASE_RESUME_PATH', 'resume.json')
    default_resume_data = supabase_utils.get_base_resume()
    
    if not default_resume_data and os.path.exists(resume_path):
        logging.info(f"Supabase fetch failed. Falling back to local file: {resume_path}")
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                default_resume_data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to read or decode {resume_path}: {e}")
            default_resume_data = None
    
    if not default_resume_data:
        logging.error(f"Base resume not found. Please run the 'Parse Resume' workflow first.")
        return

    default_resume_text = format_resume_to_text(default_resume_data)
    logging.info("Generating embedding for the base resume...")
    default_resume_embedding = model.encode(default_resume_text, convert_to_tensor=True)
    logging.info("Base resume embedding generated.")

    jobs_to_score = supabase_utils.get_jobs_to_score(config.JOBS_TO_SCORE_PER_RUN)
    if not jobs_to_score:
        logging.info("No jobs require initial scoring at this time.")
    else:
        logging.info(f"Processing {len(jobs_to_score)} jobs for initial scoring...")
        successful_scores = 0
        failed_scores = 0

        for i, job in enumerate(jobs_to_score):
            job_id = job.get('job_id')
            if not job_id:
                logging.warning("Found job data without job_id. Skipping.")
                failed_scores +=1
                continue

            logging.info(f"--- Scoring Job {i+1}/{len(jobs_to_score)} (ID: {job_id}) ---")
            score = get_embedding_score(default_resume_embedding, job)

            if score is not None:
                if supabase_utils.update_job_score(job_id, score, resume_score_stage="initial"):
                    successful_scores += 1
                else:
                    failed_scores += 1
            else:
                failed_scores += 1
        
        initial_score_end_time = time.time()
        logging.info("--- Initial Scoring Phase Finished ---")
        logging.info(f"Successfully scored: {successful_scores}")
        logging.info(f"Failed/Skipped scores: {failed_scores}")
        logging.info(f"Total initial scoring time: {initial_score_end_time - initial_score_start_time:.2f} seconds")

    overall_end_time = time.time()
    logging.info("--- Job Scoring Script Finished ---")
    logging.info(f"Total script execution time: {overall_end_time - overall_start_time:.2f} seconds")

if __name__ == "__main__":
    main()