import logging
import io
import supabase_utils
import config
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any
import json
import pdf_generator
import re
import asyncio
from llm_client import primary_client
from models import (
    Resume,
    SummaryOutput
)
import time
import os

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Keyword-based Skill Personalization ---
def personalize_skills_with_keyword_injection(
    base_skills: List[str],
    job_description: str
) -> List[str]:
    """
    Personalizes the skills list by injecting relevant keywords from the job description.
    """
    logging.info("Personalizing skills with keyword injection.")
    if not job_description:
        return base_skills

    potential_skills_from_job = set()
    job_desc_lower = job_description.lower()

    for keyword in config.TARGET_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', job_desc_lower):
            potential_skills_from_job.add(keyword)

    logging.info(f"Found {len(potential_skills_from_job)} potential skills in job description: {potential_skills_from_job}")

    combined_skills = set(base_skills) | potential_skills_from_job

    final_skills = list(base_skills)
    for skill in potential_skills_from_job:
        if len(final_skills) >= 15:
            break
        if skill not in final_skills:
            final_skills.append(skill)
    
    logging.info(f"Final personalized skills list: {final_skills}")
    return final_skills


# --- LLM Personalization Function (Now only for Summary) ---
async def personalize_summary_with_llm(
    summary_content: str,
    full_resume: Resume,
    job_details: Dict[str, Any]
) -> str:
    """
    Uses an LLM to personalize the summary of the resume for the given job.
    """
    if not summary_content or summary_content == "NA":
        logging.warning("Skipping summary personalization for empty or 'NA' content.")
        return summary_content

    OutputModel = SummaryOutput
    output_key = "summary"

    resume_context_dict = full_resume.model_dump(exclude={"summary"})
    resume_context = json.dumps(resume_context_dict, indent=2)

    prompt = f"""
    **Task:** Enhance the resume summary for the target job application.

    **Target Job**
    - Title: {job_details['job_title']}
    - Company: {job_details['company']}
    - Seniority Level: {job_details['level']}
    - Job Description: {job_details['description']}

    ---

    **Full Resume Context (excluding the summary):**
    {resume_context}

    ---

    **Original Summary:**
    {summary_content}

    ---
    **Instructions:**
    - Rewrite **only** the summary to be concise, impactful, and highly relevant to the Target Job.
    - **CRITICAL: The core professional identity and experience level from the original summary MUST be preserved.** Do NOT change the candidate's stated primary role.
    - Highlight 2-3 key qualifications or experiences from the "Full Resume Context" that ALIGN with the "Job Description."
    - Use strong action verbs and keywords from the "Job Description" where appropriate, but ONLY when describing actual experiences or skills present in the resume.
    - **ABSOLUTELY DO NOT INVENT new information.**
    ---
    **Expected JSON Output Structure:** {{"summary": "A dynamic and results-oriented Software Engineer with X years of experience..."}}
    """

    system_prompt = f"""
    You are an expert resume writer and a precise JSON generation assistant.
    Your primary function is to enhance the resume summary.
    **CRITICAL OUTPUT REQUIREMENTS:**
    1.  You MUST ALWAYS output a single, valid JSON object.
    2.  Your entire response MUST be *only* the JSON object.
    3.  Do NOT include any introductory text, explanations, markdown formatting, or any text outside of the JSON structure itself.
    **CORE WRITING PRINCIPLES:**
    1.  **No Fabrication:** NEVER invent new information. Rephrasing and emphasizing existing facts is allowed; fabrication is strictly forbidden.
    2.  **Relevance:** Focus on aligning the candidate's existing experience and skills with the target job.
    3.  **Fact-Based:** All enhancements must be grounded in the provided resume context.
    """

    try:
        logging.info(f"Sending prompt to LLM for summary personalization.")
        llm_output = await primary_client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            response_format=OutputModel,
        )
        
        logging.info("Received response from LLM for summary.")

        parsed_response_model = OutputModel.model_validate_json(llm_output)
        return getattr(parsed_response_model, output_key)

    except (ValidationError, json.JSONDecodeError) as e:
        logging.error(f"Failed to validate or parse LLM JSON output for summary: {e}")
        logging.error(f"LLM Raw Output was: {llm_output}")
        return summary_content # Fallback
    except Exception as e:
        logging.error(f"Error calling LLM or processing response for summary: {e}")
        return summary_content # Fallback

