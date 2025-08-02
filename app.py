import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
from io import StringIO

st.set_page_config(page_title="Call CRM", layout="wide")
st.title("📞 Call CRM – Multi-Entry Management")

# --- Session-state storage for multiple call records ---
if "call_records" not in st.session_state:
    st.session_state.call_records = []

# Function to load data from Google Sheets
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_google_sheets_data(sheet_url):
    """Load data from a public Google Sheets URL"""
    try:
        # Extract the sheet ID from the URL
        if "/spreadsheets/d/" in sheet_url:
            # Extract sheet ID from URL like: https://docs.google.com/spreadsheets/d/SHEET_ID/edit...
            sheet_id = sheet_url.split("/spreadsheets/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            # Fallback for other URL formats
            csv_url = sheet_url + "/export?format=csv"
        
        # Fetch the data
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV data
        df = pd.read_csv(StringIO(response.text))
        return df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {str(e)}")
        return None

# Function to convert Google Sheets data to call records format
def convert_sheets_to_records(df):
    """Convert Google Sheets DataFrame to call records format"""
    records = []
    for _, row in df.iterrows():
        # Map the actual column names from the Google Sheet to our expected format
        record = {
            "transcript": str(row.get("transcript", row.get("call_summary", ""))),  # Use call_summary if transcript not available
            "recording_url": str(row.get("recording_url", "")),
            "call_summary": str(row.get("call_summary", "")),
            "cost": float(row.get("cost", row.get("call_cost", 0.0))) if pd.notna(row.get("cost", row.get("call_cost"))) else 0.0,
            "customer_number": str(row.get("customer_number", row.get("phone number", ""))),
            "started_at": str(row.get("started_at", row.get("call_start_time", ""))),
            "ended_at": str(row.get("ended_at", row.get("call_end_time", ""))),
            "call_id": str(row.get("call_id", f"SHEET{len(records) + 1:04d}")),
            "added_at": datetime.now().isoformat(),
            "source": "google_sheets"
        }
        records.append(record)
    return records

# ----- Sidebar: CRM - Add New Call & File Upload -----
with st.sidebar:
    st.header("➕ Add Call Record")

    # Manual entry form
    with st.form("add_call_form", clear_on_submit=True):
        transcript = st.text_area("Transcript", height=100)
        recording_url = st.text_input("Recording URL (audio link)", placeholder="https://...")
        call_summary = st.text_area("Summary", height=60)
        cost = st.number_input("Cost (USD)", min_value=0.0, format="%.3f")
        customer_number = st.text_input("Customer Number", placeholder="+1...")
        started_at = st.text_input("Started At (ISO)", placeholder="YYYY-MM-DDTHH:MM:SSZ")
        ended_at = st.text_input("Ended At (ISO)", placeholder="YYYY-MM-DDTHH:MM:SSZ")
        call_id = st.text_input("Call ID")

        submitted = st.form_submit_button("Add Call")
        if submitted:
            st.session_state.call_records.append({
                "transcript": transcript,
                "recording_url": recording_url,
                "call_summary": call_summary,
                "cost": cost,
                "customer_number": customer_number,
                "started_at": started_at,
                "ended_at": ended_at,
                "call_id": call_id if call_id else f"ID{len(st.session_state.call_records) + 1:04d}",
                "added_at": datetime.now().isoformat(),
                "source": "manual"
            })
            st.success("✔️ Call record added!")

    st.divider()
    
    # JSON file upload section
    st.header("📁 Upload JSON Data")
    uploaded_file = st.file_uploader(
        "Choose a JSON file",
        type=['json'],
        help="Upload a JSON file containing call records"
    )
    
    if uploaded_file is not None:
        try:
            # Read and parse JSON file
            json_data = json.load(uploaded_file)
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                # If it's a list of records
                records_to_add = json_data
            elif isinstance(json_data, dict) and "records" in json_data:
                # If it's wrapped in a "records" key
                records_to_add = json_data["records"]
            elif isinstance(json_data, dict):
                # If it's a single record
                records_to_add = [json_data]
            else:
                st.error("Invalid JSON format")
                records_to_add = []
            
            if st.button("Import JSON Records"):
                imported_count = 0
                for record in records_to_add:
                    # Ensure all required fields exist with defaults
                    formatted_record = {
                        "transcript": record.get("transcript", ""),
                        "recording_url": record.get("recording_url", ""),
                        "call_summary": record.get("call_summary", ""),
                        "cost": float(record.get("cost", 0.0)),
                        "customer_number": record.get("customer_number", ""),
                        "started_at": record.get("started_at", ""),
                        "ended_at": record.get("ended_at", ""),
                        "call_id": record.get("call_id", f"JSON{len(st.session_state.call_records) + imported_count + 1:04d}"),
                        "added_at": datetime.now().isoformat(),
                        "source": "json_upload"
                    }
                    st.session_state.call_records.append(formatted_record)
                    imported_count += 1
                
                st.success(f"✔️ Imported {imported_count} records from JSON!")
                st.rerun()
                
        except json.JSONDecodeError:
            st.error("Invalid JSON file format")
        except Exception as e:
            st.error(f"Error processing JSON file: {str(e)}")
    
    st.divider()
    
    # Google Sheets integration section
    st.header("📊 Google Sheets Integration")
    
    # Default Google Sheets URL
    default_sheets_url = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/"
    
    sheets_url = st.text_input(
        "Google Sheets URL",
        value=default_sheets_url,
        help="Enter a public Google Sheets URL"
    )
    
    if st.button("Load from Google Sheets"):
        with st.spinner("Loading data from Google Sheets..."):
            sheets_df = load_google_sheets_data(sheets_url)
            
            if sheets_df is not None:
                sheets_records = convert_sheets_to_records(sheets_df)
                
                # Add records to session state
                for record in sheets_records:
                    st.session_state.call_records.append(record)
                
                st.success(f"✔️ Loaded {len(sheets_records)} records from Google Sheets!")
                st.rerun()
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh from Google Sheets (every 5 minutes)")
    if auto_refresh:
        st.info("Data will be automatically refreshed from Google Sheets")

st.header("📋 All Calls Overview")

# ---- Table displaying all records ----
if st.session_state.call_records:
    df = pd.DataFrame(st.session_state.call_records)
    df["transcript_short"] = df["transcript"].str.slice(0, 30) + "..."
    
    # Add source column to show data origin
    show_cols = ["call_id", "customer_number", "started_at", "cost", "transcript_short", "call_summary", "source"]
    st.dataframe(df[show_cols], use_container_width=True)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Calls", len(df))
    with col2:
        st.metric("Total Cost", f"${df['cost'].sum():.2f}")
    with col3:
        st.metric("Manual Entries", len(df[df['source'] == 'manual']))
    with col4:
        st.metric("Imported Records", len(df[df['source'].isin(['json_upload', 'google_sheets'])]))

    call_ids = df["call_id"].tolist()
    sel_call_id = st.selectbox("🔎 Select Call to View in CRM", call_ids)
    sel_record = df[df["call_id"] == sel_call_id].iloc[0].to_dict()

    # ---- CRM Tabs for selected record ----
    crm_tabs = st.tabs(["Transcript", "Summary", "Customer Info", "Recording", "Cost & Timing"])

    with crm_tabs[0]:
        st.subheader("Transcript")
        st.text_area("Full Transcript", value=sel_record["transcript"], height=200, key=f"transcript_{sel_call_id}")

    with crm_tabs[1]:
        st.subheader("Summary")
        st.write(sel_record["call_summary"])

    with crm_tabs[2]:
        st.subheader("Customer Information")
        st.text_input("Phone Number", value=sel_record["customer_number"], disabled=True, key=f"number_{sel_call_id}")
        st.text_input("Call ID", value=sel_record["call_id"], disabled=True, key=f"id_{sel_call_id}")
        st.text_input("Data Source", value=sel_record.get("source", "unknown"), disabled=True, key=f"source_{sel_call_id}")

    with crm_tabs[3]:
        st.subheader("Call Recording")
        if sel_record["recording_url"]:
            st.audio(sel_record["recording_url"], format="audio/wav")
        else:
            st.info("No recording URL for this call.")

    with crm_tabs[4]:
        st.subheader("Cost and Timing")
        st.metric("Cost (USD)", f"${sel_record['cost']:.2f}")
        st.write(f"Started At: {sel_record['started_at']}")
        st.write(f"Ended At: {sel_record['ended_at']}")
        st.write(f"Added to CRM: {sel_record['added_at']}")

    # Clear all records button
    st.divider()
    if st.button("🗑️ Clear All Records", type="secondary"):
        st.session_state.call_records = []
        st.success("All records cleared!")
        st.rerun()

else:
    st.info("No calls stored yet. Use the sidebar to add records manually, upload JSON, or load from Google Sheets.")

# --- Instructions and next steps for the CRM user ---
with st.expander("ℹ️ How to use this Enhanced CRM"):
    st.write("""
    **Manual Entry:**
    - Use the left sidebar form to add individual call records.
    
    **JSON Upload:**
    - Upload JSON files containing multiple call records.
    - Supports both single records and arrays of records.
    - JSON should contain fields: transcript, recording_url, call_summary, cost, customer_number, started_at, ended_at, call_id.
    
    **Google Sheets Integration:**
    - Load data directly from public Google Sheets.
    - Data is cached for 5 minutes for better performance.
    - Columns should match the call record fields.
    
    **Viewing Data:**
    - See summaries of all calls in the main table with source tracking.
    - Click any Call ID to see its full CRM record in organized tabs.
    - View statistics including total calls, costs, and data sources.
    
    **Data Management:**
    - Clear all records using the clear button.
    - All data sources are merged into a unified view.
    """)

