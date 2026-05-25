# AI-Powered Job Application Automation Suite

This project is a sophisticated, AI-driven suite of tools designed to automate the entire job application process, from scraping and scoring new job postings to generating customized, keyword-optimized resumes for each application.

The system is architected around two core, decoupled workflows:

1.  **Resume Parsing Workflow (`parse_resume.yml`):** A manually triggered workflow that parses your base resume, extracts key skills and experience, and stores this structured data in your Supabase database. This workflow should be run once, or whenever you update your master resume.
2.  **Job Processing Workflow (`job_processing.yml`):** A scheduled or manually triggered workflow that continuously scrapes jobs from multiple sources, scores them against your parsed resume, and automatically generates tailored resumes for the highest-scoring opportunities.

This dual-workflow architecture ensures that your resume is parsed only when necessary, saving significant time and computational resources.

## Key Features

*   **Interactive Web Dashboard:** A built-in Streamlit dashboard to visualize your job pipeline, filter results, and download customized resumes.
*   **Multi-Source Job Scraping:** Aggregates job postings from LinkedIn, GulfTalent, and other niche job boards.
*   **AI-Powered Job Scoring:** Uses Large Language Models (LLMs) to intelligently score and rank jobs based on their relevance to your skills and experience.
*   **Automated Resume Customization:** Generates a unique, keyword-optimized resume for each high-scoring job, significantly increasing your chances of passing ATS filters.
*   **Dynamic LLM Fallback:** Intelligently switches between multiple LLM providers (Gemini, OpenAI, Groq) to ensure high availability and cost-effectiveness.
*   **Cloud-Native & Serverless:** Built entirely on a modern, serverless stack using Supabase for the database and storage, and GitHub Actions for orchestration.

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

1.  **Python & Pip:** Ensure you have Python 3.8+ and pip installed on your local machine.
2.  **Supabase Project:** Create a new project on [Supabase](https://supabase.com/).
3.  **API Keys:** Obtain API keys for the LLM providers you wish to use (Gemini, OpenAI, Groq).
4.  **GitHub Account:** A GitHub account with access to GitHub Actions.

### Setup Instructions

1.  **Clone this Repository:** Clone this repository to your local machine.
2.  **Create `.env` file:** In the root of the project, create a file named `.env` and add your credentials:
    ```
    SUPABASE_URL="your_supabase_project_url"
    SUPABASE_SERVICE_ROLE_KEY="your_supabase_service_role_key"
    GEMINI_API_KEY="your_gemini_api_key"
    OPENAI_API_KEY="your_openai_api_key"
    GROQ_API_KEY="your_groq_api_key"
    ```
3.  **Install Dependencies:** Open a terminal in the project root and run:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create Supabase Tables:** In the Supabase SQL Editor, run the `schema.sql` script to create the required tables and storage buckets.
5.  **Run the "Parse Resume" Workflow:** To use the automated GitHub Actions, set up the secrets as described in the original `README.md` and run the "Parse Resume" workflow from the Actions tab.
6.  **Run the "Job Processing" Workflow:** Enable and run the "Job Processing" workflow from the Actions tab.

## Running the Web Dashboard

This project includes an interactive web dashboard built with Streamlit to help you visualize your job data.

1.  **Ensure Dependencies are Installed:** Make sure you have completed the setup steps and installed all the packages from `requirements.txt`.
2.  **Run the App:** In your terminal, from the project root, run the following command:
    ```bash
    streamlit run app.py
    ```
3.  **View in Browser:** The command will start a local web server and provide you with a URL (usually `http://localhost:8501`). Open this URL in your web browser to view the dashboard.

## Technical Details

*   **Dashboard:** [Streamlit](https://streamlit.io/)
*   **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
*   **Storage:** [Supabase Storage](https://supabase.com/storage)
*   **Orchestration:** [GitHub Actions](https://github.com/features/actions)
*   **LLM Integration:** [LiteLLM](https://github.com/BerriAI/litellm)
*   **Web Scraping:** [Playwright](https://playwright.dev/)

This project is designed to be a powerful and flexible platform for automating your job search. By leveraging the latest in AI and cloud technology, it gives you a significant advantage in today's competitive job market.
