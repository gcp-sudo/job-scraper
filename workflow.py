
import logging
import asyncio
import config
import scraper
import score_jobs
import custom_resume_generator
import job_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_table_name(source: str) -> str:
    """Gets the table name for a given source from the config mapping."""
    table_name = config.TABLE_MAP.get(source)
    if not table_name:
        logging.error(f"No table mapping found for source: {source}")
        raise ValueError(f"Invalid source: {source}")
    return table_name

async def main():
    """Main orchestration function to run the entire job processing pipeline."""
    logging.info("--- Starting master workflow --- ")

    # The pipeline will run sequentially for each enabled source.
    for source in config.SCRAPING_SOURCES:
        logging.info(f"--- Processing source: {source} --- ")
        try:
            table_name = get_table_name(source)
            source_config = config.SEARCH_CONFIG.get(source, {})

            # --- 1. Scrape new jobs ---
            logging.info(f"Starting scraper for {source}")
            await scraper.run(source, source_config, table_name)

            # --- 2. Score new jobs ---
            logging.info(f"Starting job scoring for {source}")
            await score_jobs.run(table_name)

            # --- 3. Generate custom resumes ---
            logging.info(f"Starting resume generation for {source}")
            await custom_resume_generator.run(table_name)

            # --- 4. Perform job maintenance ---
            logging.info(f"Starting job maintenance for {source}")
            await job_manager.run(table_name)

            logging.info(f"--- Finished processing source: {source} --- ")

        except ValueError as e:
            # This will catch invalid source errors and continue to the next one.
            logging.error(e)
            continue
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing source {source}: {e}")
            # Continue to the next source even if one fails.
            continue

    logging.info("--- Master workflow finished --- ")

if __name__ == "__main__":
    asyncio.run(main())
