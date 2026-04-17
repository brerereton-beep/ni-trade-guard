import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# --- 1. THE ULTIMATE PRINT & LOGO STYLE ---
st.markdown("""
    <style>
        /* Logo Animation */
        .main-title { font-size: 2.5rem; font-weight: 700; display: flex; align-items: center; gap: 15px; }
        .logo-container { position: relative; width: 60px; height: 60px; }
        .logo-icon { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; font-size: 50px; text-align: center; animation: logoFade 9s infinite; }
        .logo-icon:nth-child(1) { animation-delay: 0s; } 
        .logo-icon:nth-child(2) { animation-delay: 3s; } 
        .logo-icon:nth-child(3) { animation-delay: 6s; }
        @keyframes logoFade {
            0% { opacity: 0; } 10% { opacity: 1; } 30% { opacity: 1; } 40% { opacity: 0; } 100% { opacity: 0; }
        }

        /* --- THE PRINT FIX --- */
        @media print {
            /* Hide the sidebar, headers, and all buttons */
            header, footer, .stSidebar, .stButton, [data-testid="stHeader"] {
                display: none !important;
            }
            /* Force the main container to be visible */
            .main, .block-container {
                display: block !important;
                visibility: visible !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            /* Style the table for paper */
            table { 
                width: 100% !important; 
                border: 1px solid #000 !important; 
                color: black !important;
            }
            th, td { 
                border: 1px solid #666 !important; 
                padding: 10px !important; 
                background-color: white !important;
                color: black !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-title">
        <div class="logo-container">
            <div class="logo-icon">🛳️</div>
            <div class="logo-icon">✈️</div>
            <div class="logo-icon">🚛</div>
        </div>
        <span>NI Trade Guard Pro</span>
    </div>
    <p style="color: gray; font-size: 1.1rem; margin-top: -10px;">Official Compliance & Audit Report</p>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Controls")
    mode = st.radio("Input:", ["Manual", "Bulk CSV"])
    st.divider()
    # Simple Print Button
    components.html('<button onclick="window.print()" style="width:100%; border-radius:8px; background-color:#FF4B4B; color:white; border:none; padding:12px; font-weight:bold; cursor:pointer;">📄 Generate Audit PDF</button>', height=70)

# Input
items = []
if mode == "Manual":
    txt = st.sidebar.text_area("List Items:", "beef\n0203\n7210")
    items = [i.strip() for i in txt.split('\n') if i.strip()]
else:
    f = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if f: items = pd.read_csv(f).iloc[:, 0].tolist()

# The Run Logic
if st.sidebar.button("🚀 Analyze Shipment") and items:
    results = []
    for item in items:
        # Mini-Dictionary for test
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207"}
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        if not code: continue

        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}")
        lane, advice = "Green Lane", "UKIMS Only"
        
        if res.status_code == 200:
            raw = str(res.json()).lower()
            if code[:2] in ['72', '73']: lane, advice = "Category 1 (Red)", "Full Customs Dec"
            elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                lane, advice = "Category 2 (Orange)", "NIRMS Health Cert"

        results.append({"Product": item, "Code": code, "Result": lane, "Action": advice})

    # Results Expanders
    for r in results:
        with st.expander(f"{r['Product']} — {r['Result']}"):
            st.write(f"**Required Action:** {r['Action']}")

    # --- THE AUDIT TABLE (PDF TARGET) ---
    st.divider()
    st.subheader("📋 Shipment Audit Report")
    # Using the static table again as it's the safest for PDF
    st.table(pd.DataFrame(results))
