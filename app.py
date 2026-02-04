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
    
    prog_bar = st.progress(0)
    status = st.empty()
    
    # Each page gives 20 results. 100 leads = 5 pages.
    pages_to_scan = (target_num // 20) if target_num > 20 else 1
    
    for page_idx in range(pages_to_scan):
        current_page = page_idx + 1
        status.info(f"🔍 **Scanning Page {current_page} of {pages_to_scan}... (Leads found: {len(all_leads)})**")
        
        url = f"https://google.serper.dev/{search_type}"
        # CRITICAL: We must send the 'page' number to get new results
        payload = json.dumps({
            "q": f"{industry} in {city}" if is_maps else f'site:{source.lower()}.com "{industry}" "{city}" "+91"',
            "num": 20,
            "page": current_page 
        })
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            data = response.json()
            
            # Pick the right data list based on source
            items = data.get('places' if is_maps else 'organic', [])
            
            if not items:
                status.warning(f"⚠️ No more data on Page {current_page}. Finishing...")
                break

            for item in items:
                snippet = item.get('snippet', '') if not is_maps else item.get('address', '')
                
                # Enhanced Email Hunter
                email = extract_email(snippet)
                if email == "Not Found" and not is_maps:
                    # Look in the title too
                    email = extract_email(item.get('title', ''))

                phone_raw = item.get('phoneNumber') if is_maps else re.search(r'[6-9]\d{9}', snippet)
                
                if phone_raw:
                    phone = phone_raw if is_maps else phone_raw.group()
                    clean_phone = re.sub(r'\D', '', str(phone))[-10:]
                    
                    all_leads.append({
                        "Business Name": item.get('title', 'Unknown'),
                        "Phone": clean_phone,
                        "Email": email,
                        "Website": item.get('website') if is_maps else item.get('link'),
                        "Source": source,
                        "WhatsApp": f"https://wa.me/91{clean_phone}"
                    })
            
            # Update UI
            prog_bar.progress(current_page / pages_to_scan)
            time.sleep(2) # Delay to prevent API rate limiting
            
        except Exception as e:
            st.error(f"Error on Page {current_page}: {e}")
            break

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

