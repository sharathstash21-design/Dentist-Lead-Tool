import os
os.environ["OPENBLAS_NUM_THREADS"] = "1" # Fixed that memory crash!

import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# --- IMPROVED SCRAPER LOGIC ---

def search_google_social(industry, city, platform):
    """Searches Google with 'human-like' headers to avoid blocks."""
    query = f'site:{platform} "{industry}" "{city}" "+91"'
    url = f"https://www.google.com/search?q={query}"
    
    # These headers are the secret to not getting 0 results
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1"
    }

    try:
        # Added a 10-second timeout so the app doesn't hang
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return [] # If blocked, return nothing
            
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # We search broadly to find numbers hiding in text
        for g in soup.find_all('div'):
            text = g.get_text()
            # This regex finds Indian mobile numbers
            phone = re.search(r'[6-9]\d{9}', text)
            if phone:
                results.append({
                    "Name": f"{industry} @ {platform}",
                    "Phone": phone.group(),
                    "Platform": platform,
                    "Action": f"https://wa.me/91{phone.group()}"
                })
        return results
    except Exception:
        return []

# --- STREAMLIT UI ---

st.set_page_config(page_title="Dentist Lead Generator", layout="wide")
st.title("🦷 Lead Scraber Pro")

with st.sidebar:
    st.header("Search Settings")
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    search_btn = st.button("Find Leads")

if search_btn:
    with st.spinner(f"Scouring {city} for {industry} leads..."):
        # Running both platforms
        fb_leads = search_google_social(industry, city, "facebook.com")
        ig_leads = search_google_social(industry, city, "instagram.com")
        
        total_data = fb_leads + ig_leads
        
        if total_data:
            df = pd.DataFrame(total_data).drop_duplicates(subset=['Phone'])
            st.success(f"Found {len(df)} Leads!")
            
            # Displaying the data with a clickable WhatsApp link
            st.dataframe(
                df, 
                column_config={
                    "Action": st.column_config.LinkColumn("WhatsApp Lead")
                },
                use_container_width=True
            )
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "leads.csv", "text/csv")
        else:
            st.warning("Google blocked the search or no leads were found. Try again in 5 minutes.")
