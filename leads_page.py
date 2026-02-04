import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. DATA CLEANER ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_searchapi(query, pin, api_key, target_source):
    url = "https://www.searchapi.io/api/v1/search"
    is_maps = (target_source == "Google Maps")
    
    # We use 'google_maps' engine for Maps and 'google' for Search
    params = {
        "engine": "google_maps" if is_maps else "google",
        "q": f"{query} {pin} India",
        "api_key": api_key,
        "gl": "in",
        "hl": "en"
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        
        # DEBUG: Let's see if the API actually sent something
        if "error" in data:
            st.error(f"API Error: {data['error']}")
            return []

        # UNIVERSAL FINDER: Look in all possible result folders
        results = data.get('places', []) or \
                  data.get('organic_results', []) or \
                  data.get('local_results', [])
        
        return results
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- 2. UI ---
st.title("🎯 Nuera Universal Sniper")

with st.sidebar:
    st.header("⚙️ Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Dentist"))
    pin_input = st.text_area("PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])
    start_btn = st.button("🚀 Start Sniper Scan")

if start_btn:
    pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    all_leads = []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 Sniping PIN: {pin}...")
        raw_items = fetch_searchapi(industry, pin, api_key_val, target_src)
        
        for item in raw_items:
            # SearchAPI uses different names for Phone and Website
            name = item.get('title', 'Unknown')
            # Look for phone in multiple possible fields
            phone_raw = item.get('phone') or item.get('phone_number')
            site = item.get('website') or item.get('link', 'Not Available')
            address = item.get('address', item.get('snippet', ''))

            if phone_raw:
                clean_phone = re.sub(r'\D', '', str(phone_raw))[-10:]
                all_leads.append({
                    "PIN Code": pin,
                    "Business Name": name,
                    "Phone": clean_phone,
                    "Email": extract_email(str(item)),
                    "Website": site,
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1)

    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        st.success(f"✅ Found {len(df)} Leads!")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("❌ No results found. Try switching 'Google Maps' to 'Google Search' or use a different keyword.")
