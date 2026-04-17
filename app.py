import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# --- 1. DYNAMIC ANIMATED LOGO & STYLING ---
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        
        /* The Title with Flexbox to align logo and text */
        .main-title { 
            font-size: 3rem; 
            font-weight: 700; 
            display: flex; 
            align-items: center; 
            gap: 20px;
        }

        /* The Animation Container */
        .logo-container { 
            position: relative; 
            width: 70px; 
            height: 70px; 
        }

        /* Individual Icons */
        .logo-icon { 
            position: absolute; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            opacity: 0; 
            font-size: 55px; 
            text-align: center;
            animation: logoFade 9s infinite; 
        }

        /* Timing: 3 seconds each (Ship -> Plane -> Truck) */
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
    </style>
""", unsafe_allow_html=True)

# Render the Animated Header
st.markdown("""
    <div class="main-title">
        <div class="logo-container">
            <div class="logo-icon">🛳️</div>
            <div class="logo-icon">✈️</div>
            <div class="logo-icon">🚛</div>
        </div>
        <span>NI Trade Guard Pro</span>
    </div>
    <p style="color: gray; font-size: 1.2rem; margin-top: -10px; margin-bottom: 25px;">
        Windsor Framework Compliance Dashboard
    </p>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Control Panel")
    input_method = st.radio("Choose Input Method:", ["Manual Entry", "Bulk CSV Upload"])
    st.divider()
    
    # PDF Button
    st.subheader("Reporting")
    print_btn = """
        <button onclick="window.print()" style="width:100%; border-radius:8px; background-color:#FF4B4B; color:white; border:none; padding:12px; font-weight:bold; cursor:pointer;">
        📄 Save Report as PDF
        </button>
    """
    components.html(print_btn, height=60)
    st.info("💡 Pro Tip: Tap the PDF button to generate an audit for your manifest.")

# --- 3. INPUT LOGIC ---
items = []
if input_method == "Manual Entry":
    user_input = st.sidebar.text_area("List products/codes (one per line):", "beef\n0203\n7210\ncheese")
    items = [i.strip() for i in user_input.split('\n') if i.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        items = df_upload.iloc[:, 0].tolist()

# --- 4. COMPLIANCE ENGINE ---
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    for item in items:
        # Dictionary for text mapping
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        
        if not code: continue

        try:
            # Query the XI (Northern Ireland) Tariff API
            res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=5)
            lane, action, color = "Green Lane", "UKIMS Only", "green"
            
            if res.status_code == 200:
                raw_data = str(res.json()).lower()
                # Category 1: Steel/Heavy Industrial
                if code[:2] in ['72', '73']:
                    lane, action, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                # Category 2: Food/Retail (NIRMS)
                elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw_data:
                    lane, action, color = "Category 2 (Retail)", "NIRMS: 'Not for EU' Label + Health Cert", "orange"

            results.append({"Product": item, "Code": code, "Lane": lane, "Action": action, "color": color})
        except:
            results.append({"Product": item, "Code": code, "Lane": "Error", "Action": "API Timeout", "color": "gray"})

    # --- 5. RESULTS DISPLAY ---
    st.divider()
    for r in results:
        with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"🔴 **Decision:** {r['Action']}")
            elif r['color'] == 'orange': st.warning(f"🟡 **Decision:** {r['Action']}")
            else: st.success(f"🟢 **Decision:** {r['Action']}")

    # --- 6. AUDIT TABLE ---
    st.divider()
    st.subheader("📋 Official Shipment Audit Report")
    df_results = pd.DataFrame(results).drop(columns=['color'])
    st.dataframe(df_results, use_container_width=True, hide_index=True)
