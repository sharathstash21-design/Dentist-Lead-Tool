import os
# Fixing that memory crash permanently
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- POWERED BY SERPER API ---

def search_leads_via_api(industry, city, platform, api_key):
    url = "https://google.serper.dev/search"
    
    # This specifically hunts for Indian mobile numbers on social pages
    query = f'site:{platform} "{industry}" "{city}" "+91"'
    
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        leads = []
        
        # Organic results are the real gold mine
        for result in data.get('organic', []):
            snippet = result.get('snippet', '')
            # Regex for Indian mobile numbers starting with 6-9
            phone = re.search(r'[6-9]\d{9}', snippet)
            
            if phone:
                leads.append({
                    "Clinic/Name": result.get('title', 'Dentist'),
                    "Phone": phone.group(),
                    "Platform": platform,
                    "WhatsApp": f"https://wa.me/91{phone.group()}"
                })
        return leads
    except Exception:
        return []

# --- STREAMLIT UI ---

st.set_page_config(page_title="Dentist Lead Pro", layout="wide")
st.title("🦷 Dentist Lead Scraber (API Powered)")
st.markdown("Directly fetching verified numbers from Facebook & Instagram.")

# Your API Key is now hardcoded here for your personal use
API_KEY = "7ab11ec8c0050913c11a96062dc1e295af9743f0"

with st.sidebar:
    st.header("Search Settings")
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    search_btn = st.button("Generate Leads")

if search_btn:
    with st.spinner(f"Scraping {industry} leads in {city}..."):
        # Fetching from both platforms
        fb_leads = search_leads_via_api(industry, city, "facebook.com", API_KEY)
        ig_leads = search_leads_via_api(industry, city, "instagram.com", API_KEY)
        
        total_leads = fb_leads + ig_leads
        
        if total_leads:
            df = pd.DataFrame(total_leads).drop_duplicates(subset=['Phone'])
            st.success(f"🔥 Found {len(df)} High-Quality Leads!")
            
            # Making the WhatsApp link clickable in the table
            st.dataframe(
                df,
                column_config={
                    "WhatsApp": st.column_config.LinkColumn("Message Now")
                },
                use_container_width=True
            )
            
            # Download button for your CSV backup
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Lead List", csv, f"{city}_leads.csv", "text/csv")
        else:
            st.error("Still no leads found. Check if your API key has credits left!")
