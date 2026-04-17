import streamlit as st
import requests
import pandas as pd
import time

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Reset Memory
if 'results' not in st.session_state:
    st.session_state.results = []

# 3. Logo & Styling
st.markdown("""
    <style>
        .header-unit { text-align: center; margin-bottom: 20px; }
        .logo-box { position: relative; width: 60px; height: 60px; margin: 0 auto 10px auto; }
        .logo-item { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; font-size: 50px; text-align: center; animation: logoCycle 9s infinite; }
        .logo-item:nth-child(1) { animation-delay: 0s; } 
        .logo-item:nth-child(2) { animation-delay: 3s; } 
        .logo-item:nth-child(3) { animation-delay: 6s; }
        @keyframes logoCycle { 0% { opacity: 0; } 10% { opacity: 1; } 30% { opacity: 1; } 40% { opacity: 0; } 100% { opacity: 0; } }
        .clean-title { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# 4. Header
st.markdown("""<div class="header-unit"><div class="logo-box"><div class="logo-item">🛳️</div><div class="logo-item">✈️</div><div class="logo-item">🚛</div></div><div class="clean-title">NI Trade Guard Pro</div></div>""", unsafe_allow_html=True)

# 5. Sidebar
with st.sidebar:
    st.header("🛡️ Resources")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    if st.button("🗑️ Clear All Results"):
        st.session_state.results = []
        st.rerun()

# 6. Input Logic
input_list = []
if mode == "Manual":
    raw = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw: input_list = [i.strip() for i in raw.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df_in = pd.read_csv(file)
        input_list = df_in.iloc[:, 0].dropna().tolist()

# 7. THE ENGINE (Now with Live Progress)
if st.sidebar.button("🚀 Run Compliance Check"):
    if not input_list:
        st.sidebar.warning("No data to check.")
    else:
        # 1. Start the Throbber
        with st.status("🎡 Spinning the wheel... checking HMRC servers...", expanded=True) as status:
            temp_results = []
            progress_bar = st.progress(0)
            
            for index, item in enumerate(input_list):
                # Calculate progress
                pct = (index + 1) / len(input_list)
                progress_bar.progress(pct)
                
                # Code mapping
                manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
                code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
                
                if not code: continue

                try:
                    res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=15)
                    lane, advice, color = "Green Lane", "UKIMS Only", "green"
                    if res.status_code == 200:
                        raw = res.text.lower()
                        if code[:2] in ['72', '73']: lane, advice, color = "Category 1 (Red)", "Full Customs Dec", "red"
                        elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                            lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert Required", "orange"
                    
                    temp_results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice, "color": color})
                except:
                    temp_results.append({"Product": item, "Code": code, "Lane": "Error", "Advice": "HMRC Server Timeout", "color": "gray"})
            
            # 2. Finish
            st.session_state.results = temp_results
            status.update(label="🎰 Wheel stopped! Results ready.", state="complete", expanded=False)

# 8. RESULTS DISPLAY
if st.session_state.results:
    st.divider()
    # Cards
    for r in st.session_state.results:
        with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"🔴 {r['Advice']}")
            elif r['color'] == 'orange': st.warning(f"🟡 {r['Advice']}")
            else: st.success(f"🟢 {r['Advice']}")

    # Table
    st.divider()
    st.subheader("📋 Audit Summary")
    df_final = pd.DataFrame(st.session_state.results).drop(columns=['color'])
    st.table(df_final)
    
    # Download
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Official Audit", csv, "audit.csv", "text/csv")
