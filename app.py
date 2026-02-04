import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- THE HUNTER ---
def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_and_process_pro(query, api_key, target_source, target_num):
    all_leads = []
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    pages_to_run = (target_num // 20) if target_num > 20 else 1
    prog_bar = st.progress(0)
    status_msg = st.empty()
    
    for page in range(pages_to_run):
        current_page = page + 1
        status_msg.info(f"🔍 **Scanning Page {current_page} of {pages_to_run}... (Total: {len(all_leads)})**")
        
        url = f"https://google.serper.dev/{search_type}"
        payload = json.dumps({"q": query, "num": 20, "page": current_page})
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
                continue # Try next page if this is empty
                
            for index, item in enumerate(items):
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                title = item.get('title', 'Unknown')
                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
                # Capture Rank and Website
                rank = index + 1 + (page * 20)
                website = item.get('website', 'Not Found') if is_maps else item.get('link', 'Not Found')
                
                if phone_raw:
                    phone = phone_raw if is_maps else phone_raw.group()
                    clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                    all_leads.append({
                        "Rank": rank,
                        "Business Name": title,
                        "Phone": clean_phone,
                        "Email": extract_email(snippet),
                        "Website": website,
                        "Location": query.split("in")[-1].strip(),
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            prog_bar.progress(current_page / pages_to_run)
            time.sleep(1.5)
            
        except:
            break
            
    return all_leads

# --- THE UI ---
st.set_page_config(page_title="Nuera Global Lead Pro", layout="wide")

# (Login logic remains the same...)

st.title("🌍 Nuera Global Lead Scraber")

with st.sidebar:
    st.header("📍 Location Filters")
    country = st.selectbox("Country", ["India", "USA", "UK", "UAE"])
    state = st.text_input("State", "Tamil Nadu")
    district = st.text_input("District/City", "Salem")
    
    st.divider()
    industry = st.text_input("Industry", "Dentist")
    target = st.selectbox("Source", ["Google Maps", "JustDial", "LinkedIn", "Facebook"])
    depth = st.select_slider("Lead Target", options=[20, 40, 60, 80, 100], value=40)
    
    start_scan = st.button("🔥 Run Global Scan")

if start_scan:
    # BUILD POWERFUL QUERY
    full_location = f"{district}, {state}, {country}"
    
    if target == "Google Maps":
        search_query = f"{industry} in {full_location}"
    else:
        domains = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com"}
        search_query = f'site:{domains[target]} "{industry}" "{full_location}" "+91"'
            
    results = fetch_and_process_pro(search_query, api_key, target, depth)
    
    if results:
        final_df = pd.DataFrame(results).drop_duplicates(subset=['Phone'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Leads Found", len(final_df))
        m2.metric("Target", full_location)
        m3.metric("Emails Found", len(final_df[final_df['Email'] != "Not Found"]))

        st.dataframe(final_df, use_container_width=True)
        st.download_button("📥 Export CSV", final_df.to_csv(index=False).encode('utf-8'), f"{district}_leads.csv", "text/csv")
