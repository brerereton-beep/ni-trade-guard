import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Centered & Stacked Logo Styling
st.markdown("""
    <style>
        /* Container to stack logo on top of text */
        .header-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            width: 100%;
            margin-bottom: 20px;
        }

        /* The Animation Box */
        .logo-container { 
            position: relative; 
            width: 80px; 
            height: 80px; 
            margin-bottom: 10px;
        }

        /* Icons */
        .logo-icon { 
            position: absolute; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            opacity: 0; 
            font-size: 60px; 
            animation: logoFade 9s infinite; 
        }

        .logo-icon:nth-child(1) { animation-delay: 0s; } 
        .logo-icon:nth-child(2) { animation-delay: 3s; } 
        .logo-icon:nth-child(3) { animation-delay: 6s; }

        @keyframes logoFade {
            0% { opacity: 0; transform: scale(0.8); }
            10% { opacity: 1; transform: scale(1); }
            30% { opacity: 1; }
            40% { opacity: 0; transform: scale(1.1); }
            100% { opacity: 0; }
        }

        .main-title { 
            font-size: 2.2rem; 
            font-weight: 700; 
            margin: 0;
            line-height: 1.2;
        }
        
        .main-subtitle {
            color: gray;
            font-size: 1rem;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Render Stacked Header
st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            <div class="logo-icon">🛳️</div>
            <div class="logo-icon">✈️</div>
            <div class="logo-icon">🚛</div>
        </div>
        <div class="main-title">NI Trade Guard Pro</div>
        <div class="main-subtitle">Official Compliance & NIRMS Audit Tool</div>
    </div>
""", unsafe_allow_html=True)

# 4. Sidebar Controls
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Mode:", ["Manual Entry", "Bulk CSV"])
    st.divider()

# 5. Input Logic
items = []
if mode == "Manual Entry":
    txt = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    items = [i.strip() for i in txt.split('\n') if i.strip()]
else:
    f = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if f: items = pd.read_csv(f).iloc[:, 0].tolist()

# 6. Compliance Engine
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    st.divider()
    
    for item in items:
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        
        if not code: continue

        try:
            res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=5)
            lane, advice, color = "Green Lane", "UKIMS Only", "green"
            
            if res.status_code == 200:
                raw = str(res.json()).lower()
                if code[:2] in ['72', '73']: 
                    lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                    lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert (CHED-P) + 'Not for EU' Labels", "orange"

            # Results directly under product
            with st.expander(f"{item} — {lane}", expanded=True):
                if color == 'red':
                    st.error(f"🚨 **Action:** {advice}")
                elif color == 'orange':
                    st.warning(f"⚠️ **Action:** {advice}")
                    st.info("💡 **Requirement:** Seal must be recorded on the General Certificate.")
                else:
                    st.success(f"✅ **Action:** {advice}")
            
            results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice})
        except:
            st.error(f"Connection error for {item}")

    # 7. Audit Table & CSV Downloader
    if results:
        st.divider()
        st.subheader("📋 Audit Summary")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Report",
            data=csv_data,
            file_name='ni_trade_audit.csv',
            mime='text/csv',
        )
