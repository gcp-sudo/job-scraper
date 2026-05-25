
-- Enable the required pg_tle extension
CREATE EXTENSION IF NOT EXISTS pg_tle;

-- Drop existing tables and types if they exist to ensure a clean slate
DROP TABLE IF EXISTS "jobs_linkedin", "jobs_gulf", "jobs_startup", "jobs_freelance", "jobs_fresher", "base_resume", "customized_resumes", "archived_jobs" CASCADE;
DROP TYPE IF EXISTS "job_status";

-- Create a custom type for job status
CREATE TYPE "job_status" AS ENUM (
    'new',
    'scored',
    'resume_generated',
    'applied',
    'archived',
    'expired',
    'offer',
    'removed'
);

-- Create a generic function to create a job table
-- This reduces code duplication and ensures all job tables are identical.
CREATE OR REPLACE FUNCTION create_job_table(table_name TEXT)
RETURNS void AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            "id" TEXT PRIMARY KEY,
            "title" TEXT,
            "company" TEXT,
            "location" TEXT,
            "description_html" TEXT,
            "description_text" TEXT,
            "url" TEXT UNIQUE,
            "scraped_at" TIMESTAMPTZ DEFAULT now(),
            "source" TEXT,
            "status" job_status DEFAULT ''new'',
            "score" INTEGER DEFAULT 0,
            "is_active" BOOLEAN DEFAULT true,
            "resume_score_stage" TEXT,
            "customized_resume_id" UUID
        );
    ', table_name);
END;
$$ LANGUAGE plpgsql;

-- Select the function to create the tables
SELECT create_job_table('jobs_linkedin');
SELECT create_job_table('jobs_gulf');
SELECT create_job_table('jobs_startup');
SELECT create_job_table('jobs_freelance');
SELECT create_job_table('jobs_fresher');


-- Create the table for the parsed base resume
CREATE TABLE IF NOT EXISTS "base_resume" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "full_text" TEXT,
    "skills" TEXT[],
    "experience_summary" TEXT,
    "parsed_at" TIMESTAMPTZ DEFAULT now()
);

-- Create the table for customized resumes
CREATE TABLE IF NOT EXISTS "customized_resumes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "job_id" TEXT,
    "base_resume_id" UUID REFERENCES base_resume(id),
    "generated_resume_text" TEXT,
    "resume_url" TEXT,
    "created_at" TIMESTAMPTZ DEFAULT now()
);

-- Create the table for archived jobs
CREATE TABLE IF NOT EXISTS "archived_jobs" (
    "archived_id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "original_id" TEXT,
    "title" TEXT,
    "company" TEXT,
    "location" TEXT,
    "url" TEXT,
    "archived_at" TIMESTAMPTZ DEFAULT now(),
    "reason" TEXT
);

-- Create Storage Buckets
-- Note: Bucket creation is idempotent. If the bucket exists, it will be ignored.
-- We handle this in the app logic or assume it's done via Supabase UI.
-- For clarity in the schema, here's how you'd think about it:
-- INSERT into storage.buckets (id, name, public) values ('resumes', 'resumes', false);
-- INSERT into storage.buckets (id, name, public) values ('personalized_resumes', 'personalized_resumes', true);
