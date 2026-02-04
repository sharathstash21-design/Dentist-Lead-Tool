import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. CORE DATA LOGIC ---
def extract_email(text):
    """Detects emails in text. Returns 'Not Available' if none found."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_by_pin(query, pin, api_key, target_source):
    """Fetches 20 leads for a specific PIN code."""
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    # Ensuring we stay in India
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

# --- 2. USER INTERFACE ---

st.title("🎯 Nuera PIN Code Sniper")
st.markdown("### *Precision Lead Extraction Area-by-Area*")

# SIDEBAR CONFIGURATION
with st.sidebar:
    st.header("⚙️ Sniper Settings")
    
    # Unique keys prevent 'DuplicateElementId' errors
    api_key = st.text_input(
        "Serper API Key", 
        value="7ab11ec8c0050913c11a96062dc1e295af9743f0", 
        type="password", 
        key="api_key_sniper"
    )
    
    industry = st.text_input("Business Type", "Dental Clinic", key="ind_sniper")
    
    # AUTO-CONNECT: Check if PINs were sent from the Generator Page
    ready_pins = st.session_state.get('sniping_pincodes', "636001, 636007")
    pin_input = st.text_area("Target PIN Codes (comma separated)", value=ready_pins, key="pins_sniper")
    
    target_src = st.selectbox("Data Source", ["Google Maps", "Facebook", "LinkedIn"], key="src_sniper")
    
    start_btn = st.button("🚀 Start Sniper Scan", use_container_width=True, key="btn_sniper")

# --- 3. EXECUTION ---

if start_btn:
    # Clean the input list
    pins = [p.strip() for p in pin_input.split(",")]
    all_leads = []
    
    # Visual Feedback
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 **Sniping PIN: {pin} ({idx+1} of {len(pins)})...**")
        
        raw_items = fetch_by_pin(industry, pin, api_key, target_src)
        
        for item in raw_items:
            # Handle different data structures from Maps vs Search
            snippet = item.get('snippet', '') if target_src != "Google Maps" else item.get('address', '')
            web_link = item.get('website') if target_src == "Google Maps" else item.get('link')
            
            # Extract Phone
            phone_raw = item.get('phoneNumber') if target_src == "Google Maps" else re.search(r'[6-9]\d{9}', snippet)
            
            if phone_raw:
                phone = phone_raw if target_src == "Google Maps" else phone_raw.group()
                clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                
                all_leads.append({
                    "PIN Code": pin,
                    "Business Name": item.get('title', 'Unknown'),
                    "Phone": clean_phone,
                    "Email": extract_email(snippet),
                    "Website": web_link if web_link else "Not Available",
                    "Source": target_src,
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        
        # Update progress
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1) # Be gentle with the API

    # --- 4. DISPLAY RESULTS ---
    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        
        # Sales Intelligence Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Leads", len(df))
        m2.metric("PINs Scanned", len(pins))
        
        no_web = len(df[df['Website'] == "Not Available"])
        m3.metric("Web Opportunities", no_web)

        if no_web > 0:
            st.warning(f"💡 Found {no_web} businesses without a website. Great for Web Dev sales!")

        st.dataframe(
            df, 
            column_config={
                "WhatsApp": st.column_config.LinkColumn("Chat on WA"),
                "Website": st.column_config.LinkColumn("Website Link")
            },
            use_container_width=True
        )
        
        # Export Data
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Sniper Database (CSV)", 
            csv_data, 
            f"leads_{industry}.csv", 
            "text/csv",

            with st.sidebar:
    st.header("⚙️ Sniper Settings")
    
    # GET THE CATEGORY FROM THE SHARED BRAIN
    # Default to "Dental Clinic" if nothing was sent
    saved_category = st.session_state.get('sniping_category', "Dental Clinic")
    industry = st.text_input("Business Type", value=saved_category, key="ind_sniper")
    
    # GET THE PINs
    ready_pins = st.session_state.get('sniping_pincodes', "636001, 636007")
    pin_input = st.text_area("Target PIN Codes", value=ready_pins, key="pins_sniper")
            key="download_sniper"
        )
    else:
        st.error("Target area scan returned 0 results. Try different PIN codes.")
