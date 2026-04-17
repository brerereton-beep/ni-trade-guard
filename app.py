import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# --- 1. DYNAMIC LOGO SECTION (Fixed and Animated) ---
# This CSS will sit at the very top of the app
st.markdown("""
    <style>
        /* 1. Fix the main title alignment so it doesn't drop down */
        .block-container {
            padding-top: 1rem;
        }
        
        /* 2. Style the main title */
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }
        
        /* 3. Style the subtitle */
        .main-subtitle {
            font-size: 1.2rem;
            color: gray;
            margin-bottom: 2rem;
        }

        /* 4. THE ANIMATED LOGO CSS */
        .logo-container {
            position: relative;
            width: 80px;
            height: 80px;
            margin-right: 20px;
            display: inline-block;
            vertical-align: middle;
        }
        
        .logo-icon {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            animation: logoFade 9s infinite; /* Total cycle: 9 seconds (3s per icon) */
            font-size: 60px; /* Use emojis/icons as logos for simplicity */
            line-height: 80px;
            text-align: center;
        }
        
        /* Define the sequence: Boat -> Plane -> Lorry */
        .logo-icon:nth-child(1) { animation-delay: 0s; } /* Boat 🛳️ */
        .logo-icon:nth-child(2) { animation-delay: 3s; } /* Plane ✈️ */
        .logo-icon:nth-child(3) { animation-delay: 6s; } /* Lorry 🚛 */

        @keyframes logoFade {
            0% { opacity: 0; }
            10% { opacity: 1; }  /* Fade in quick */
            33% { opacity: 1; }  /* Stay visible for 1/3 of the time */
            43% { opacity: 0; }  /* Fade out */
            100% { opacity: 0; }
        }
    </style>
""", unsafe_allow_whitespace=True)

# Render the Title with the Animated Logo
st.markdown(f"""
    <div class="main-title">
        <div class="logo-container">
            <div class="logo-icon">🛳️</div> <div class="logo-icon">✈️</div> <div class="logo-icon">🚛</div> </div>
        <span>NI Trade Guard Pro</span>
    </div>
    <div class="main-subtitle">Windsor Framework Compliance Dashboard</div>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & INPUT CONTROLS ---
with st.sidebar:
    st.header("Control Panel")
    input_method = st.radio("Choose Input Method:", ["Manual Entry", "Bulk CSV Upload"])
    st.divider()
    
    # PDF PRINT BUTTON (Using JavaScript to print the clean audit table)
    st.subheader("Reporting")
    print_btn = """
        <button onclick="window.print()" style="width:100%; border-radius:5px; background-color:#FF4B4B; color:white; border:none; padding:10px; font-weight:bold; cursor:pointer;">
        📄 Save Report as PDF
        </button>
    """
    components.html(print_btn, height=60)
    st.info("💡 Pro Tip: Filter the 'Official Audit' table below before printing to customize your report.")

# --- INPUT LOGIC ---
items = []
if input_method == "Manual Entry":
    user_input = st.sidebar.text_area("List products/codes (one per line):", "beef\n0203\n7210\ncheese\nchicken")
    items = [i.strip() for i in user_input.split('\n') if i.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        # We assume the first column contains the items/codes
        items = df_upload.iloc[:, 0].tolist()

# --- THE ENGINE ---
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    # (The processing logic remains the same for stability)
    for item in items:
        # Dictionary for text-to-code mapping
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "salmon":"0302", "steel":"7210"}
        
        # Convert item to string, lower it, look it up, OR filter for digits (e.g., '0203')
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        
        if not code:
            continue

        try:
            # Query the HMRC Online Tariff API for Northern Ireland (XI) heading
            res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}")
            lane, action, color = "Green Lane", "UKIMS Only", "green"
            
            if res.status_code == 200:
                raw_api_data = str(res.json()).lower()
                
                # Apply categorization rules
                if code[:2] in ['72', '73']:
                    lane, action, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw_api_data:
                    lane, action, color = "Category 2 (Retail)", "NIRMS: 'Not for EU' Label", "orange"

            results.append({"Product": item, "Code": code, "Lane": lane, "Action": action, "color": color})
            
        except requests.exceptions.RequestException:
            results.append({"Product": item, "Code": "API Error", "Lane": "N/A", "Action": "Check connection", "color": "gray"})

    # --- RESULTS DISPLAY ---
    st.divider()
    st.subheader("Analysis Results")
    
    # Use Expanders to show/hide details, keeping the view clean
    for r in results:
        with st.expander(f"[{r['Code']}] {r['Product']} — {r['Lane']}", expanded=True):
            if r['color'] == 'red':
                st.error(f"🔴 **Action Required:** {r['Action']}")
            elif r['color'] == 'orange':
                st.warning(f"🟡 **Action Required:** {r['Action']}")
            elif r['color'] == 'green':
                st.success(f"🟢 **Action Required:** {r['Action']}")
            else:
                st.info(f"⚪ **Action Required:** {r['Action']}")

    # --- THE "PROFESSIONAL FINISH": AUDIT TABLE ---
    # We display a clean, filterable table designed for the PDF report.
    st.divider()
    st.markdown("### 📋 Official Shipment Audit Report")
    
    if results:
        df_results = pd.DataFrame(results)
        # Drop the internal 'color' column before showing the user
        st.dataframe(df_results.drop(columns=['color']), use_container_width=True, hide_index=True)
    else:
        st.info("Run the compliance check to generate the audit report.")
