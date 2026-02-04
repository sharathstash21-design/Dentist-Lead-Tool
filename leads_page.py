import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- DATA LOGIC ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_by_pin(query, pin, api_key, target_source):
    url = f"https://google.serper.dev/{'maps' if target_source == 'Google Maps' else 'search'}"
    payload = json.dumps({"q": f"{query} in {pin}, India", "num": 20})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=20)
        data = response.json()
        return data.get('places' if target_source == 'Google Maps' else 'organic', [])
    except: return []

# --- UI ---
st.title("🎯 Nuera PIN Code Sniper")

# SHARED BRAIN: Check for data from the Generator
default_cat = st.session_state.get('sniping_category', "Dental Clinic")
default_pins = st.session_state.get('sniping_pincodes', "636001, 636007")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key = st.text_input("API Key", value="7ab11ec8...", type="password", key="api_snip")
    
    # These 'value=' settings make the auto-sync work!
    industry = st.text_input("Business Type", value=default_cat, key="ind_snip")
    pin_input = st.text_area("PIN Codes", value=default_pins, key="pins_snip")
    
    target_src = st.selectbox("Source", ["Google Maps", "Facebook", "LinkedIn"], key="src_snip")
    start_btn = st.button("🚀 Start Sniper Scan", key="run_snip")

if start_btn:
    pins = [p.strip() for p in pin_input.split(",")]
    all_leads = []
    
    status_msg = st.empty()
    progress_bar = st.progress(0)

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 Sniping PIN: {pin} ({idx+1}/{len(pins)})")
        raw_items = fetch_by_pin(industry, pin, api_key, target_src)
        
        for item in raw_items:
            snippet = item.get('snippet', '') if target_src != 'Google Maps' else item.get('address', '')
            phone_raw = item.get('phoneNumber') if target_src == 'Google Maps' else re.search(r'[6-9]\d{9}', snippet)
            
            if phone_raw:
                phone = phone_raw if target_src == 'Google Maps' else phone_raw.group()
                clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                all_leads.append({
                    "PIN Code": pin,
                    "Business Name": item.get('title', 'Unknown'),
                    "Phone": clean_phone,
                    "Email": extract_email(snippet),
                    "Website": item.get('website' if target_src == 'Google Maps' else 'link', "Not Available"),
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1)

    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download", df.to_csv(index=False).encode('utf-8'), "leads.csv", "text/csv", key="dl_snip")
