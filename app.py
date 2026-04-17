import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz 

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header & Styling
st.markdown("<h1 style='text-align: center;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Windsor Framework Compliance Decision Support</p>", unsafe_allow_html=True)

# 3. Sidebar Configuration
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Compliance Helplines")
    st.write("**TSS:** 0800 060 8888")
    st.write("**DAERA:** 0300 200 7840")

# 4. Input Handling
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products (one per line):", "beef\npallets\nsensor\nlasagna")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        # Automatically targets the first column for item descriptions
        final_list = df.iloc[:, 0].dropna().tolist()

# 5. THE ENGINE (The Brain of the App)
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.error("⚠️ No items found. Please provide product descriptions or codes.")
    else:
        results = []
        with st.spinner('Analyzing manifest against XI/UK Tariff Rules...'):
            # Set Timezone to Belfast/London
            try:
                tz = pytz.timezone('Europe/London')
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            except:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            for item in final_list:
                # Clean the input to prevent hidden space errors
                item_str = str(item).lower().strip()
                digits = ''.join(filter(str.isdigit, item_str))
                chapter = digits[:2] if len(digits) >= 2 else ""
                
                # Default Lane
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                # --- CATEGORY 1: RED LANE (INDUSTRIAL/DUAL-USE) ---
                red_chapters = ["72", "73", "76", "28", "29", "84", "85", "90"]
                red_keywords = ["steel", "aluminum", "iron", "chemical", "precision", "sensor", "drone", "military", "ballistic"]
                
                # --- CATEGORY 2: ORANGE LANE (SPS/COMPOSITE/EXCISE) ---
                orange_chapters = ["01", "02", "03", "04", "05", "07", "08", "09", "10", "12", "16", "19", "21", "44"]
                orange_keywords = [
                    "beef", "pork", "chicken", "lamb", "mutton", "venison", "poultry", "meat", 
                    "cheese", "dairy", "fish", "prawn", "seafood", "milk", "fruit", "veg", 
                    "sausage", "bacon", "ham", "pizza", "lasagna", "ready meal", "pasta", 
                    "timber", "wood", "logs", "plant", "flower", "pallet", "crate", "box"
                ]

                # --- THE LOGIC GATE ---
                # 1. Check RED first (Highest Priority)
                if chapter in red_chapters or any(x in item_str for x in red_keywords):
                    lane, advice, color = "Category 1 (Red)", "Full Customs Declaration / License Required", "red"
                
                # 2. Check ORANGE (SPS & Packaging)
                elif chapter in orange_chapters or any(x in item_str for x in orange_keywords):
                    lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED) + Labeling", "orange"

                # 3. Check EXCISE
                elif chapter == "22" or "alcohol" in item_str:
                    lane, advice, color = "Category 2 (Orange)", "Excise Controls: Duty rules apply", "orange"

                # 4. API SEARCH (HMRC/XI Safety Net)
                elif digits:
                    try:
                        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{digits[:4]}", timeout=5)
                        if res.status_code == 200:
                            raw = res.text.lower()
                            if any(term in raw for term in ["veterinary", "animal health", "sanitary", "phytosanitary"]):
                                lane, advice, color = "Category 2 (Orange)", "NIRMS Required (API Detected)", "orange"
                    except:
                        pass

                results.append({
                    "Date Verified": timestamp,
                    "Product": item, 
                    "Lane": lane, 
                    "Action": advice, 
                    "color": color
                })

        # 6. RESULTS DISPLAY
        st.divider()
        for r in results:
            with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
                if r['color'] == 'red': st.error(f"🔴 **Action Required:** {r['Action']}")
                elif r['color'] == 'orange': st.warning(f"🟡 **Action Required:** {r['Action']}")
                else: st.success(f"🟢 **Action:** {r['Action']}")

        # 7. AUDIT SUMMARY & DOWNLOAD
        if results:
            st.divider()
            st.subheader("📋 Shipment Audit Summary")
            df_final = pd.DataFrame(results).drop(columns=['color'])
            st.table(df_final)
            
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Official Audit Report (CSV)",
                data=csv_file,
                file_name=f"NI_Audit_{timestamp.replace(' ','_').replace(':','')}.csv",
                mime="text/csv"
            )
