import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="NI Trade Guard", page_icon="🛡️")

# --- 1. BRANDING: CUSTOM LOGO ---
# You can replace this URL with a link to your own logo later!
st.logo("https://www.freeiconspng.com/uploads/shield-icon-26.png")
st.title("🛡️ NI Trade Guard Pro")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Control Panel")
    input_method = st.radio("Choose Input Method:", ["Manual Entry", "Bulk CSV Upload"])
    st.divider()
    
    # PDF PRINT BUTTON (Hidden in Sidebar)
    st.subheader("Reporting")
    print_btn = """
        <button onclick="window.print()" style="width:100%; border-radius:5px; background-color:#FF4B4B; color:white; border:none; padding:10px;">
        📄 Save Report as PDF
        </button>
    """
    components.html(print_btn, height=50)

# --- INPUT LOGIC ---
items = []
if input_method == "Manual Entry":
    user_input = st.sidebar.text_area("List products/codes:", "beef\n0203\n7210")
    items = [i.strip() for i in user_input.split('\n') if i.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        items = df_upload.iloc[:, 0].tolist()

# --- THE ENGINE ---
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    for item in items:
        # Dictionary for text-to-code
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207"}
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        if not code: continue

        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}")
        lane, action, color = "Green Lane", "UKIMS Only", "green"
        
        if res.status_code == 200:
            raw = str(res.json()).lower()
            # Category 1: Steel/Industrial
            if code[:2] in ['72', '73']:
                lane, action, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
            # Category 2: NIRMS (Food/Retail)
            elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                lane, action, color = "Category 2 (Retail)", "NIRMS: General Certificate + 'Not for EU' Label", "orange"

        results.append({"Product": item, "Lane": lane, "Action": action, "color": color})

    # --- RESULTS DISPLAY ---
    for r in results:
        with st.expander(f"{r['Product']} - {r['Lane']}", expanded=True):
            if r['color'] == 'red': st.error(f"**Action:** {r['Action']}")
            elif r['color'] == 'orange': st.warning(f"**Action:** {r['Action']}")
            else: st.success(f"**Action:** {r['Action']}")
            
            # Specific Advice
            if "NIRMS" in r['Action']:
                st.info("💡 **Requirement:** Seal must be recorded on the CHED and General Certificate.")

    # Audit Table for PDF
    st.markdown("### Official Shipment Audit")
    st.table(pd.DataFrame(results).drop(columns=['color']))
