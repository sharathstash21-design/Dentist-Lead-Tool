import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. DATA HUNTER ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_by_pin(query, pin, api_key, target_source):
    """Fetches data for a specific PIN code area."""
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    full_query = f"{query} in {pin}, India"
    
    url = f"https://google.serper.dev/{search_type}"
    payload = json.dumps({"q": full_query, "num": 20})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=20)
        data = response.json()
        return data.get('places' if is_maps else 'organic', [])
    except:
        return []

# --- 2. THE UI ---
st.set_page_config(page_title="Nuera PIN Sniper", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 License Portal")
    code = st.text_input("Enter License Key", type="password")
    if st.button("Unlock"):
        if code == "Salem123":
            st.session_state.auth = True
            st.rerun()
    st.stop()

st.title("🎯 Nuera PIN Code Sniper")
st.markdown("### *Extract leads area-by-area for maximum data volume*")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    industry = st.text_input("Business Type", "Dentist")
    # Example input: 636001, 636007, 636016
    pin_input = st.text_area("Enter PIN Codes (comma separated)", "636001, 636007")
    
    target = st.selectbox("Source", ["Google Maps", "Facebook", "LinkedIn"])
    start_btn = st.button("🚀 Start Sniper Scan")

if start_btn:
    pins = [p.strip() for p in pin_input.split(",")]
    all_leads = []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 **Sniping PIN: {pin} ({idx+1} of {len(pins)})...**")
        
        raw_items = fetch_by_pin(industry, pin, api_key_input, target)
        
        for item in raw_items:
            snippet = item.get('snippet', '') if target != "Google Maps" else item.get('address', '')
            website = item.get('website') if target == "Google Maps" else item.get('link')
            
            # Use 'Not Available' if data is missing
            email = extract_email(snippet)
            phone_raw = item.get('phoneNumber') if target == "Google Maps" else re.search(r'[6-9]\d{9}', snippet)
            
            if phone_raw:
                phone = phone_raw if target == "Google Maps" else phone_raw.group()
                clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                
                all_leads.append({
                    "PIN Code": pin,
                    "Business Name": item.get('title', 'Unknown'),
                    "Phone": clean_phone,
                    "Email": email,
                    "Website": website if website else "Not Available",
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1.5)

    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        st.success(f"✅ Total leads sniped: {len(df)}")
        
        # UI for Sales Opportunity
        missing_web = len(df[df['Website'] == "Not Available"])
        st.warning(f"💡 Sales Opportunity: {missing_web} businesses have no website. Call them!")

        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download Database", df.to_csv(index=False).encode('utf-8'), "pin_leads.csv", "text/csv")
    else:
        st.error("No results found. Check your PIN codes or API key.")

# ... (Top of your file stays the same) ...

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    industry = st.text_input("Business Type", "Dentist")
    
    # DYNAMIC INPUT: Get pins from the Generator if they exist
    ready_pins = st.session_state.get('sniping_pincodes', "636001, 636007")
    pin_input = st.text_area("Enter PIN Codes (comma separated)", value=ready_pins)
    
    # ... (Rest of your scan logic) ...
