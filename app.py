import streamlit as st
import requests
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="NI Trade Guard Pro", page_icon="🛡️", layout="wide")

# 2. Header
st.markdown("<h1 style='text-align: center;'>🛡️ NI Trade Guard Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Official Compliance Decision Support</p>", unsafe_allow_html=True)

# 3. Sidebar Resources
with st.sidebar:
    st.header("Shipment Input")
    mode = st.radio("Input Mode:", ["Manual", "Bulk CSV"])
    st.divider()
    st.subheader("📞 Helplines")
    st.write("TSS: 0800 060 8888")
    st.write("DAERA: 0300 200 7840")

# 4. Input Handling
final_list = []
if mode == "Manual":
    raw_text = st.sidebar.text_area("List Products:", "beef\n0203\n7210")
    if raw_text:
        final_list = [i.strip() for i in raw_text.split('\n') if i.strip()]
else:
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        # This grabs the first column regardless of the header name
        final_list = df.iloc[:, 0].dropna().tolist()

# 5. THE ENGINE
if st.sidebar.button("🚀 Run Compliance Check"):
    if not final_list:
        st.error("⚠️ No items found. Please check your input or CSV file.")
    else:
        results = []
        
        # THE THROBBER (Spinner)
        with st.spinner('🔍 Analyzing manifest items... please wait...'):
            for item in final_list:
                # Logic: We use a very broad search so it doesn't fail
                item_str = str(item).lower()
                manual_map = {"beef":"0201", "cheese":"0406", "pork":"0203", "chicken":"0207", "steel":"7210"}
                
                # Try to find a code: 1. Map name to code, 2. Look for digits in string, 3. Use the name itself
                code = manual_map.get(item_str) or ''.join(filter(str.isdigit, item_str)) or item_str[:4]
                
                try:
                    # Fresh API Request to HMRC (XI Tariff)
                    res = requests.get(f"https://www.trade-tariff.service.gov.uk/xi/api/v2/headings/{code[:4]}", timeout=10)
                    lane, advice, color = "Green Lane", "UKIMS Only", "green"
                    
                    if res.status_code == 200:
                        raw_body = res.text.lower()
                        if "72" in code[:2] or "73" in code[:2]:
                            lane, advice, color = "Category 1 (Red)", "Full Customs Declaration Required", "red"
                        elif any(x in code[:2] for x in ['01','02','03','04','05']) or "veterinary" in raw_body:
                            lane, advice, color = "Category 2 (Orange)", "NIRMS: Health Cert + 'Not for EU' Label", "orange"

                    results.append({"Product": item, "Lane": lane, "Action": advice, "color": color})
                except:
                    results.append({"Product": item, "Lane": "Error", "Action": "API Timeout", "color": "gray"})

        # 6. DISPLAY RESULTS
        st.divider()
        for r in results:
            with st.expander(f"{r['Product']} — {r['Lane']}", expanded=True):
                if r['color'] == 'red': st.error(f"🔴 **Action:** {r['Action']}")
                elif r['color'] == 'orange': st.warning(f"🟡 **Action:** {r['Action']}")
                else: st.success(f"🟢 **Action:** {r['Action']}")

        if results:
            st.divider()
            st.subheader("📋 Shipment Audit Summary")
            df_final = pd.DataFrame(results).drop(columns=['color'])
            st.table(df_final)
            
            # Download Link
            csv_file = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Official Audit", csv_file, "audit.csv", "text/csv")
