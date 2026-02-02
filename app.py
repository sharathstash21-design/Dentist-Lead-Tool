import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- CORE LOGIC FUNCTIONS ---

def fetch_leads(query, api_key, search_type="organic"):
    """Generic fetcher for both Maps and Social Media."""
    url = f"https://google.serper.dev/{search_type}"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        return response.json()
    except:
        return {}

def parse_social_leads(data, platform):
    leads = []
    for result in data.get('organic', []):
        snippet = result.get('snippet', '')
        phone = re.search(r'[6-9]\d{9}', snippet)
        if phone:
            leads.append({
                "Business Name": result.get('title', 'Unknown'),
                "Phone": phone.group(),
                "Source": platform,
                "Action Link": f"https://wa.me/91{phone.group()}"
            })
    return leads

def parse_maps_leads(data):
    leads = []
    for result in data.get('places', []):
        phone = result.get('phoneNumber')
        if phone:
            # Clean non-digits
            clean_phone = re.sub(r'\D', '', phone)[-10:]
            leads.append({
                "Business Name": result.get('title'),
                "Phone": clean_phone,
                "Source": "Google Maps",
                "Action Link": f"https://www.google.com/maps/place/?q=place_id:{result.get('cid')}"
            })
    return leads

# --- UI SETUP ---
st.set_page_config(page_title="Pro Scraber SaaS", layout="wide")

# 1. SIMPLE LOGIN
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 SaaS Login")
    password = st.text_input("Enter Access Code", type="password")
    if st.button("Unlock Tool"):
        if password == "Salem123": # Change this to your desired password
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Wrong code, brother!")
    st.stop()

# --- MAIN APP ---
st.title("🚀 Multi-Source Lead Scraber")

with st.sidebar:
    st.header("⚙️ Configuration")
    user_api_key = st.text_input("Serper API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    st.header("🔍 Search Parameters")
    industry = st.text_input("Industry/Business", "Dentist")
    city = st.text_input("City", "Salem")
    
    source = st.radio("Select Source", ["Social Media (FB/IG)", "Google Maps"])
    
    search_btn = st.button("Extract Leads")

if search_btn:
    if not user_api_key:
        st.error("Please enter an API Key!")
    else:
        with st.spinner("Extracting data..."):
            all_results = []
            
            if source == "Social Media (FB/IG)":
                # Search FB
                fb_raw = fetch_leads(f'site:facebook.com "{industry}" "{city}" "+91"', user_api_key, "search")
                all_results += parse_social_leads(fb_raw, "Facebook")
                # Search IG
                ig_raw = fetch_leads(f'site:instagram.com "{industry}" "{city}" "+91"', user_api_key, "search")
                all_results += parse_social_leads(ig_raw, "Instagram")
            
            else:
                # Search Google Maps
                maps_raw = fetch_leads(f"{industry} in {city}", user_api_key, "maps")
                all_results += parse_maps_leads(maps_raw)

            if all_results:
                df = pd.DataFrame(all_results).drop_duplicates(subset=['Phone'])
                
                # METRICS
                st.success(f"Successfully extracted {len(df)} leads!")
                
                # DISPLAY TABLE
                st.dataframe(
                    df,
                    column_config={"Action Link": st.column_config.LinkColumn("Visit/Message")},
                    use_container_width=True
                )
                
                # DOWNLOAD
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download All Data", csv, f"{industry}_{city}_leads.csv", "text/csv")
            else:
                st.warning("No data found. Try changing your search keywords.")
