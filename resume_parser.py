import asyncio
import logging
import json
from typing import List
import io

# Third-party libraries
import PyPDF2
from pydantic import BaseModel, Field

# Internal modules
from llm_client import primary_client
import supabase_utils
import config

# --- Pydantic Model for Parsed Resume ---
class ParsedResume(BaseModel):
    """Structure for the parsed resume data."""
    full_text: str = Field(description="The full, unmodified text content of the resume.")
    skills: List[str] = Field(description="A list of key skills, technologies, and methodologies extracted from the resume.")
    experience_summary: str = Field(description="A concise summary of the candidate's professional experience, highlighting key roles and achievements.")

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def parse_resume_text(resume_text: str) -> ParsedResume:
    """Uses the LLM to parse the resume text and extract structured data."""
    system_prompt = "You are an expert resume parser. Your task is to extract information from the provided resume text and format it into a JSON object according to the specified schema. Please be precise and thorough."
    
    prompt = f"""
    Here is the resume text to parse:
    ---
    {resume_text}
    ---
    Please extract the full text, a list of skills, and a summary of the professional experience.
    """
    
    # Use the corrected generate_content method. It now correctly handles the Pydantic model.
    response_json_str = await asyncio.to_thread(
        primary_client.generate_content,
        prompt=prompt,
        system_prompt=system_prompt,
        response_format=ParsedResume
    )
    
    # Parse the JSON string into the Pydantic model
    parsed_data = json.loads(response_json_str)
    return ParsedResume(**parsed_data)

async def main():
    """Main function to download, parse, and save the resume."""
    logging.info("Starting resume processing...")

    try:
        # 1. Download the resume PDF from Supabase Storage
        resume_bytes = await supabase_utils.download_resume_from_storage("resume.pdf")

        if not resume_bytes:
            logging.error("Failed to download or find resume. Please upload 'resume.pdf' to the 'resumes' bucket in Supabase.")
            return

        # 2. Extract text from the PDF
        logging.info("Extracting text from PDF...")
        pdf_file = io.BytesIO(resume_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        resume_text = "".join(page.extract_text() or "" for page in reader.pages)
        
        if not resume_text.strip():
            logging.error("Extracted text from PDF is empty. The PDF might be an image or scanned document.")
            return

        # 3. Parse the extracted text using the LLM
        logging.info("Parsing resume text with LLM...")
        parsed_resume = await parse_resume_text(resume_text)

        # Overwrite the LLM's full_text with the ground truth from the PDF
        parsed_resume.full_text = resume_text

        # 4. Save the parsed resume to the 'base_resume' table
        logging.info("Saving parsed resume to the database...")
        success = await supabase_utils.save_base_resume(parsed_resume.model_dump())

        if success:
            logging.info("Resume processing finished successfully.")
        else:
            logging.error("Failed to save the parsed resume to the database.")

    except ImportError:
        logging.error("PyPDF2 is not installed. Please add it to your requirements.txt and install.")
    except Exception as e:
        logging.error(f"An error occurred during resume processing: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
