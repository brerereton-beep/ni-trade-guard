import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header Animation (CSS)
st.markdown("""
    <style>
        .header-unit { text-align: center; margin-bottom: 20px; }
        .logo-box { position: relative; width: 60px; height: 60px; margin: 0 auto 10px auto; }
        .logo-item { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; font-size: 50px; text-align: center; animation: logoCycle 9s infinite; }
        .logo-item:nth-child(1) { animation-delay: 0s; } 
        .logo-item:nth-child(2) { animation-delay: 3s; } 
        .logo-item:nth-child(3) { animation-delay: 6s; }
        @keyframes logoCycle { 0% { opacity: 0; } 10% { opacity: 1; } 30% { opacity: 1; } 40% { opacity: 0; } 100% { opacity: 0; } }
        .clean-title { font-size: 2rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Resources
with st.sidebar:
    st.header("🛡️ Resources")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.write("**TSS Support:** 0800 060 8888")
    st.write("**DAERA NI:** 0300 200 7840")

# 4. Header Display
st.markdown("""<div class="header-unit"><div class="logo-box"><div class="logo-item">🛳️</div><div class="logo-item">✈️</div><div class="logo-item">🚛</div></div><div class="clean-title">NI Trade Guard Pro</div></div>""", unsafe_allow_html=True)

# 5. Get the Items
items_to_process = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw_text:
        items_to_process = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df_csv = pd.read_csv(file)
        items_to_process = df_csv.iloc[:, 0].dropna().tolist()

# 6. THE STAGE (This prevents the blank screen)
results_area = st.empty() # This is the placeholder that stays open
audit_area = st.empty()

# 7. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not items_to_process:
        st.sidebar.error("⚠️ No data detected.")
    else:
        all_results = []
        
        # Open the stage
        with results_area.container():
            st.info("🎡 The wheel is spinning... results will appear below as they are verified.")
            
            for item in items_to_process:
                # Logic
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
                    
                    # Store Result
                    res_obj = {"Product": item, "Code": code, "Lane": lane, "Advice": advice, "color": color}
                    all_results.append(res_obj)

                    # PAINT THE CARD IMMEDIATELY
                    if color == 'red': st.error(f"🚨 **{item}** — {lane}: {advice}")
                    elif color == 'orange': st.warning(f"⚠️ **{item}** — {lane}: {advice}")
                    else: st.success(f"✅ **{item}** — {lane}: {advice}")

                except:
                    st.error(f"❌ Connection error for {item}")

        # 8. THE FINAL AUDIT (This paints once the loop finishes)
        if all_results:
            with audit_area.container():
                st.divider()
                st.subheader("📋 Shipment Audit Report")
                df_out = pd.DataFrame(all_results).drop(columns=['color'])
                st.table(df_out)
                
                csv = df_out.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Official Audit", csv, "ni_audit.csv", "text/csv")
