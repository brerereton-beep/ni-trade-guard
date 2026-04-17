import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="NI Trade Guard", page_icon="🛡️")
st.title("🛡️ NI Trade Guard Pro")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Control Panel")
    # This creates the toggle you were looking for
    input_method = st.radio("Choose Input Method:", ["Manual Entry", "Bulk CSV Upload"])
    st.divider()

# --- INPUT LOGIC ---
items = []
if input_method == "Manual Entry":
    user_input = st.sidebar.text_area("List products/codes:", "beef\ncheese\n7210")
    items = [i.strip() for i in user_input.split('\n') if i.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload Shipment CSV", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        # We take the first column of the CSV
        items = df_upload.iloc[:, 0].tolist()
    else:
        st.info("Please upload a CSV file in the sidebar.")

# --- RUN BUTTON & ANALYSIS ---
if st.sidebar.button("🚀 Run Compliance Check") and items:
    results = []
    for item in items:
        # Dictionary for text-to-code
        manual = {"beef":"0201", "cheese":"0406", "pork":"0203", "fish":"0302", "steel":"7210"}
        code = manual.get(str(item).lower()) or ''.join(filter(str.isdigit, str(item)))
        
        if not code: continue

        res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}")
        lane, action, color = "Green Lane", "UKIMS Only", "green"
        
        if res.status_code == 200:
            raw = str(res.json()).lower()
            if code[:2] in ['72', '73']:
                lane, action, color = "Category 1 (Red)", "Full Dec Required", "red"
            elif code[:2] in ['01','02','03','04','05'] or "veterinary" in raw:
                lane, action, color = "Category 2 (Retail)", "NIRMS: 'Not for EU' Label", "orange"

        results.append({"Product": item, "Lane": lane, "Action": action, "color": color})

    # --- DISPLAY RESULTS ---
    for r in results:
        if r['color'] == 'red': st.error(f"🔴 {r['Product']}: {r['Lane']} — {r['Action']}")
        elif r['color'] == 'orange': st.warning(f"🟡 {r['Product']}: {r['Lane']} — {r['Action']}")
        else: st.success(f"🟢 {r['Product']}: {r['Lane']} — {r['Action']}")
    
    # Audit Table
    st.divider()
    st.dataframe(pd.DataFrame(results).drop(columns=['color']), use_container_width=True)