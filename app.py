import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Reset Memory on Start
if 'results' not in st.session_state:
    st.session_state.results = None

# 3. Logo Styling
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

# 5. Sidebar Resources
with st.sidebar:
    st.header("🛡️ Resources")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.write("**TSS Support:** 0800 060 8888")
    st.write("**DAERA NI:** 0300 200 7840")

# 6. Input Handling
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df_csv = pd.read_csv(file)
        final_list = df_csv.iloc[:, 0].dropna().tolist()

# 7. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.sidebar.warning("⚠️ No data found to analyze.")
    else:
        # This forces the spinner to show up immediately
        with st.spinner('🎡 Spinning the compliance wheel... checking HMRC...'):
            temp_results = []
            for item in final_list:
                # Basic code lookup
                manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
                code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
                
                if not code: continue

                try:
                    # Fresh API Request
                    url = f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}"
                    res = requests.get(url, timeout=10)
                    
                    lane, advice, color = "Green Lane", "UKIMS Only", "green"
                    
                    if res.status_code == 200:
                        raw = res.text.lower()
                        if code[:2] in ['72', '73']: lane, advice, color = "Category 1 (Red)", "Full Customs Dec", "red"
                        elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                            lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert Required", "orange"
                    
                    temp_results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice, "color": color})
                except:
                    temp_results.append({"Product": item, "Code": code, "Lane": "Error", "Advice": "Connection Issue", "color": "gray"})
            
            # Save results to memory
            st.session_state.results = temp_results

# 8. RESULTS DISPLAY (Drawn outside the button)
if st.session_state.results:
    st.success("🎰 The wheel has stopped!")
    st.divider()
    
    # Show Cards
    for r in st.session_state.results:
        with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"🔴 {r['Advice']}")
            elif r['color'] == 'orange': st.warning(f"🟡 {r['Advice']}")
            else: st.success(f"🟢 {r['Advice']}")

    # Show Final Audit Table
    st.divider()
    st.subheader("📋 Audit Summary")
    df_final = pd.DataFrame(st.session_state.results).drop(columns=['color'])
    st.table(df_final)
    
    # Download Link
    csv_bytes = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Official Audit", csv_bytes, "audit.csv", "text/csv")
