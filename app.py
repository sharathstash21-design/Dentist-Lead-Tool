import streamlit as st
import pandas as pd
import requests
import json
import re
import time

# --- 1. THE DATA HUNTER ---

def extract_email(text):
    """Regex to catch emails in snippets."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_massive_leads(industry, city, api_key, target_num, source):
    all_leads = []
    is_maps = (source == "Google Maps")
    search_type = "maps" if is_maps else "search"
    
    # UI Progress
    prog_bar = st.progress(0)
    status = st.empty()
    
    # Turn the page up to the requested depth
    pages = (target_num // 20) if target_num > 20 else 1
    
    for page in range(pages):
        current_page = page + 1
        status.info(f"🔍 **Scanning Page {current_page} of {pages}... Found {len(all_leads)} leads.**")
        
        # Build query
        if source == "Google Maps":
            q = f"{industry} in {city}"
        else:
            domains = {"JustDial": "justdial.com", "LinkedIn": "linkedin.com", "Facebook": "facebook.com"}
            q = f'site:{domains.get(source, "google.com")} "{industry}" "{city}" "+91"'

        url = f"https://google.serper.dev/{search_type}"
        payload = json.dumps({"q": q, "num": 20, "page": current_page})
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
                # If we hit a dead end, try a broader search for the next page
                status.warning(f"⚠️ Page {current_page} was thin. Broadening search...")
                continue

            for idx, item in enumerate(items):
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                website = item.get('website') if is_maps else item.get('link')
                
                # Phone extraction
                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
                if phone_raw:
                    phone = phone_raw if is_maps else phone_raw.group()
                    clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                    
                    all_leads.append({
                        "Rank": idx + 1 + (page * 20),
                        "Business Name": item.get('title', 'Unknown'),
                        "Phone": clean_phone,
                        "Email": extract_email(snippet),
                        "Website": website if website else "Not Found",
                        "Source": source,
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            prog_bar.progress((page + 1) / pages)
            time.sleep(1) # Safety delay
            
        except Exception as e:
            st.error(f"Error: {e}")
            break

    status.success(f"✅ Extraction Complete! Total Unique Leads: {len(all_leads)}")
    return all_leads

# --- 2. THE UI ---

st.set_page_config(page_title="Nuera Deep-Scan", layout="wide")
st.title("🚀 Nuera Deep-Scan Lead Scraber")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Serper API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    industry = st.text_input("Industry", "Dentist")
    city = st.text_input("City", "Salem")
    source = st.selectbox("Source", ["Google Maps", "JustDial", "Facebook", "LinkedIn"])
    depth = st.select_slider("Lead Target", options=[20, 40, 60, 80, 100], value=40)
    run = st.button("🔥 Start Deep Extraction")

if run:
    results = fetch_massive_leads(industry, city, api_key, depth, source)
    
    if results:
        df = pd.DataFrame(results).drop_duplicates(subset=['Phone'])
        
        # Metric Dashboard
        c1, c2, c3 = st.columns(3)
        c1.metric("Leads Found", len(df))
        c2.metric("Target City", city)
        c3.metric("Emails Found", len(df[df['Email'] != "Not Found"]))
        
        st.dataframe(
            df, 
            column_config={
                "WhatsApp": st.column_config.LinkColumn("Message"),
                "Website": st.column_config.LinkColumn("Visit")
            },
            use_container_width=True
        )
        
        st.download_button("📥 Download Full CSV", df.to_csv(index=False).encode('utf-8'), "leads.csv", "text/csv")
