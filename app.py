import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header & Branding
st.markdown("<h1 style='text-align: center;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Official Compliance Decision Support</p>", unsafe_allow_html=True)

# 3. Sidebar Resources
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Helplines")
    st.write("TSS: 0800 060 8888")
    st.write("DAERA: 0300 200 7840")

# 4. Input Handling
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        # Load CSV and force the first column into a list
        df = pd.read_csv(file)
        final_list = df.iloc[:, 0].dropna().astype(str).tolist()

# 5. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.error("⚠️ No items found. Please check your input or CSV file.")
    else:
        # THE THROBBER: A simple, reliable progress bar
        progress_text = "Checking HMRC servers... please wait."
        my_bar = st.progress(0, text=progress_text)
        
        audit_data = []
        
        # PROCESS ITEMS ONE BY ONE
        for index, item in enumerate(final_list):
            # Update Throbber
            progress_pct = (index + 1) / len(final_list)
            my_bar.progress(progress_pct, text=f"Analyzing: {item}")
            
            # Logic: Map common words to codes or extract digits
            manual_map = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
            code = manual_map.get(item.lower()) or ''.join(filter(str.isdigit, item))
            
            if not code:
                st.warning(f"❓ Could not find a code for: {item}")
                continue

            try:
                # API Call
                res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=10)
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                if res.status_code == 200:
                    raw_body = res.text.lower()
                    if code[:2] in ['72', '73']:
                        lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                    elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw_body:
                        lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert + 'Not for EU' Label", "orange"

                # SHOW RESULTS IMMEDIATELY AS THEY ARRIVE
                if color == "red":
                    st.error(f"🔴 **{item}** ({code}) — {lane}: {advice}")
                elif color == "orange":
                    st.warning(f"🟡 **{item}** ({code}) — {lane}: {advice}")
                else:
                    st.success(f"🟢 **{item}** ({code}) — {lane}: {advice}")
                
                audit_data.append({"Product": item, "Code": code, "Lane": lane, "Action": advice})
                
            except Exception as e:
                st.error(f"❌ Error checking {item}: {str(e)}")

        # 6. FINAL SUMMARY TABLE
        if audit_data:
            st.divider()
            st.subheader("📋 Shipment Audit Summary")
            df_final = pd.DataFrame(audit_data)
            st.table(df_final)
            
            # Download Link
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Official CSV Audit", csv_file, "audit.csv", "text/csv")

        # Remove the progress bar when finished
        my_bar.empty()
