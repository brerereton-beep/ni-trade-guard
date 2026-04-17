import streamlit as st
import requests
import pandas as pd
import time

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Styling (Centered Header & Animation)
st.markdown("""
    <style>
        .header-unit { text-align: center; padding: 10px; margin-bottom: 20px; }
        .logo-box { position: relative; width: 70px; height: 70px; margin: 0 auto 15px auto; }
        .logo-item { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; font-size: 55px; text-align: center; animation: logoCycle 9s infinite; }
        .logo-item:nth-child(1) { animation-delay: 0s; } 
        .logo-item:nth-child(2) { animation-delay: 3s; } 
        .logo-item:nth-child(3) { animation-delay: 6s; }
        @keyframes logoCycle {
            0% { opacity: 0; transform: translateY(10px); }
            10% { opacity: 1; transform: translateY(0); }
            30% { opacity: 1; }
            40% { opacity: 0; transform: translateY(-10px); }
            100% { opacity: 0; }
        }
        .clean-title { font-size: 1.8rem; font-weight: 800; letter-spacing: -1px; }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar with REAL Contacts
with st.sidebar:
    st.markdown("<div style='text-align: center;'><h1>🛡️ Resources</h1></div>", unsafe_allow_html=True)
    mode = st.radio("Mode:", ["Manual Entry", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Official Helplines")
    st.markdown("**Trader Support (TSS):** 0800 060 8888\n\n**DAERA:** 0300 200 7840\n\n**NIRMS:** 0300 020 0301")

# 4. Header
st.markdown("""
    <div class="header-unit">
        <div class="logo-box">
            <div class="logo-item">🛳️</div>
            <div class="logo-item">✈️</div>
            <div class="logo-item">🚛</div>
        </div>
        <div class="clean-title">NI Trade Guard Pro</div>
        <div style="color: gray;">Windsor Framework Decision Support</div>
    </div>
""", unsafe_allow_html=True)

# 5. Input Logic
items = []
if mode == "Manual Entry":
    txt = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    items = [i.strip() for i in txt.split('\n') if i.strip()]
else:
    f = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if f: items = pd.read_csv(f).iloc[:, 0].tolist()

# 6. Compliance Engine with "Quirky Spinning Wheel"
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    
    # Custom Spinner Text
    with st.spinner('🎡 Spinning the compliance wheel... hang tight...'):
        for item in items:
            manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
            code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
            if not code: continue

            try:
                res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=10)
                lane, advice, color = "Green Lane", "UKIMS Only", "green"
                
                if res.status_code == 200:
                    raw = str(res.json()).lower()
                    if code[:2] in ['72', '73']: lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                    elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                        lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED-P) + 'Not for EU' Labels", "orange"

                results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice, "color": color})
            except:
                results.append({"Product": item, "Code": code, "Lane": "Error", "Advice": "API Timeout", "color": "gray"})

    # 7. Final Results
    st.success("🎰 The wheel has stopped! Results below.")
    st.divider()
    
    for r in results:
        with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"🚨 **Action:** {r['Advice']}")
            elif r['color'] == 'orange':
                st.warning(f"⚠️ **Action:** {r['Advice']}")
                st.info("💡 **Haulier Rule:** Seal must be recorded on the General Certificate.")
            else: st.success(f"✅ **Action:** {r['Advice']}")

    if results:
        st.divider()
        st.subheader("📋 Audit Summary")
        df_audit = pd.DataFrame(results).drop(columns=['color'])
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
        
        csv_data = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Audit Report", data=csv_data, file_name='ni_trade_audit.csv', mime='text/csv')
