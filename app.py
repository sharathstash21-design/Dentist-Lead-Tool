import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
exit
import streamlit as st
import pandas as pd
# ... rest of your code ...

import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# --- SCRAPER LOGIC ---

def search_google_social(industry, city, platform):
    """Searches Google for social media profiles with phone numbers."""
    query = f'site:{platform} "{industry}" "{city}" "+91"'
    url = f"https://www.google.com/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for g in soup.find_all('div'):
            text = g.get_text()
            phone = re.search(r'[6-9]\d{9}', text)
            if phone:
                results.append({
                    "Name": f"{industry} @ {platform}",
                    "Phone": phone.group(),
                    "Platform": platform,
                    "Link": f"https://wa.me/91{phone.group()}"
                })
        return results
    except:
        return []

# --- STREAMLIT UI ---

st.set_page_config(page_title="Salem Lead Generator", layout="wide")
st.title("🦷 Dentist Lead Generator (Salem/CBE/Chennai)")

with st.sidebar:
    st.header("Search Settings")
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    search_btn = st.button("Find Leads")

if search_btn:
    with st.spinner("Scraping Facebook, Instagram, and Google..."):
        # We run the search for different platforms
        fb_leads = search_google_social(industry, city, "facebook.com")
        ig_leads = search_google_social(industry, city, "instagram.com")
        
        all_leads = fb_leads + ig_leads
        
        if all_leads:
            df = pd.DataFrame(all_leads).drop_duplicates(subset=['Phone'])
            st.success(f"Found {len(df)} Unique Leads!")
            
            # Show the data in a nice table
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button("📥 Download Leads CSV", csv, "leads.csv", "text/csv")
        else:
            st.warning("No leads found. Try a different city or industry.")