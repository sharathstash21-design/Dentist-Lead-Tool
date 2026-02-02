import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- ADVANCED PARSING LOGIC ---

def extract_email(text):
    """Regex to find emails in snippets."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_leads(query, api_key, search_type="search", num_results=20):
    url = f"https://google.serper.dev/{search_type}"
    # Adding 'num' to get more data
    payload = json.dumps({"q": query, "num": num_results})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        return response.json()
    except:
        return {}

def parse_all_sources(data, platform, source_type):
    leads = []
    
    if source_type == "social":
        for result in data.get('organic', []):
            snippet = result.get('snippet', '')
            phone = re.search(r'[6-9]\d{9}', snippet)
            email = extract_email(snippet) # Email Hunter
            
            if phone:
                leads.append({
                    "Business Name": result.get('title', 'Unknown'),
                    "Phone": phone.group(),
                    "Email": email,
                    "Source": platform,
                    "Link": f"https://wa.me/91{phone.group()}"
                })
    else: # Maps
        for result in data.get('places', []):
            phone = result.get('phoneNumber')
            # Emails are rarely in basic Maps API, but we check snippet if available
            snippet = result.get('address', '')
            email = extract_email(snippet)
            
            if phone:
                clean_phone = re.sub(r'\D', '', phone)[-10:]
                leads.append({
                    "Business Name": result.get('title'),
                    "Phone": clean_phone,
                    "Email": email,
                    "Source": "Google Maps",
                    "Link": f"https://wa.me/91{clean_phone}"
                })
    return leads

# --- UI DASHBOARD ---
st.set_page_config(page_title="Nuera Lead Pro", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Nuera SaaS Login")
    password = st.text_input("Access Code", type="password")
    if st.button("Unlock"):
        if password == "Salem123":
            st.session_state.authenticated = True
            st.rerun()
        st.stop()

st.title("🚀 Nuera Deep-Scan Scraber")

with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("Serper API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    
    # NEW: Slider for more data
    lead_count = st.slider("Target Lead Count", 10, 100, 40)
    
    source = st.radio("Source", ["Social Media", "Google Maps"])
    search_btn = st.button("Start Deep Scan")

if search_btn:
    with st.spinner(f"Performing deep scan for {industry}..."):
        all_results = []
        
        if source == "Social Media":
            # Scan FB, IG, and LinkedIn for maximum data
            for site in ["facebook.com", "instagram.com", "linkedin.com"]:
                raw = fetch_leads(f'site:{site} "{industry}" "{city}" "+91"', user_api_key, "search", lead_count)
                all_results += parse_all_sources(raw, site.capitalize(), "social")
        else:
            raw = fetch_leads(f"{industry} in {city}", user_api_key, "maps", lead_count)
            all_results += parse_all_sources(raw, "Maps", "maps")

        if all_results:
            df = pd.DataFrame(all_results).drop_duplicates(subset=['Phone'])
            st.success(f"✅ Found {len(df)} Leads with Emails/Phones!")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Database", csv, "leads.csv", "text/csv")
        else:
            st.warning("No data found. Try increasing the Lead Count slider.")
