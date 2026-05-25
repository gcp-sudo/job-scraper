# AI-Powered Job Application Automation Suite

This project is a sophisticated, AI-driven suite of tools designed to automate the entire job application process, from scraping and scoring new job postings to generating customized, keyword-optimized resumes for each application.

The system is architected around two core, decoupled workflows:

1.  **Resume Parsing Workflow (`parse_resume.yml`):** A manually triggered workflow that parses your base resume, extracts key skills and experience, and stores this structured data in your Supabase database. This workflow should be run once, or whenever you update your master resume.
2.  **Job Processing Workflow (`job_processing.yml`):** A scheduled or manually triggered workflow that continuously scrapes jobs from multiple sources, scores them against your parsed resume, and automatically generates tailored resumes for the highest-scoring opportunities.

This dual-workflow architecture ensures that your resume is parsed only when necessary, saving significant time and computational resources.

## Key Features

*   **Multi-Source Job Scraping:** Aggregates job postings from LinkedIn, GulfTalent, and other niche job boards.
*   **AI-Powered Job Scoring:** Uses Large Language Models (LLMs) to intelligently score and rank jobs based on their relevance to your skills and experience.
*   **Automated Resume Customization:** Generates a unique, keyword-optimized resume for each high-scoring job, significantly increasing your chances of passing ATS filters.
*   **Dynamic LLM Fallback:** Intelligently switches between multiple LLM providers (Gemini, OpenAI, Groq) to ensure high availability and cost-effectiveness.
*   **Cloud-Native & Serverless:** Built entirely on a modern, serverless stack using Supabase for the database and storage, and GitHub Actions for orchestration.
*   **Centralized Configuration:** A single, easy-to-manage `config.py` file allows for simple configuration of all system parameters.

## How It Works

### 1. Resume Parsing Workflow

1.  **Manual Trigger:** You initiate the "Parse Resume" workflow manually via the GitHub Actions tab.
2.  **Upload Resume:** The workflow prompts you to upload your master resume in PDF format.
3.  **Parse & Store:** The system parses the PDF, extracts your skills, experience, and other relevant data, and stores it in the `base_resume` table in your Supabase database.

### 2. Job Processing Workflow

1.  **Scrape Jobs:** The workflow scrapes new job postings from the sources defined in your `config.py`.
2.  **Store New Jobs:** New jobs are stored in their respective tables in the Supabase database (e.g., `jobs_linkedin`).
3.  **Score Jobs:** The AI scoring module fetches the new jobs and your parsed resume data. It then uses an LLM to assign a relevance score to each job.
4.  **Generate Custom Resumes:** For the top-scoring jobs, the system generates a new, customized resume (in PDF format) and stores it in the `personalized_resumes` bucket in Supabase Storage.

## Getting Started

### Prerequisites

1.  **Supabase Project:** Create a new project on [Supabase](https://supabase.com/).
2.  **API Keys:** Obtain API keys for the LLM providers you wish to use (Gemini, OpenAI, Groq).
3.  **GitHub Account:** A GitHub account with access to GitHub Actions.

### Setup Instructions

1.  **Fork this Repository:** Fork this repository to your own GitHub account.
2.  **Create Supabase Tables:** In the Supabase SQL Editor, run the `schema.sql` script to create the required tables and storage buckets.
3.  **Set up GitHub Secrets:** In your forked repository, go to `Settings > Secrets and variables > Actions` and create the following secrets:
    *   `SUPABASE_URL`: Your Supabase project URL.
    *   `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key.
    *   `GEMINI_API_KEY`: Your Google AI Studio API key.
    *   `OPENAI_API_KEY`: Your OpenAI API key.
    *   `GROQ_API_KEY`: Your Groq API key.
4.  **Configure `config.py`:** Review and customize the `config.py` file to set your desired search queries, scraping sources, and LLM preferences. The `LLM_PROVIDER` variable determines which LLM will be used as the primary model.
5.  **Run the "Parse Resume" Workflow:**
    *   Go to the "Actions" tab in your repository.
    *   Select the "Parse Resume" workflow.
    *   Click "Run workflow" and upload your master resume when prompted.
6.  **Enable and Run the "Job Processing" Workflow:**
    *   Go to the "Actions" tab.
    *   Enable the "Job Processing" workflow.
    *   You can now run this workflow manually or let it run on its schedule.

## Technical Details

*   **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
*   **Storage:** [Supabase Storage](https://supabase.com/storage)
*   **Orchestration:** [GitHub Actions](https://github.com/features/actions)
*   **LLM Integration:** [LiteLLM](https://github.com/BerriAI/litellm)
*   **Web Scraping:** [Playwright](https://playwright.dev/)

This project is designed to be a powerful and flexible platform for automating your job search. By leveraging the latest in AI and cloud technology, it gives you a significant advantage in today's competitive job market.
