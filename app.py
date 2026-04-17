import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Centered & Stacked Logo Styling
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

# 3. Sidebar
with st.sidebar:
    st.markdown("<div style='text-align: center;'><h1>🛡️ Control Panel</h1></div>", unsafe_allow_html=True)
    mode = st.radio("Mode:", ["Manual Entry", "Bulk CSV"])
    st.divider()
    st.markdown("### 📞 Support Desk\n**Phone:** +44 28 XXXX XXXX\n**Email:** support@nitradeguard.com")

# 4. Header
st.markdown("""
    <div class="header-unit">
        <div class="logo-box">
            <div class="logo-item">🛳️</div>
            <div class="logo-item">✈️</div>
            <div class="logo-item">🚛</div>
        </div>
        <div class="clean-title">NI Trade Guard Pro</div>
        <div style="color: gray;">Real-time Windsor Framework Decision Support</div>
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

            # Results Display
            with st.expander(f"{item} — {lane}", expanded=True):
                if color == 'red':
                    st.error(f"🚨 **Action:** {advice}")
                    st.markdown("[View Full Customs Guidance](https://www.gov.uk/import-goods-into-uk)")
                elif color == 'orange':
                    st.warning(f"⚠️ **Action:** {advice}")
                    st.info("💡 **Requirement:** Seal must be recorded on the General Certificate. Not for EU labeling must be applied to retail packaging.")
                    # Direct Help for Hauliers
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.link_button("📜 Download CHED-P Form", "https://www.gov.uk/guidance/import-of-products-animals-food-and-feed-system")
                    with col2:
                        st.link_button("📞 Contact DAERA Support", "https://www.daera-ni.gov.uk/contacts/vets-and-animal-health-contacts")
                else:
                    st.success(f"✅ **Action:** {advice}")
            
            results.append({"Product": item, "Code": code, "Lane": lane, "Advice": advice})
        except:
            st.error(f"Connection error for {item}")

    # 7. Audit & CSV Downloader
    if results:
        st.divider()
        st.subheader("📋 Audit Summary")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Report for Manifest",
            data=csv_data,
            file_name='ni_trade_audit.csv',
            mime='text/csv',
        )
