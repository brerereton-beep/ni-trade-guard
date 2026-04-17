import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Memory Initialization
if 'results' not in st.session_state:
    st.session_state.results = None

# 3. Logo & Styling
st.markdown("""
    <style>
        .header-unit { text-align: center; margin-bottom: 20px; }
        .logo-box { position: relative; width: 70px; height: 70px; margin: 0 auto 10px auto; }
        .logo-item { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; font-size: 55px; text-align: center; animation: logoCycle 9s infinite; }
        .logo-item:nth-child(1) { animation-delay: 0s; } 
        .logo-item:nth-child(2) { animation-delay: 3s; } 
        .logo-item:nth-child(3) { animation-delay: 6s; }
        @keyframes logoCycle { 0% { opacity: 0; } 10% { opacity: 1; } 30% { opacity: 1; } 40% { opacity: 0; } 100% { opacity: 0; } }
        .clean-title { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# 4. Header
st.markdown("""<div class="header-unit"><div class="logo-box"><div class="logo-item">🛳️</div><div class="logo-item">✈️</div><div class="logo-item">🚛</div></div><div class="clean-title">NI Trade Guard Pro</div></div>""", unsafe_allow_html=True)

# 5. Sidebar Resources
with st.sidebar:
    st.header("🛡️ Resources")
    mode = st.radio("Mode:", ["Manual Entry", "Bulk CSV"])
    st.divider()
    st.write("**TSS:** 0800 060 8888")
    st.write("**DAERA:** 0300 200 7840")

# 6. Data Input Handling
items_to_check = []
if mode == "Manual Entry":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    items_to_check = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    f = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if f:
        df_in = pd.read_csv(f)
        items_to_check = df_in.iloc[:, 0].tolist()

# 7. THE ENGINE (The Fixed Logic)
if st.sidebar.button("🚀 Run Compliance Check"):
    if not items_to_check:
        st.sidebar.error("⚠️ No items found to analyze.")
    else:
        # Clear old results first
        st.session_state.results = []
        
        with st.spinner('🎡 Spinning the compliance wheel...'):
            temp_results = []
            for item in items_to_check:
                # Mapping
                manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
                code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
                
                if not code: continue

                try:
                    res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=10)
                    lane, advice, color = "Green Lane", "UKIMS Only", "green"
                    
                    if res.status_code == 200:
                        raw = res.text.lower()
                        if code[:2] in ['72', '73']: lane, advice, color = "Category 1 (Red)", "Full Customs Dec", "red"
                        elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                            lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert", "orange"
                    
                    temp_results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice, "color": color})
                except:
                    temp_results.append({"Product": item, "Code": code, "Lane": "Error", "Advice": "Connection Timeout", "color": "gray"})
            
            # Save to permanent memory
            st.session_state.results = temp_results

# 8. THE DISPLAY (Always looks at memory)
if st.session_state.results:
    st.success("🎰 The wheel has stopped!")
    st.divider()
    
    for r in st.session_state.results:
        with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"🔴 {r['Advice']}")
            elif r['color'] == 'orange': st.warning(f"🟡 {r['Advice']}")
            else: st.success(f"🟢 {r['Advice']}")

    st.divider()
    st.subheader("📋 Audit Summary")
    df_out = pd.DataFrame(st.session_state.results).drop(columns=['color'])
    st.table(df_out)
    
    csv = df_out.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Audit Report", csv, "ni_trade_audit.csv", "text/csv")
