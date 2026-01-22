import os
import streamlit as st
import requests
import time
import pandas as pd


API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Morocco Invoice Validator", layout="wide")

st.title("🇲🇦 Morocco Invoice Validator (Async AI)")
st.markdown("Upload a PDF invoice to validate math, ICE codes, and tax compliance.")


uploaded_file = st.file_uploader("Upload Invoice (PDF)", type=["pdf"])

if uploaded_file:
    if st.button("🔍 Validate Invoice"):
        

        with st.spinner("Uploading to Server..."):
            files = {"file": uploaded_file.getvalue()}
            # We use the filename to handle extension checks
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            
            try:
                response = requests.post(f"{API_URL}/invoices/validate", files=files)
                response.raise_for_status()
                task_data = response.json()
                task_id = task_data["task_id"]
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")
                st.stop()


        progress_bar = st.progress(0)
        status_text = st.empty()
        
        extracted_data = None
        

        for i in range(60):
            status_text.text(f"Processing... (Time: {i}s)")
            progress_bar.progress(i + 1)
            
            check = requests.get(f"{API_URL}/invoices/status/{task_id}")
            result = check.json()
            
            if result["status"] == "Completed":
                extracted_data = result["data"]
                progress_bar.progress(100)
                status_text.text("✅ Processing Complete!")
                break
            
            elif result["status"] == "Failed":
                st.error(f"Processing Failed: {result.get('error')}")
                st.stop()
                
            time.sleep(1)


        if extracted_data:
            st.divider()
            
            if extracted_data.get("status") == "failed":
                st.error(f"❌ Processing Error: {extracted_data.get('error')}")
                st.warning("Tip: If this is 'Connection refused', vLLM might still be loading. Wait 30s and try again.")
                st.stop()

            if extracted_data["is_valid"]:
                st.success(f"✅ **VALID INVOICE** verified by AI")
            else:
                st.error(f"❌ **INVALID INVOICE** - Found {len(extracted_data['issues'])} issues")

      
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📑 Extracted Details")
                data = extracted_data["extracted_data"]
                st.write(f"**Invoice #:** {data['meta']['invoice_number']}")
                st.write(f"**Date:** {data['meta']['date']}")
                st.write(f"**Seller:** {data['seller']['name']}")
                st.write(f"**Client:** {data['client']['name']}")
                
                st.subheader("💰 Financials")
                metrics = data["financials"]
                st.metric("Total HT", f"{metrics['total_ht']:,.2f} DH")
                st.metric("Total TVA", f"{metrics['total_tva']:,.2f} DH")
                st.metric("Total TTC", f"{metrics['total_ttc']:,.2f} DH")

            with col2:
                st.subheader("🛡️ Validation Report")
                if not extracted_data["issues"]:
                    st.info("No compliance issues found. Calculations and ICE codes match.")
                else:
                    for issue in extracted_data["issues"]:
                 
                        msg = f"**{issue['field']}**: {issue['message']}"
                        if issue['error_type'] == "Math Mismatch":
                            st.warning(msg)
                        else:
                            st.error(msg)
            
   
            st.subheader("📦 Line Items")
            items_df = pd.DataFrame(data["items"])
            st.dataframe(items_df, use_container_width=True)

            with st.expander("View Raw JSON"):
                st.json(extracted_data)