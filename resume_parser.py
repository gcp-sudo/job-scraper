
import asyncio
import json
import logging
import os
import sys
import pdfplumber

import config
import models
import supabase_utils
from llm_client import primary_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF file."""
    logging.info(f"Extracting text from: {pdf_path}")
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if page.hyperlinks:
                    for link in page.hyperlinks:
                        uri = link.get("uri")
                        if uri:
                            text += f" Embedded Link: {uri}\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def parse_resume_with_ai(resume_text):
    """Sends resume text to an AI model for structured parsing."""
    logging.info("Processing resume with AI model...")
    prompt = f'''Extract and return the structured resume information from the text below.
    Only use what is explicitly stated in the text and do not infer or invent any details.
    CRITICAL: If any information is missing or not available, use "NA" for that field.

    Resume text:
    {resume_text}
    '''
    try:
        response_text = primary_client.generate_content(
            prompt=prompt,
            response_format=models.Resume,
        )
        return response_text
    except Exception as e:
        logging.error(f"AI processing failed: {e}")
        return None

async def main():
    """Main async function to orchestrate the resume parsing process."""
    pdf_file_path = "./resume.pdf"

    # 1. Download resume from Supabase Storage
    pdf_bytes = await supabase_utils.download_resume_from_storage(os.path.basename(pdf_file_path))

    if not pdf_bytes:
        logging.error("Failed to download or find resume. Please upload 'resume.pdf' to the 'resumes' bucket in Supabase.")
        sys.exit(1)

    logging.info("Successfully downloaded resume.pdf.")
    with open(pdf_file_path, 'wb') as f:
        f.write(pdf_bytes)

    # 2. Extract text from PDF
    resume_text = extract_text_from_pdf(pdf_file_path)
    if not resume_text:
        logging.error("Failed to extract text. Exiting.")
        sys.exit(1)

    # 3. Parse resume with AI
    parsed_resume_str = parse_resume_with_ai(resume_text)
    if not parsed_resume_str:
        logging.error("Failed to parse resume. Exiting.")
        sys.exit(1)

    # 4. Process and save data
    try:
        resume_data = json.loads(parsed_resume_str)
        
        # Save to Supabase
        success = await supabase_utils.save_base_resume(resume_data)
        if success:
            logging.info("Successfully saved parsed resume to Supabase.")
        else:
            logging.warning("Failed to save parsed resume to Supabase.")

        # Save locally for verification
        output_path = os.path.join(os.path.dirname(__file__), 'parsed_resume.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=4)
        logging.info(f"Saved parsed resume to {output_path} for verification.")

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from AI: {e}")
        logging.error(f"Raw response: {parsed_resume_str}")
    except Exception as e:
        logging.error(f"An error occurred during data processing: {e}")

    # 5. Clean up temporary file
    if os.path.exists(pdf_file_path):
        try:
            os.remove(pdf_file_path)
            logging.info(f"Cleaned up temporary file: {pdf_file_path}")
        except Exception as e:
            logging.warning(f"Could not clean up {pdf_file_path}: {e}")

    logging.info("\nResume processing finished.")

if __name__ == "__main__":
    logging.info("Starting resume processing...")
    asyncio.run(main())
