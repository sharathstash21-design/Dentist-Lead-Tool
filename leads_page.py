import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. THE DATA HUNTER ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_by_pin_searchapi(query, pin, api_key, target_source):
    """Fetches leads using SearchAPI.io engine."""
    # SearchAPI uses 'google_maps' for local business listings
    is_maps = (target_source == "Google Maps")
    engine = "google_maps" if is_maps else "google"
    
    url = "https://www.searchapi.io/api/v1/search"
    
    # We add 'India' to ensure pinpoint accuracy
    refined_q = f"{query} {pin} India"
    
    params = {
        "engine": engine,
        "q": refined_q,
        "api_key": api_key,
        "gl": "in", # Sets location to India
        "hl": "en"  # Sets language to English
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        
        # SearchAPI returns 'places' for Google Maps engine
        if is_maps:
            return data.get('places', [])
        else:
            # For standard Google Search, it returns 'organic_results'
            return data.get('organic_results', [])
    except Exception as e:
        st.error(f"SearchAPI Connection Error: {e}")
        return []

# --- 2. THE UI ---
st.title("🎯 Nuera PIN Code Sniper")
st.markdown("### *Powered by SearchAPI.io*")

# Check for data from Generator
default_cat = st.session_state.get('sniping_category', "Dental Clinic")
default_pins = st.session_state.get('sniping_pincodes', "")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    # Using your new SearchAPI key
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password", key="api_snip")
    
    industry = st.text_input("Business Type", value=default_cat, key="ind_snip")
    pin_input = st.text_area("PIN Codes", value=default_pins, key="pins_snip")
    
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"], key="src_snip")
    start_btn = st.button("🚀 Start Sniper Scan", key="run_snip")

if start_btn:
    if not pin_input:
        st.error("⚠️ No PIN codes found! Go to the Prompt Generator first.")
        st.stop()
        
    pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    all_leads = []
    
    status_msg = st.empty()
    progress_bar = st.progress(0)

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 Sniping PIN: {pin} ({idx+1}/{len(pins)})")
        
        raw_items = fetch_by_pin_searchapi(industry, pin, api_key_val, target_src)
        
        for item in raw_items:
            # SearchAPI 'places' fields are slightly different
            name = item.get('title', 'Unknown')
            address = item.get('address', '')
            site = item.get('website', 'Not Available')
            phone_raw = item.get('phone') # SearchAPI Maps results usually have 'phone'
            
            # Use snippet for email extraction if not in maps
            snippet = item.get('snippet', address)
            
            if phone_raw:
                # Clean phone to 10 digits
                clean_phone = re.sub(r'\D', '', str(phone_raw))[-10:]
                
                all_leads.append({
                    "PIN Code": pin,
                    "Business Name": name,
                    "Phone": clean_phone,
                    "Email": extract_email(snippet),
                    "Website": site,
                    "Address": address,
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1) # SearchAPI is fast, but we stay safe

    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        st.success(f"✅ Total leads sniped: {len(df)}")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download Data", df.to_csv(index=False).encode('utf-8'), "leads.csv", "text/csv")
    else:
        st.error("❌ No results found. Check your SearchAPI credits or try a different PIN.")
