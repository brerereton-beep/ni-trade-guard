import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz 

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header
st.markdown("<h1 style='text-align: center;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)

# 3. Sidebar
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
    raw_text = st.sidebar.text_area("List Products:", "lamb\nbeef\n7210")
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
        with st.spinner('🎡 Spinning the wheel... checking Chapter Ranges and HMRC rules...'):
            # Timezone Setup
            try:
                tz = pytz.timezone('Europe/London')
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            except:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            for item in final_list:
                item_str = str(item).lower()
                # Extract first 2 digits (The Chapter)
                digits = ''.join(filter(str.isdigit, item_str))
                chapter = digits[:2] if len(digits) >= 2 else ""
                
                # Default Setup
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                # --- RULE 1: CATEGORY 1 (RED) - INDUSTRIAL CONTROLS ---
                if chapter in ["72", "73", "76", "28", "29"] or any(x in item_str for x in ["steel", "aluminum", "iron", "chemical"]):
                    lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                
                # --- RULE 2: CATEGORY 2 (ORANGE) - SPS / VETERINARY ---
                # Added lamb, mutton, venison, poultry, and specific meat chapters
                sps_chapters = ["01", "02", "03", "04", "05", "07", "08", "09", "10", "12", "16"]
                sps_keywords = [
                    "beef", "pork", "chicken", "lamb", "mutton", "venison", "poultry", 
                    "meat", "cheese", "dairy", "fish", "prawn", "seafood", "milk", 
                    "fruit", "veg", "sausage", "bacon", "ham"
                ]
                
                if chapter in sps_chapters or any(x in item_str for x in sps_keywords):
                    lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED-P) + 'Not for EU' Label", "orange"

                # --- RULE 3: EXCISE (ORANGE) ---
                elif chapter == "22" or "alcohol" in item_str:
                    lane, advice, color = "Category 2 (Orange)", "Excise Controls: Duty & Movement rules apply", "orange"

                # --- RULE 4: API SEARCH (The Safety Net) ---
                elif digits:
                    try:
                        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{digits[:4]}", timeout=5)
                        if res.status_code == 200:
                            raw = res.text.lower()
                            if any(term in raw for term in ["veterinary", "animal health", "sanitary"]):
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
            
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Official Audit Report",
                data=csv_file,
                file_name=f"NI_Audit_{timestamp.replace(' ','_').replace(':','')}.csv",
                mime="text/csv"
            )
