import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json
import time

# --- CORE LOGIC: DATA HUNTER ---

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_and_process_pro(query, api_key, target_source, target_num):
    all_leads = []
    is_maps = (target_source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    # Calculate how many pages we need to turn
    pages_to_run = (target_num // 20) if target_num > 20 else 1
    
    # UI Elements for Live Updates
    prog_bar = st.progress(0)
    status_msg = st.empty()
    
    for page in range(pages_to_run):
        current_page = page + 1
        status_msg.info(f"🔍 **Scanning Page {current_page} of {pages_to_run}... Found {len(all_leads)} leads so far.**")
        
        url = f"https://google.serper.dev/{search_type}"
        payload = json.dumps({"q": query, "num": 20, "page": current_page})
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
                status_msg.warning(f"⚠️ No more results found on Page {current_page}. Stopping search.")
                break
                
            for index, item in enumerate(items):
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                title = item.get('title', 'Unknown')
                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
                # New Data Points: Rank and Website
                rank = index + 1 + (page * 20)
                website = item.get('website', 'Not Found') if is_maps else item.get('link', 'Not Found')
                
                if phone_raw:
                    phone = phone_raw if is_maps else phone_raw.group()
                    clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                    all_leads.append({
                        "Rank": rank, # Competitor Ranking
                        "Business Name": title,
                        "Keyword": query, # The keyword used
                        "Phone": clean_phone,
                        "Email": extract_email(snippet),
                        "Website": website,
                        "Source": target_source,
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            # Update Progress Bar
            prog_bar.progress(current_page / pages_to_run)
            time.sleep(1) # Small delay to be safe
            
            if len(all_leads) >= target_num:
                break
        except:
            break
            
    status_msg.success(f"✅ Extraction Complete! Total Leads: {len(all_leads)}")
    return all_leads

# --- UI DESIGN ---

st.set_page_config(page_title="Nuera Lead Pro", layout="wide", page_icon="📈")

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
st.markdown("### *Competitor Research & Lead Intelligence*")

with st.sidebar:
    st.header("Admin Settings")
    api_key = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    industry = st.text_input("Business Category", "Dentist")
    city = st.text_input("Location", "Salem")
    target = st.selectbox("Source", ["Google Maps", "JustDial", "LinkedIn", "Facebook", "Instagram"])
    depth = st.select_slider("Lead Target (Depth)", options=[20, 40, 60, 80, 100], value=40)
    
    start_scan = st.button("🔥 Run Deep Scan", use_container_width=True)

if start_scan:
    source_map = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com", "Instagram": "instagram.com"}
    if target == "Google Maps":
        search_query = f"{industry} in {city}"
    else:
        domain = source_map[target]
        search_query = f'site:{domain} "{industry}" "{city}" "+91"'
            
    leads_data = fetch_and_process_pro(search_query, api_key, target, depth)
    final_df = pd.DataFrame(leads_list := leads_data)

    if not final_df.empty:
        final_df = final_df.drop_duplicates(subset=['Phone'])
        
        # Dashboard Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("Leads Found", len(final_df))
        m2.metric("Keyword Used", industry)
        m3.metric("Emails Found", len(final_df[final_df['Email'] != "Not Found"]))

        st.dataframe(
            final_df,
            column_config={"WhatsApp": st.column_config.LinkColumn("Message Now"), "Website": st.column_config.LinkColumn("Visit Site")},
            use_container_width=True
        )
        
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Deep Scan (CSV)", csv, f"{industry}_{city}_analysis.csv", "text/csv")
