-- Drop existing tables and functions to ensure a clean slate
DROP TABLE IF EXISTS "public"."jobs_linkedin" CASCADE;
DROP TABLE IF EXISTS "public"."jobs_gulf" CASCADE;
DROP TABLE IF EXISTS "public"."jobs_startup" CASCADE;
DROP TABLE IF EXISTS "public"."jobs_freelance" CASCADE;
DROP TABLE IF EXISTS "public"."jobs_fresher" CASCADE;
DROP TABLE IF EXISTS "public"."customized_resumes" CASCADE;
DROP TABLE IF EXISTS "public"."base_resume" CASCADE;

DROP FUNCTION IF EXISTS "public"."get_jobs_for_resume_generation_custom_sort"(text,integer,integer);
DROP FUNCTION IF EXISTS "public"."get_jobs_for_rescore"(text,integer);

-- Create a reusable function to create the job tables
CREATE OR REPLACE FUNCTION create_job_table(table_name TEXT)
RETURNS void AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS "public".%I (
            "job_id" TEXT NOT NULL PRIMARY KEY,
            "provider" TEXT NOT NULL,
            "scraped_at" TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            "company" TEXT,
            "job_title" TEXT,
            "level" TEXT,
            "location" TEXT,
            "description" TEXT,
            "status" TEXT DEFAULT ''new'' NOT NULL,
            "is_active" BOOLEAN DEFAULT true NOT NULL,
            "application_date" TIMESTAMP WITH TIME ZONE,
            "resume_score" INTEGER,
            "resume_score_stage" TEXT,
            "customized_resume_id" UUID,
            "notes" TEXT,
            "last_checked" TIMESTAMP WITH TIME ZONE DEFAULT ''1970-01-01 00:00:00+00'' NOT NULL
        );

        COMMENT ON TABLE "public".%I IS ''Stores job postings scraped from %s'';
    ', table_name, table_name, table_name);
END;
$$ LANGUAGE plpgsql;

-- Create all the job tables
SELECT create_job_table('jobs_linkedin');
SELECT create_job_table('jobs_gulf');
SELECT create_job_table('jobs_startup');
SELECT create_job_table('jobs_freelance');
SELECT create_job_table('jobs_fresher');

-- Drop the helper function as it's no longer needed
DROP FUNCTION create_job_table(text);

-- Create customized_resumes table
CREATE TABLE IF NOT EXISTS "public"."customized_resumes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL PRIMARY KEY,
    "name" "text" NOT NULL,
    "email" "text" NOT NULL,
    "phone" "text",
    "location" "text",
    "summary" "text",
    "skills" "text"[],
    "education" "jsonb",
    "experience" "jsonb",
    "projects" "jsonb",
    "certifications" "jsonb",
    "languages" "text"[],
    "links" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "last_updated" timestamp with time zone DEFAULT "now"(),
    "resume_link" "text"
);

-- Create base_resume table
CREATE TABLE "public"."base_resume" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    "resume_data" JSONB
);
ALTER TABLE "public"."base_resume" ADD CONSTRAINT "base_resume_pkey" PRIMARY KEY ("id");


-- Add Foreign Key constraint to job tables
DO $$
DECLARE
    t_name TEXT;
BEGIN
    FOR t_name IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'jobs_%'
    LOOP
        EXECUTE format('ALTER TABLE "public".%I ADD CONSTRAINT fk_customized_resume FOREIGN KEY (customized_resume_id) REFERENCES "public"."customized_resumes"(id) ON DELETE SET NULL;', t_name);
    END LOOP;
END;
$$;

-- RLS Policies
ALTER TABLE "public"."customized_resumes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."base_resume" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON "public"."customized_resumes" FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON "public"."base_resume" FOR SELECT USING (true);

DO $$
DECLARE
    t_name TEXT;
BEGIN
    FOR t_name IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'jobs_%'
    LOOP
        EXECUTE format('ALTER TABLE "public".%I ENABLE ROW LEVEL SECURITY;', t_name);
        EXECUTE format('CREATE POLICY "Enable read access for all users" ON "public".%I FOR SELECT USING (true);', t_name);
    END LOOP;
END;
$$;

-- Create updated RPC functions
CREATE OR REPLACE FUNCTION get_jobs_for_resume_generation_custom_sort(p_table_name text, p_page_number integer, p_page_size integer)
RETURNS SETOF json
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY EXECUTE format('
    SELECT row_to_json(t) FROM (
      SELECT 
        job_id, job_title, company, description, level, resume_score
      FROM public.%I
      WHERE status = ''new'' AND resume_score IS NOT NULL
      ORDER BY resume_score DESC, scraped_at DESC
      LIMIT %s OFFSET %s
    ) t', p_table_name, p_page_size, (p_page_number - 1) * p_page_size);
END;
$$;


CREATE OR REPLACE FUNCTION get_jobs_for_rescore(p_table_name text, p_limit_val integer)
RETURNS SETOF json
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY EXECUTE format('
    SELECT row_to_json(t) FROM (
      SELECT 
          j.job_id, 
          j.job_title, 
          j.company, 
          j.description, 
          j.level, 
          j.customized_resume_id,
          cr.resume_link
      FROM public.%I j
      JOIN public.customized_resumes cr ON j.customized_resume_id = cr.id
      WHERE j.status = ''resume_generated'' AND j.resume_score_stage = ''initial''
      ORDER BY j.resume_score DESC
      LIMIT %s
    ) t', p_table_name, p_limit_val);
END;
$$;

-- Grant usage on functions
GRANT EXECUTE ON FUNCTION public.get_jobs_for_resume_generation_custom_sort(text, integer, integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.get_jobs_for_rescore(text, integer) TO service_role;
