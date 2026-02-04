import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. DATA EXTRACTION TOOLS ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Available"

def fetch_precious_data(query, pin, api_key, target_source):
    url = "https://www.searchapi.io/api/v1/search"
    is_maps = (target_source == "Google Maps")
    
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
        
        # SearchAPI organizes Maps results in 'places' or 'local_results'
        results = data.get('places', []) or data.get('local_results', [])
        if not results and not is_maps:
            results = data.get('organic_results', [])
            
        return results
    except:
        return []

# --- 2. THE UI ---
st.title("🎯 Nuera Precious Lead Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password", key="api_snip")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Dentist"), key="ind_snip")
    pin_input = st.text_area("PIN Codes", value=st.session_state.get('sniping_pincodes', ""), key="pins_snip")
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"], key="src_snip")
    start_btn = st.button("🚀 Start Precious Extraction", key="run_snip")

if start_btn:
    pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    all_leads = []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 Sniping PIN: {pin} ({idx+1}/{len(pins)})")
        raw_items = fetch_precious_data(industry, pin, api_key_val, target_src)
        
        for rank, item in enumerate(raw_items, 1):
            # Extracting all the 'Precious' fields from SearchAPI
            phone_raw = item.get('phone') or item.get('phone_number')
            
            if phone_raw:
                clean_phone = re.sub(r'\D', '', str(phone_raw))[-10:]
                
                all_leads.append({
                    "GMB Rank": rank,
                    "Business Name": item.get('title', 'Unknown'),
                    "Rating ⭐": item.get('rating', 'N/A'),
                    "Reviews 💬": item.get('reviews', 0),
                    "Phone": clean_phone,
                    "Email": extract_email(str(item)),
                    "Website": item.get('website') or item.get('link', 'Not Available'),
                    "Address": item.get('address', 'View on Maps'),
                    "PIN Code": pin,
                    "WhatsApp": f"https://wa.me/91{clean_phone}"
                })
        
        progress_bar.progress((idx + 1) / len(pins))
        time.sleep(1)

    if all_leads:
        df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
        
        # --- 3. SALES METRICS ---
        st.success(f"✅ Extracted {len(df)} High-Quality Leads!")
        
        m1, m2, m3 = st.columns(3)
        no_web = len(df[df['Website'] == "Not Available"])
        low_rated = len(df[(df['Rating ⭐'] != 'N/A') & (df['Rating ⭐'] < 4.0)])
        
        m1.metric("Total Leads", len(df))
        m2.metric("No Website (Web Sales)", no_web)
        m3.metric("Low Rated (SEO Sales)", low_rated)

        st.divider()
        
        # Professional Data Table
        st.dataframe(
            df, 
            column_config={
                "WhatsApp": st.column_config.LinkColumn("Chat"),
                "Website": st.column_config.LinkColumn("Website"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # CSV Download
        st.download_button(
            "📥 Download Precious Database (CSV)", 
            df.to_csv(index=False).encode('utf-8'), 
            f"precious_{industry}.csv", 
            "text/csv",
            key="dl_btn"
        )
    else:
        st.error("❌ No results found. Try switching to 'Google Maps' or checking your PIN codes.")
