import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Job Application Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Environment and Supabase Setup ---
load_dotenv()

@st.cache_resource
def init_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        st.error("Supabase URL or Key is missing. Please set them in your .env file or environment variables.")
        st.stop()
    return create_client(url, key)

supabase = init_supabase_client()

# --- Data Loading ---

@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_all_jobs() -> pd.DataFrame:
    """Fetch all jobs from every job table in Supabase."""
    all_jobs = []
    # These are the table names as defined in your config.py
    job_tables = ["jobs_linkedin", "jobs_gulf", "jobs_startup", "jobs_freelance", "jobs_fresher"]
    for table in job_tables:
        try:
            response = supabase.table(table).select("*", count='exact').execute()
            if response.data:
                df = pd.DataFrame(response.data)
                df['source'] = table.replace("jobs_", "").capitalize()
                all_jobs.append(df)
        except Exception as e:
            st.warning(f"Could not load data from table: {table}. Error: {e}")
    
    if not all_jobs:
        return pd.DataFrame() # Return empty dataframe if no data

    # Concatenate and process the dataframe
    full_df = pd.concat(all_jobs, ignore_index=True)
    full_df["scraped_at"] = pd.to_datetime(full_df["scraped_at"])
    full_df = full_df.sort_values(by="scraped_at", ascending=False)
    return full_df

@st.cache_data(ttl=600)
def fetch_custom_resumes() -> pd.DataFrame:
    """Fetches the metadata for all generated custom resumes."""
    try:
        response = supabase.table("customized_resumes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Failed to load custom resumes: {e}")
    return pd.DataFrame()

# --- UI Rendering ---

st.title("🤖 AI Job Application Dashboard")

# --- Main Data & Metrics ---
jobs_df = fetch_all_jobs()
resumes_df = fetch_custom_resumes()

if jobs_df.empty:
    st.warning("No job data found. Please run the job processing workflow.")
    st.stop()

# --- Metrics Row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs Scraped", len(jobs_df))
col2.metric("Jobs Scored > 7", len(jobs_df[jobs_df["score"] > 7]))
col3.metric("Custom Resumes Generated", len(resumes_df))
col4.metric("Jobs Applied To", len(jobs_df[jobs_df["status"] == 'applied']))

st.divider()

# --- Interactive Dashboard ---

st.header("All Scraped Jobs")

# --- Filtering ---
with st.sidebar:
    st.header("Filter Jobs")
    
    # Filter by source
    sources = st.multiselect(
        "Job Source",
        options=jobs_df['source'].unique(),
        default=jobs_df['source'].unique()
    )
    
    # Filter by status
    statuses = st.multiselect(
        "Job Status",
        options=jobs_df['status'].unique(),
        default=['new', 'scored', 'resume_generated'] # Sensible defaults
    )

    # Filter by score
    min_score, max_score = st.slider(
        'Filter by Score', 
        min_value=0, max_value=10, value=(0, 10)
    )

# Apply filters
filtered_df = jobs_df[
    (jobs_df['source'].isin(sources)) &
    (jobs_df['status'].isin(statuses)) &
    (jobs_df['score'].between(min_score, max_score))
]

st.dataframe(
    filtered_df,
    column_config={
        "url": st.column_config.LinkColumn("Job Link", display_text="🔗"),
        "scraped_at": st.column_config.DateColumn("Scraped On", format="YYYY-MM-DD"),
        "score": st.column_config.NumberColumn("Score", format="%d ⭐")
    },
    use_container_width=True,
    hide_index=True,
)

st.divider()

# --- Generated Resumes Section ---
st.header("Generated Custom Resumes")

if not resumes_df.empty:
    # Join with jobs data to show company/title
    merged_resumes = pd.merge(
        resumes_df, 
        jobs_df, 
        left_on='job_id', 
        right_on='id', 
        how='left',
        suffixes= ('_resume', '_job')
    )

    st.dataframe(
        merged_resumes[['title', 'company', 'score', 'resume_url']],
        column_config={
            "resume_url": st.column_config.LinkColumn("Download Resume", display_text="📄 Download")
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No custom resumes have been generated yet.")

