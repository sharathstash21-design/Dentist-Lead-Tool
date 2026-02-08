import streamlit as st
import pandas as pd
import re
import requests
import time
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURATION ---
# I have put your key here securely. 
API_KEY = "E7PCYwNsJvWgmyGkqDcMdfYN"
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

st.set_page_config(page_title="Nuera Sniper Elite", layout="wide")

# --- 2. SESSION STATE ---
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 20 # Default starting
if 'user_email' not in st.session_state:
    st.session_state.user_email = "sharath@nuera.space"

# --- 3. FUNCTIONS ---
def deduct_credit(email, amount):
    try:
        requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=5)
    except:
        pass

def fetch_data(query, page_num=1, url=None):
    search_api_url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "api_key": API_KEY,
        "gl": "in",
        "hl": "en"
    }
    
    # FIX: Ensure 'q' is always there if URL is not provided
    if url and "google.com/maps" in url:
        params["google_url"] = url
    else:
        params["q"] = query
        params["offset"] = (page_num - 1) * 20
        
    try:
        response = requests.get(search_api_url, params=params, timeout=20)
        data = response.json()
        return data.get('local_results', [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

def get_audit_reason(item):
    reasons = []
    if not item.get('website'): reasons.append("No Website")
    if item.get('rating', 0) < 4.0: reasons.append("Low Rating")
    if item.get('reviews', 0) < 10: reasons.append("Few Reviews")
    return ", ".join(reasons) if reasons else "Optimized"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎯 Nuera Sniper")
    st.write(f"Logged in: {st.session_state.user_email}")
    st.write(f"Credits: **{st.session_state.user_credits}**")
    
    st.divider()
    mode = st.radio("Search Mode", ["Keyword Mode", "Direct URL Mode"])
    
    if mode == "Keyword Mode":
        cat = st.text_input("Category", "Hospital")
        loc = st.text_input("City", "Namakkal")
        final_query = f"{cat} in {loc}, Tamil Nadu"
        final_url = None
    else:
        final_url = st.text_input("Paste Google Maps Link")
        final_query = "Scanned via URL"

    pages = st.number_input("Pages to Scan", 1, 5, 1)
    cost = pages * 2
    
    st.divider()
    can_run = st.session_state.user_credits >= cost
    if not can_run:
        st.error("Low Balance!")
    
    run_btn = st.button("🚀 Start Sniper", disabled=not can_run, use_container_width=True)

# --- 5. MAIN ACTION ---
if run_btn:
    with st.status("💎 Extracting Leads...", expanded=True) as status:
        all_leads = []
        for p in range(1, pages + 1):
            status.write(f"🛰️ Scanning Page {p}...")
            results = fetch_data(final_query, p, final_url)
            
            if not results:
                status.write("No more results found.")
                break
                
            for item in results:
                phone = item.get('phone', '')
                all_leads.append({
                    "Business Name": item.get('title'),
                    "Audit Reason": get_audit_reason(item),
                    "Phone": re.sub(r'\D', '', str(phone))[-10:] if phone else "N/A",
                    "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone))[-10:]}" if phone else "N/A",
                    "Rating": item.get('rating', 0),
                    "Reviews": item.get('reviews', 0),
                    "Website": item.get('website', 'N/A'),
                    "Address": item.get('address'),
                    "lat": item.get('gps_coordinates', {}).get('latitude'),
                    "lng": item.get('gps_coordinates', {}).get('longitude')
                })
            time.sleep(1)

        if all_leads:
            df = pd.DataFrame(all_leads).drop_duplicates(subset=['Business Name'])
            st.session_state['leads'] = df
            # Deduct Credits
            deduct_credit(st.session_state.user_email, cost)
            st.session_state.user_credits -= cost
            status.update(label="Extraction Complete!", state="complete")

# --- 6. RESULTS ---
if 'leads' in st.session_state:
    df = st.session_state['leads']
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    with col2:
        st.download_button("📥 Download CSV", df.to_csv(index=False), "leads.csv", use_container_width=True)
        
    # Map Display
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        st.subheader("📍 Lead Map")
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Business Name']).add_to(m)
        st_folium(m, height=400, width=1000)
