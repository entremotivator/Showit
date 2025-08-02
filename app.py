import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Call CRM", layout="wide")
st.title("📞 Call CRM – Multi-Entry Management")

# --- Session-state storage for multiple call records ---
if "call_records" not in st.session_state:
    st.session_state.call_records = []

# ----- Sidebar: CRM - Add New Call -----
with st.sidebar:
    st.header("➕ Add Call Record")

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
                "added_at": datetime.now().isoformat()
            })
            st.success("✔️ Call record added!")

st.header("📋 All Calls Overview")

# ---- Table displaying all records ----
if st.session_state.call_records:
    df = pd.DataFrame(st.session_state.call_records)
    df["transcript_short"] = df["transcript"].str.slice(0, 30) + "..."
    show_cols = ["call_id", "customer_number", "started_at", "cost", "transcript_short", "call_summary"]
    st.dataframe(df[show_cols], use_container_width=True)

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

else:
    st.info("No calls stored yet. Use the sidebar to add your first record.")

# --- Optional: Instructions and next steps for the CRM user ---
with st.expander("ℹ️ How to use this CRM"):
    st.write("""
    - Use the left sidebar to add as many call records as you need.
    - See summaries of all calls in the main table.
    - Click any Call ID to see its full CRM record, split into useful tabs.
    - Extend with Airtable/database for persistent storage when ready.
    """)