# --- Main Processing Logic ---
async def process_job(job_details: Dict[str, Any], base_resume_details: Resume):
    """
    Processes a single job: personalizes resume, generates PDF, uploads, updates status.
    """
    job_id = job_details.get("job_id")
    if not job_id:
        logging.error("Job details missing job_id.")
        return

    logging.info(f"--- Starting processing for job_id: {job_id} ---")

    try:
        personalized_resume_data = base_resume_details.model_copy(deep=True)

        # --- 1. Personalize Summary (LLM Call) ---
        if personalized_resume_data.summary and personalized_resume_data.summary != "NA":
            logging.info(f"Personalizing summary for job_id: {job_id}")
            personalized_summary = await personalize_summary_with_llm(
                personalized_resume_data.summary,
                base_resume_details,
                job_details
            )
            personalized_resume_data.summary = personalized_summary
            logging.info(f"Finished summary personalization for job_id: {job_id}")
        else:
            logging.info(f"Skipping empty summary for job_id: {job_id}")

        # --- 2. Personalize Skills (Keyword Injection) ---
        if personalized_resume_data.skills:
            logging.info(f"Personalizing skills for job_id: {job_id}")
            personalized_skills = personalize_skills_with_keyword_injection(
                personalized_resume_data.skills,
                job_details.get('description', '')
            )
            personalized_resume_data.skills = personalized_skills
            logging.info(f"Finished skills personalization for job_id: {job_id}")
        else:
            logging.info(f"Skipping empty skills section for job_id: {job_id}")

        logging.info("Skipping LLM personalization for 'experience' and 'projects' sections as per new strategy.")

        # 3. Generate PDF
        logging.info(f"Generating PDF for job_id: {job_id}")
        try:
            pdf_bytes = pdf_generator.create_resume_pdf(personalized_resume_data)
            if not pdf_bytes:
                 raise ValueError("PDF generation returned empty bytes.")
            logging.info(f"PDF generation complete for job_id: {job_id}")
        except Exception as e:
            logging.error(f"Failed to generate PDF for job_id {job_id}: {e}")
            return

        # 4. Upload PDF to Supabase Storage
        destination_path = f"resume_{job_id}.pdf"
        logging.info(f"Uploading PDF to {destination_path} for job_id: {job_id}")
        resume_path = supabase_utils.upload_customized_resume_to_storage(pdf_bytes, destination_path)

        if not resume_path:
            logging.error(f"Failed to upload resume PDF for job_id: {job_id}")
            return

        logging.info(f"Successfully uploaded PDF for job_id: {job_id}. Path: {resume_path}")

        # 5. Add Customized Resume to Supabase
        logging.info("Adding customized resume to Supabase")
        customized_resume_id = supabase_utils.save_customized_resume(personalized_resume_data, resume_path)

        # 6. Update Job Record in Supabase
        logging.info(f"Updating job record for job_id: {job_id} with resume path.")
        update_success = supabase_utils.update_job_with_resume_link(job_id, customized_resume_id, new_status="resume_generated")

        if update_success:
            logging.info(f"Successfully updated job record for job_id: {job_id}")
        else:
            logging.error(f"Failed to update job record for job_id: {job_id}")

        logging.info(f"--- Finished processing for job_id: {job_id} ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred while processing job_id {job_id}: {e}", exc_info=True)


async def run_job_processing_cycle():
    """
    Fetches top jobs and processes them one by one.
    """
    logging.info("Starting new job processing cycle...")

    resume_path = getattr(config, 'BASE_RESUME_PATH', 'resume.json')
    raw_resume_details = supabase_utils.get_base_resume()
    
    if not raw_resume_details and os.path.exists(resume_path):
        logging.info(f"Supabase fetch failed. Falling back to local file: {resume_path}")
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                raw_resume_details = json.load(f)
        except Exception as e:
            logging.error(f"Failed to read or decode {resume_path}: {e}")
            return

    if not raw_resume_details:
        logging.error(f"Base resume not found. Please run the 'Parse Resume' workflow first.")
        return

    try:
        for key in ['skills', 'experience', 'education', 'projects', 'certifications', 'languages']:
             if raw_resume_details.get(key) is None:
                 raw_resume_details[key] = []
        base_resume_details = Resume(**raw_resume_details)
        logging.info("Successfully parsed base resume.")
    except Exception as e:
        logging.error(f"Error parsing base resume details into Pydantic model: {e}")
        return

    jobs_limit = config.JOBS_TO_CUSTOMIZE_PER_RUN
    logging.info(f"Fetching top {jobs_limit} scored jobs to apply for...")
    jobs_to_process = supabase_utils.get_top_scored_jobs_for_resume_generation(limit=jobs_limit)

    if not jobs_to_process:
        logging.info("No new jobs found to process in this cycle.")
        return

    logging.info(f"Found {len(jobs_to_process)} jobs to process.")

    for job_details in jobs_to_process:
        await process_job(job_details, base_resume_details)
        logging.info(f"Waiting for {config.LLM_REQUEST_DELAY_SECONDS} seconds before processing next job.")
        await asyncio.sleep(config.LLM_REQUEST_DELAY_SECONDS)


if __name__ == "__main__":
    logging.info("Script started.")
    try:
        asyncio.run(run_job_processing_cycle())
        logging.info("Resume processing completed successfully.")
    except Exception as e:
        logging.error(f"Error during task execution: {e}", exc_info=True)