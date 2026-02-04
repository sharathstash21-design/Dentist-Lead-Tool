import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- 1. PRO LOGIC: PAGINATION & EMAIL HUNTER ---

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_and_process(query, api_key, target_source, target_num):
    """Loops through pages to get the full lead count requested."""
    all_leads = []
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    # Each page gives 20 results
    pages_to_run = (target_num // 20) if target_num > 20 else 1
    
    for page in range(pages_to_run):
        url = f"https://google.serper.dev/{search_type}"
        payload = json.dumps({
            "q": query, 
            "num": 20, 
            "page": page + 1
        })
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
                break
                
            for item in items:
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                title = item.get('title', 'Unknown')
                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
                if phone_raw:
                    phone = phone_raw if is_maps else phone_raw.group()
                    clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                    all_leads.append({
                        "Business Name": title,
                        "Phone": clean_phone,
                        "Email": extract_email(snippet),
                        "Source": target_source,
                        "Action": f"https://wa.me/91{clean_phone}"
                    })
            
            if len(all_leads) >= target_num:
                break
        except:
            break
            
    return all_leads[:target_num]

# --- 2. UI DESIGN: PROFESSIONAL DASHBOARD ---

st.set_page_config(page_title="Nuera Lead Pro", layout="wide", page_icon="📈")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Client Access Portal")
    code = st.text_input("Enter License Key", type="password")
    if st.button("Access Software"):
        if code == "Salem123":
            st.session_state.auth = True
            st.rerun()
    st.stop()

st.title("🚀 Nuera Lead Scraber Pro")
st.markdown("### *Premium Business Intelligence & Lead Extraction*")

with st.sidebar:
    st.header("Admin Settings")
    api_key = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    st.header("Search Filters")
    industry = st.text_input("Target Industry", "Dentist")
    city = st.text_input("Target City", "Salem")
    target = st.selectbox("Data Source", ["Google Maps", "JustDial", "LinkedIn", "Facebook", "Instagram"])
    depth = st.select_slider("Extraction Depth", options=[20, 40, 60, 80, 100], value=40)
    
    start_scan = st.button("🔥 Start Deep Extraction", use_container_width=True)

# --- 3. RESULTS AREA ---

if start_scan:
    with st.spinner(f"Scanning multiple pages for {industry} in {city}..."):
        # Build Query
        source_map = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com", "Instagram": "instagram.com"}
        if target == "Google Maps":
            search_query = f"{industry} in {city}"
        else:
            domain = source_map[target]
            search_query = f'site:{domain} "{industry}" "{city}" "+91"'
            
        leads_list = fetch_and_process(search_query, api_key, target, depth)
        final_df = pd.DataFrame(leads_list)

        if not final_df.empty:
            final_df = final_df.drop_duplicates(subset=['Phone'])
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Leads Found", len(final_df))
            m2.metric("Verified Phones", len(final_df[final_df['Phone'].str.len() == 10]))
            m3.metric("Emails Captured", len(final_df[final_df['Email'] != "Not Found"]))

            st.dataframe(
                final_df,
                column_config={"Action": st.column_config.LinkColumn("WhatsApp Link")},
                use_container_width=True
            )
            
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Lead Database (CSV)", csv, f"{city}_leads.csv", "text/csv")
        else:
            st.error("No results found. Try increasing Depth or check API credits.")
