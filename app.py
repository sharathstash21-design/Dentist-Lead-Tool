import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- PRO LOGIC: PAGING & EMAIL HUNTER ---

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_pro_data(query, api_key, search_type="search", target_num=100):
    all_results = []
    # Serper usually gives 20 per page. To get 100, we need 5 pages.
    pages_needed = (target_num // 20) + 1
    
    for i in range(pages_needed):
        url = f"https://google.serper.dev/{search_type}"
        # 'start' tells Google which page to begin on (0, 20, 40, etc.)
        payload = json.dumps({
            "q": query, 
            "num": 20, 
            "page": i + 1 
        })
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            
            # Add results from this page to our main list
            items = data.get('places' if search_type == "maps" else 'organic', [])
            all_results.extend(items)
            
            # Stop if we hit our target or if there's no more data
            if len(all_results) >= target_num or not items:
                break
        except:
            break
            
    return all_results[:target_num]

def process_results(data, source_name, is_maps=False):
    leads = []
    items = data.get('places' if is_maps else 'organic', [])
    for item in items:
        snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
        title = item.get('title', 'Unknown')
        phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
        
        if phone_raw:
            phone = phone_raw if is_maps else phone_raw.group()
            clean_phone = re.sub(r'\D', '', phone)[-10:]
            leads.append({
                "Business Name": title,
                "Phone": clean_phone,
                "Email": extract_email(snippet),
                "Source": source_name,
                "Action": f"https://wa.me/91{clean_phone}"
            })
    return leads

# --- UI DESIGN: PROFESSIONAL DASHBOARD ---

st.set_page_config(page_title="Nuera Lead Pro", layout="wide", page_icon="📈")

# 1. CLEAN LOGIN
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Client Access Portal")
    col1, col2 = st.columns([1, 2])
    with col1:
        code = st.text_input("Enter License Key", type="password")
        if st.button("Access Software"):
            if code == "Salem123":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Key")
    st.stop()

# 2. MAIN DASHBOARD
st.title("🚀 Nuera Lead Scraber Pro")
st.markdown("### *Premium Business Intelligence & Lead Extraction*")

# Sidebar for professional organization
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=100)
    st.header("Admin Settings")
    api_key = st.text_input("API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    st.header("Search Filters")
    industry = st.text_input("Target Industry", "Dentist")
    city = st.text_input("Target City", "Salem")
    
    target = st.selectbox("Data Source", ["Google Maps", "JustDial", "LinkedIn", "Facebook", "Instagram"])
    depth = st.select_slider("Extraction Depth", options=[10, 20, 50, 100], value=20)
    
    start_scan = st.button("🔥 Start Deep Extraction", use_container_width=True)

# 3. RESULTS AREA
if start_scan:
    with st.spinner("Analyzing Search Results..."):
        # Source Mapping
        source_map = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com", "Instagram": "instagram.com"}
        
        if target == "Google Maps":
            raw = fetch_pro_data(f"{industry} in {city}", api_key, "maps", depth)
            final_df = pd.DataFrame(process_results(raw, "Maps", True))
        else:
            domain = source_map[target]
            q = f'site:{domain} "{industry}" "{city}" "+91"'
            raw = fetch_pro_data(q, api_key, "search", depth)
            final_df = pd.DataFrame(process_results(raw, target, False))

        if not final_df.empty:
            final_df = final_df.drop_duplicates(subset=['Phone'])
            
            # KPI METRIC CARDS
            m1, m2, m3 = st.columns(3)
            m1.metric("Leads Found", len(final_df))
            m2.metric("Verified Phones", len(final_df[final_df['Phone'].str.len() == 10]))
            m3.metric("Emails Captured", len(final_df[final_df['Email'] != "Not Found"]))

            st.divider()
            
            # DATA TABLE
            st.dataframe(
                final_df,
                column_config={"Action": st.column_config.LinkColumn("WhatsApp Link")},
                use_container_width=True
            )
            
            # DOWNLOAD
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Lead Database (CSV)", csv, f"{city}_leads.csv", "text/csv")
        else:
            st.error("No results found. Please check your API credits or try a broader search.")

