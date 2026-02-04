import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. THE BRAIN ---

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_and_process_pro(query, api_key, target_source, target_num):
    all_leads = []
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    # Force the loop to run the exact number of pages needed
    pages_to_run = (target_num // 20) if target_num > 20 else 1
    
    prog_bar = st.progress(0)
    status_msg = st.empty()
    
    for page in range(pages_to_run):
        current_page = page + 1
        status_msg.info(f"🔍 **Scanning Page {current_page} of {pages_to_run}... (Found: {len(all_leads)})**")
        
        url = f"https://google.serper.dev/{search_type}"
        # We use 'page' parameter to actually turn the page
        payload = json.dumps({
            "q": query, 
            "num": 20, 
            "page": current_page 
        })
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            # If a page is empty, we don't 'break' anymore, we just 'continue' to the next
            if not items:
                time.sleep(1)
                continue
                
            for index, item in enumerate(items):
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                title = item.get('title', 'Unknown')
                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
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
                        "Source": target_source,
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            prog_bar.progress(current_page / pages_to_run)
            time.sleep(1.5) # Give the API a second to breathe
            
        except Exception as e:
            st.error(f"Error on page {current_page}: {e}")
            break
            
    status_msg.success(f"✅ Extraction Complete! Total Leads: {len(all_leads)}")
    return all_leads

# --- 2. THE UI ---

st.set_page_config(page_title="Nuera Lead Pro", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 License Portal")
    code = st.text_input("Enter License Key", type="password")
    if st.button("Access"):
        if code == "Salem123":
            st.session_state.auth = True
            st.rerun()
    st.stop()

st.title("🚀 Nuera Deep-Scan Scraber")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    target = st.selectbox("Source", ["Google Maps", "JustDial", "LinkedIn", "Facebook", "Instagram"])
    depth = st.select_slider("Lead Target", options=[20, 40, 60, 80, 100], value=40)
    start_scan = st.button("🔥 Run Deep Scan")

if start_scan:
    source_map = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com", "Instagram": "instagram.com"}
    if target == "Google Maps":
        search_query = f"{industry} in {city}"
    else:
        domain = source_map[target]
        search_query = f'site:{domain} "{industry}" "{city}" "+91"'
            
    # CRITICAL FIX: Get the data first
    extracted_data = fetch_and_process_pro(search_query, api_key, target, depth)
    
    # CRITICAL FIX: Convert to DataFrame
    if extracted_data:
        final_df = pd.DataFrame(extracted_data).drop_duplicates(subset=['Phone'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Leads Found", len(final_df))
        m2.metric("Source", target)
        m3.metric("Emails Found", len(final_df[final_df['Email'] != "Not Found"]))

        st.dataframe(final_df, use_container_width=True)
        
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, f"{industry}_leads.csv", "text/csv")
    else:
        st.error("No results found. Try a different source or industry.")
