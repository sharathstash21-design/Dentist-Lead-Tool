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

def fetch_universal(query, pin, api_key, target_source):
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
        # SearchAPI organizes data into 'places' for Maps
        return data.get('places', []) if is_maps else data.get('organic_results', [])
    except:
        return []

# --- 2. THE UI ---
st.title("🎯 Nuera Precious Lead Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Hotels"))
    pin_input = st.text_area("PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])
    start_btn = st.button("🚀 Start Precious Extraction")

if start_btn:
    pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    all_leads = []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for idx, pin in enumerate(pins):
        status_msg.info(f"📍 Sniping PIN: {pin} ({idx+1}/{len(pins)})")
        raw_items = fetch_universal(industry, pin, api_key_val, target_src)
        
        for rank, item in enumerate(raw_items, 1):
            phone_raw = item.get('phone') or item.get('phone_number')
            if phone_raw:
                clean_phone = re.sub(r'\D', '', str(phone_raw))[-10:]
                
                # PULLING THE PRECIOUS DATA
                all_leads.append({
                    "GMB Rank": rank,
                    "Business Name": item.get('title', 'Unknown'),
                    "Rating ⭐": item.get('rating', 'No Rating'),
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
        
        # --- 3. POTENTIAL DATA SUMMARY ---
        st.success(f"✅ Found {len(df)} Precious Leads!")
        
        c1, c2, c3 = st.columns(3)
        no_web = len(df[df['Website'] == "Not Available"])
        low_rank = len(df[df['GMB Rank'] > 5])
        
        c1.metric("Total Extracted", len(df))
        c2.metric("No Website (Sales!)", no_web)
        c3.metric("Need SEO (Rank > 5)", low_rank)

        st.divider()
        
        # Display with professional links
        st.dataframe(
            df, 
            column_config={
                "WhatsApp": st.column_config.LinkColumn("Chat"),
                "Website": st.column_config.LinkColumn("Visit"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button("📥 Download Database", df.to_csv(index=False).encode('utf-8'), "precious_leads.csv", "text/csv")
    else:
        st.error("No results found. Try a different PIN or Category.")
