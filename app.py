import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- 1. THE DATA HUNTER ---
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
        status_msg.info(f"🔍 **Scanning Page {current_page} of {pages_to_run}... (Total found: {len(all_leads)})**")
        
        url = f"https://google.serper.dev/{search_type}"
        payload = json.dumps({"q": query, "num": 20, "page": current_page})
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
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
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            prog_bar.progress(current_page / pages_to_run)
            time.sleep(1)
        except:
            break
            
    return all_leads

# --- 2. THE UI ---
st.set_page_config(page_title="Nuera TN Lead Pro", layout="wide")

# Login Logic
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

st.title("🚀 Nuera TN Lead Scraber")

# Location Data
tn_districts = ["Salem", "Chennai", "Coimbatore", "Madurai", "Trichy", "Erode", "Tiruppur", "Vellore", "Thanjavur", "Tuticorin", "Tirunelveli"]

with st.sidebar:
    st.header("📍 Location Filters")
    # This fixed the NameError by ensuring api_key is always defined
    api_key_input = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    country = "India"
    state = "Tamil Nadu"
    district = st.selectbox("Select TN District", tn_districts)
    
    st.divider()
    industry = st.text_input("Business Type", "Dentist")
    target = st.selectbox("Source", ["Google Maps", "Facebook", "LinkedIn", "JustDial"])
    depth = st.select_slider("Lead Target", options=[20, 40, 60, 80, 100], value=40)
    
    start_scan = st.button("🔥 Run Scan")

if start_scan:
    full_loc = f"{district}, {state}, {country}"
    
    # Building the Query
    if target == "Google Maps":
        q = f"{industry} in {full_loc}"
    else:
        domains = {"Facebook": "facebook.com", "LinkedIn": "linkedin.com", "JustDial": "justdial.com"}
        q = f'site:{domains[target]} "{industry}" "{full_loc}" "+91"'
            
    # Passing api_key_input directly to fix the NameError
    results = fetch_and_process_pro(q, api_key_input, target, depth)
    
    if results:
        df = pd.DataFrame(results).drop_duplicates(subset=['Phone'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Leads Found", len(df))
        m2.metric("Location", district)
        m3.metric("Emails Found", len(df[df['Email'] != "Not Found"]))

        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Export CSV", df.to_csv(index=False).encode('utf-8'), f"{district}_leads.csv", "text/csv")
    else:
        st.error("No data found. Check your API or try another district.")
