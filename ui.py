import os
import streamlit as st
import requests
import time
import pandas as pd

# 1. SETUP & CONFIG
API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Morocco Invoice Validator", layout="wide")

st.markdown("""
    <style>
    span[data-testid="stMainMenu"] {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# 2. SESSION STATE MANAGEMENT
if "invoice_tasks" not in st.session_state:
    st.session_state.invoice_tasks = []  # Stores all task data persistently
if "uploading" not in st.session_state:
    st.session_state.uploading = False   # Tracks the upload phase
if "batch_notified" not in st.session_state:
    st.session_state.batch_notified = False # Tracks if we've shown the toast
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0    # Unique ID to force-reset the uploader

# --- HELPER: RENDER RESULT DASHBOARD ---
def render_invoice_report(data):
    """Renders the final report for a single invoice."""
    if not data:
        st.error("No result data found.")
        return

    # Handle System Errors (e.g., OCR crash)
    if "error" in data and "extracted_data" not in data:
        st.error(f"❌ Processing Failed: {data['error']}")
        return

    extracted = data.get("extracted_data", {})

    # 1. Validation Banner
    if data.get("is_valid"):
        st.success("✅ **INVOICE VALID** - Passed all compliance checks.")
    else:
        st.error(f"❌ **INVOICE INVALID** - Found {len(data.get('issues', []))} issues.")

    # 2. Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invoice #", extracted.get('meta', {}).get('invoice_number', 'N/A'))
    col2.metric("Date", extracted.get('meta', {}).get('date', 'N/A'))
    col3.metric("Total TTC", f"{extracted.get('financials', {}).get('total_ttc', 0):,.2f} DH")
    col4.metric("ICE Check", "✅ Match" if data.get('is_valid') else "⚠️ Check")

    # 3. Compliance Issues List
    if data.get("issues"):
        st.divider()
        st.subheader("⚠️ Compliance Issues")
        for issue in data["issues"]:
            with st.chat_message("assistant", avatar="🚨"):
                st.write(f"**{issue['field']}**: {issue['message']}")

    # 4. Line Items Table
    st.divider()
    st.subheader("📦 Line Items")
    if extracted.get("items"):
        df = pd.DataFrame(extracted["items"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No line items detected.")

    # 5. Raw JSON Viewer
    with st.expander("🔍 View Raw JSON"):
        st.json(data)


# 3. SIDEBAR & UPLOAD
with st.sidebar:
    st.header("Upload Files")
    
    # Dynamic Key: Changing this key forces the widget to reset
    uploaded_files = st.file_uploader(
        "Select PDF Invoices", 
        type=["pdf"], 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}" 
    )
    
    if uploaded_files and len(uploaded_files) > 10:
        st.warning("⚠️ Limit is 10 files.")
        uploaded_files = uploaded_files[:10]

    def start_upload():
        st.session_state.uploading = True
        st.session_state.invoice_tasks = [] 
        st.session_state.batch_notified = False 

    st.button(
        "🚀 Validate All Files", 
        disabled=not uploaded_files or st.session_state.uploading,
        type="primary",
        on_click=start_upload
    )

# ==========================================
#  PHASE 1: UPLOAD (Run Once)
# ==========================================
if st.session_state.uploading:
    with st.status("📤 Uploading files...", expanded=True) as status:
        active_tasks = []
        for uploaded_file in uploaded_files:
            try:
                uploaded_file.seek(0) # Safety rewind
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                
                response = requests.post(f"{API_URL}/invoices/validate", files=files)
                
                # Rate Limit Handling (429)
                if response.status_code == 429:
                    status.warning(f"⚠️ Rate limit hit on '{uploaded_file.name}'. Skipping...")
                    time.sleep(1)
                    continue
                
                response.raise_for_status()
                task_data = response.json()
                
                active_tasks.append({
                    "filename": uploaded_file.name,
                    "task_id": task_data["task_id"],
                    "start_time": time.time(),
                    "completed": False,
                    "result": None
                })
                status.write(f"✅ Uploaded {uploaded_file.name}")
                time.sleep(0.2) # Polite throttle

            except Exception as e:
                status.error(f"❌ Failed to upload {uploaded_file.name}: {e}")
        
        # Save State & Reset Uploader
        st.session_state.invoice_tasks = active_tasks
        st.session_state.uploading = False
        st.session_state.uploader_key += 1 # <--- This clears the sidebar for the next run!
        
        status.update(label="✅ Uploads Complete!", state="complete", expanded=False)
        time.sleep(1)
        st.rerun() # Refresh immediately to show Phase 2

# ==========================================
#  PHASE 2: RENDER TABS & POLL
# ==========================================
if st.session_state.invoice_tasks:
    st.subheader("📊 Analysis Results")
    
    # 1. Check Progress Stats
    pending_count = sum(1 for t in st.session_state.invoice_tasks if not t['completed'])
    total_count = len(st.session_state.invoice_tasks)
    all_done = (pending_count == 0)

    # 2. SUCCESS NOTIFICATION (Banner + Toast)
    if all_done:
        # A. Persistent Banner (Always visible)
        st.success(f"✅ Batch Complete! Processed {total_count}/{total_count} invoices.")
        
        # B. One-time Toast (Pop-up)
        if not st.session_state.batch_notified:
            st.toast("🎉 Batch processing finished!", icon="✅")
            st.session_state.batch_notified = True

    # 3. RENDER TABS
    tab_names = [t['filename'] for t in st.session_state.invoice_tasks]
    if not tab_names:
        st.warning("No files were successfully uploaded.")
    else:
        tabs = st.tabs(tab_names)
        active_placeholders = {} 

        for i, task in enumerate(st.session_state.invoice_tasks):
            with tabs[i]:
                if task['completed']:
                    # STATIC: Final Dashboard
                    render_invoice_report(task['result'])
                else:
                    # DYNAMIC: Loading Animation
                    st.info("⏳ AI is analyzing this document...")
                    p_bar = st.progress(0)
                    p_text = st.empty()
                    active_placeholders[task['task_id']] = (p_bar, p_text)

    # 4. POLLING LOOP (Runs in background if needed)
    if not all_done:
        while True:
            any_updated = False
            
            for task in st.session_state.invoice_tasks:
                if task['completed']:
                    continue # Skip finished tasks
                
                # Update Animation
                elapsed = int(time.time() - task["start_time"])
                if task['task_id'] in active_placeholders:
                    p_bar, p_text = active_placeholders[task['task_id']]
                    if elapsed < 300:
                        p_bar.progress(min(elapsed * 2, 95))
                        p_text.caption(f"Processing... ({elapsed}s)")
                
                # Check API Status
                try:
                    check = requests.get(f"{API_URL}/invoices/status/{task['task_id']}")
                    result = check.json()
                    status = result.get("status", "").lower()

                    if status == "completed":
                        task["completed"] = True
                        task["result"] = result["data"]
                        any_updated = True 
                    elif status == "failed":
                        task["completed"] = True
                        task["result"] = {"error": result.get("error")}
                        any_updated = True
                except:
                    pass
            
            # If ANY task finished, refresh page to show its Final Dashboard
            if any_updated:
                st.rerun()
            
            time.sleep(1)