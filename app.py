import os
# Final fix for the Windows memory crash issue
os.environ["OPENBLAS_NUM_THREADS"] = "1" 

import streamlit as st
import pandas as pd
import re
import requests
import json

# --- 1. CORE SCRAPING BRAIN ---

def extract_email(text):
    """Hunter for finding emails in search snippets."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not Found"

def fetch_data(query, api_key, search_type="search", num_results=20):
    """Talks to Serper API to get clean data."""
    url = f"https://google.serper.dev/{search_type}"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=20)
        return response.json()
    except Exception:
        return {}

def parse_leads(data, source_label, mode="organic"):
    """Turns raw JSON into a clean lead list."""
    leads = []
    
    if mode == "organic":
        for result in data.get('organic', []):
            snippet = result.get('snippet', '')
            # Regex for Indian Mobile Numbers (6-9 followed by 9 digits)
            phone = re.search(r'[6-9]\d{9}', snippet)
            email = extract_email(snippet)
            
            if phone:
                leads.append({
                    "Business Name": result.get('title', 'Unknown'),
                    "Phone": phone.group(),
                    "Email": email,
                    "Source": source_label,
                    "Action": f"https://wa.me/91{phone.group()}"
                })
    
    elif mode == "maps":
        for result in data.get('places', []):
            phone = result.get('phoneNumber')
            if phone:
                # Clean the phone number string
                clean_phone = re.sub(r'\D', '', phone)[-10:]
                leads.append({
                    "Business Name": result.get('title'),
                    "Phone": clean_phone,
                    "Email": "Check Website", # Maps API rarely shows email directly
                    "Source": "Google Maps",
                    "Action": f"https://wa.me/91{clean_phone}"
                })
    return leads

# --- 2. USER INTERFACE (DASHBOARD) ---

st.set_page_config(page_title="Nuera Lead Scraber Pro", layout="wide", page_icon="🚀")

# Simple Login Logic
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Nuera SaaS Login")
    pass_input = st.text_input("Enter Access Code", type="password")
    if st.button("Unlock Dashboard"):
        if pass_input == "Salem123": # You can change this password anytime
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code. Please contact admin.")
    st.stop()

# Main App Header
st.title("🚀 Nuera Lead Scraber Pro")
st.subheader("Extract B2B Leads from Google Maps, Social Media & JustDial")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ API Configuration")
    api_key = st.text_input("Serper API Key", value="7ab11ec8c0050913c11a96062dc1e295af9743f0", type="password")
    
    st.divider()
    st.header("🔍 Search Parameters")
    industry = st.text_input("Business Category", "Dentist")
    city = st.text_input("Location/City", "Salem")
    
    st.divider()
    target_source = st.selectbox(
        "Target Platform",
        ["Google Maps", "Facebook", "Instagram", "LinkedIn", "JustDial", "Multi-Social Scan"]
    )
    
    limit = st.slider("Target Lead Count", 10, 100, 40)
    
    run_btn = st.button("🚀 Start Extraction", use_container_width=True)

# --- 3. EXECUTION LOGIC ---

if run_btn:
    if not api_key:
        st.error("API Key is missing!")
    else:
        with st.spinner(f"Scraping {industry} leads in {city}..."):
            final_leads = []
            
            if target_source == "Google Maps":
                raw = fetch_data(f"{industry} in {city}", api_key, "maps", limit)
                final_leads = parse_leads(raw, "Maps", "maps")
            
            elif target_source == "Multi-Social Scan":
                for site in ["facebook.com", "instagram.com", "linkedin.com"]:
                    q = f'site:{site} "{industry}" "{city}" "+91"'
                    raw = fetch_data(q, api_key, "search", limit//3)
                    final_leads += parse_leads(raw, site.split('.')[0].capitalize(), "organic")
            
            else:
                # Custom site search (JustDial, LinkedIn, etc.)
                site_map = {
                    "JustDial": "justdial.com",
                    "LinkedIn": "linkedin.com",
                    "Facebook": "facebook.com",
                    "Instagram": "instagram.com"
                }
                domain = site_map[target_source]
                q = f'site:{domain} "{industry}" "{city}" "+91"'
                raw = fetch_data(q, api_key, "search", limit)
                final_leads = parse_leads(raw, target_source, "organic")

            # --- DISPLAY RESULTS ---
            if final_leads:
                df = pd.DataFrame(final_leads).drop_duplicates(subset=['Phone'])
                
                # Show Stats
                col1, col2 = st.columns(2)
                col1.metric("Total Leads Found", len(df))
                col2.metric("Emails Captured", len(df[df['Email'] != "Not Found"]))
                
                st.dataframe(
                    df, 
                    column_config={"Action": st.column_config.LinkColumn("WhatsApp")},
                    use_container_width=True
                )
                
                # Download Option
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Lead Database (CSV)",
                    data=csv,
                    file_name=f"{industry}_{city}_leads.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No leads found. Try broadening your keywords or check your API credits.")
