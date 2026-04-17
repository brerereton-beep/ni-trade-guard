import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz 

# 1. PAGE CONFIG
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. PASSWORD PROTECTION
def check_password():
    if "password_guessed" not in st.session_state:
        st.session_state["password_guessed"] = False
    if st.session_state["password_guessed"]:
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 Restricted Access</h2>", unsafe_allow_html=True)
    password = st.text_input("Please enter the access code to use NI Trade Guard Pro:", type="password")
    
    if st.button("Unlock System"):
        # UPDATED PASSWORD
        if password == "Ashgreenashgreencarnbeg92??":
            st.session_state["password_guessed"] = True
            st.rerun()
        else:
            st.error("🚫 Incorrect password. Please contact Richard Brereton for access.")
    return False

if not check_password():
    st.stop()

# 3. HEADER & STATUS
st.markdown("<h1 style='text-align: center; color: #0E1117;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)
st.info("💡 **System Status:** Connected to HMRC/XI Live Tariff APIs | Windsor Framework v2.1")

# 4. SIDEBAR
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Compliance Helplines")
    st.write("**TSS:** 0800 060 8888")
    st.write("**DAERA:** 0300 200 7840")

# 5. INPUT HANDLING
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products (one per line):", "beef\npallets\nsensor\nlasagna")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        final_list = df.iloc[:, 0].dropna().tolist()

# 6. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.error("⚠️ No items found.")
    else:
        results = []
        with st.spinner('Analyzing manifest...'):
            try:
                tz = pytz.timezone('Europe/London')
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            except:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            for item in final_list:
                item_str = str(item).lower().strip()
                digits = ''.join(filter(str.isdigit, item_str))
                chapter = digits[:2] if len(digits) >= 2 else ""
                
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                # CATEGORY 1 (RED)
                red_chapters = ["72", "73", "76", "28", "29", "84", "85", "90"]
                red_keywords = ["steel", "aluminum", "iron", "chemical", "precision", "sensor", "drone", "military"]
                
                # CATEGORY 2 (ORANGE)
                orange_chapters = ["01", "02", "03", "04", "05", "07", "08", "09", "10", "12", "16", "19", "21", "44"]
                orange_keywords = ["beef", "pork", "chicken", "lamb", "mutton", "venison", "poultry", "meat", 
                                   "cheese", "dairy", "fish", "prawn", "seafood", "milk", "fruit", "veg", 
                                   "sausage", "bacon", "ham", "pizza", "lasagna", "ready meal", "pasta", 
                                   "timber", "wood", "logs", "plant", "flower", "pallet", "crate", "box"]

                if chapter in red_chapters or any(x in item_str for x in red_keywords):
                    lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                elif chapter in orange_chapters or any(x in item_str for x in orange_keywords):
                    lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED) + Labeling", "orange"
                elif chapter == "22" or "alcohol" in item_str:
                    lane, advice, color = "Category 2 (Orange)", "Excise Controls Apply", "orange"
                elif digits:
                    try:
                        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{digits[:4]}", timeout=5)
                        if any(term in res.text.lower() for term in ["veterinary", "animal health", "sanitary"]):
                            lane, advice, color = "Category 2 (Orange)", "NIRMS Required (API Detected)", "orange"
                    except: pass

                results.append({"Date Verified": timestamp, "Product": item, "Lane": lane, "Action": advice, "color": color})

        # 7. RESULTS DISPLAY
        st.divider()
        for r in results:
            with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
                if r['color'] == 'red': st.error(f"🔴 **Action Required:** {r['Action']}")
                elif r['color'] == 'orange': st.warning(f"🟡 **Action Required:** {r['Action']}")
                else: st.success(f"🟢 **Action:** {r['Action']}")

        if results:
            st.divider()
            df_final = pd.DataFrame(results).drop(columns=['color'])
            st.table(df_final)
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Audit Report", csv_file, f"Audit_{timestamp}.csv", "text/csv")
