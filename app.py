import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz  # This is the library that handles timezones

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header
st.markdown("<h1 style='text-align: center;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)

# 3. Sidebar Resources
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Helplines")
    st.write("**TSS:** 0800 060 8888")
    st.write("**DAERA:** 0300 200 7840")

# 4. Input Handling
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        final_list = df.iloc[:, 0].dropna().tolist()

# 5. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.error("⚠️ No items found.")
    else:
        results = []
        with st.spinner('🔍 Verifying shipment compliance...'):
            # --- FIX: Explicitly set to London/Belfast time ---
            tz = pytz.timezone('Europe/London')
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            
            for item in final_list:
                item_str = str(item).lower()
                digits = ''.join(filter(str.isdigit, item_str))
                
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                if any(x in item_str for x in ["steel", "72", "73", "aluminum", "76", "iron"]):
                    lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                elif any(x in item_str for x in ["beef", "pork", "chicken", "meat", "cheese", "dairy", "020", "040", "milk"]):
                    lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED-P) + 'Not for EU' Label", "orange"
                elif digits:
                    try:
                        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{digits[:4]}", timeout=5)
                        if res.status_code == 200 and ("veterinary" in res.text.lower()):
                            lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert Required", "orange"
                    except:
                        pass

                results.append({
                    "Date Verified": timestamp,
                    "Product": item, 
                    "Lane": lane, 
                    "Action": advice, 
                    "color": color
                })

        # 6. DISPLAY RESULTS
        st.divider()
        for r in results:
            with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
                if r['color'] == 'red': st.error(f"🔴 **Action:** {r['Action']}")
                elif r['color'] == 'orange': st.warning(f"🟡 **Action:** {r['Action']}")
                else: st.success(f"🟢 **Action:** {r['Action']}")

        if results:
            st.divider()
            st.subheader("📋 Shipment Audit Summary")
            df_final = pd.DataFrame(results).drop(columns=['color'])
            st.table(df_final)
            
            # Download with Corrected Filename Timestamp
            fn_time = datetime.now(tz).strftime('%Y%m%d_%H%M')
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Official Audit Report",
                data=csv_file,
                file_name=f"NI_Audit_{fn_time}.csv",
                mime="text/csv"
            )
