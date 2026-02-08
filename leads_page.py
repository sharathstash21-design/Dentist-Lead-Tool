import streamlit as st
import pandas as pd
import re
import requests
import time
import folium
from streamlit_folium import st_folium

# --- 1. BRIDGE & API CONFIG ---
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"
API_KEY = "E7PCYwNsJvWgmyGkqDcMdfYN" # Akka secured it here for you

def deduct_remote_credit(email, amount=1):
    try:
        # Simplified for your fever-rest mode
        requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=5)
        return True
    except: return False

def fetch_precious_data(query, page_num=1, google_url=None):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "api_key": API_KEY,
        "gl": "in",
        "hl": "en"
    }
    
    # Logic fix: Use URL if provided, else use the keyword query
    if google_url:
        params["google_url"] = google_url
    else:
        params["q"] = query
        params["offset"] = (page_num - 1) * 20
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        if "error" in data:
            st.error(f"⚠️ API Error: {data['error']}")
            return []
        return data.get('local_results', [])
    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        return []

# --- 2. THE UI ---
st.set_page_config(page_title="Nuera Sniper", layout="wide")
st.title("🎯 Nuera Google Maps Sniper")

# Session state for credits
if 'user_credits' not in st.session_state: st.session_state.user_credits = 50 
if 'user_email' not in st.session_state: st.session_state.user_email = "sharath@nuera.space"

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    search_mode = st.radio("Search Mode", ["Keyword (Manual)", "Google Maps URL (Direct)"])
    
    if search_mode == "Keyword (Manual)":
        category = st.text_input("Category", "Hospital")
        city = st.text_input("City", "Namakkal")
        state = st.text_input("State", "Tamil Nadu")
        final_query = f"{category} in {city}, {state}"
        target_url = None
    else:
        target_url = st.text_input("Paste Google Maps URL")
        final_query = None

    pages = st.number_input("Pages", 1, 5, 1)
    cost = pages * 2
    
    st.write(f"Credits: {st.session_state.user_credits}")
    start_btn = st.button("🚀 Start Sniper", use_container_width=True)

# --- 3. ACTION ---
if start_btn:
    with st.status("🛰️ Scanning...", expanded=True) as status:
        all_leads = []
        
        # Decide search input
        search_input = target_url if search_mode == "Google Maps URL (Direct)" else final_query
        
        if not search_input:
            st.error("Missing Search Input!")
        else:
            for p in range(1, pages + 1):
                status.write(f"Scanning Page {p}...")
                results = fetch_precious_data(final_query, p, target_url)
                
                if not results: break
                
                for item in results:
                    # Basic Audit Logic (Omkar style)
                    has_web = "✅" if item.get('website') else "❌ No Website"
                    phone = item.get('phone', '')
                    
                    all_leads.append({
                        "Name": item.get('title'),
                        "Phone": re.sub(r'\D', '', str(phone))[-10:] if phone else "N/A",
                        "Audit": has_web,
                        "Rating": item.get('rating', 0),
                        "Reviews": item.get('reviews', 0),
                        "Address": item.get('address'),
                        "lat": item.get('gps_coordinates', {}).get('latitude'),
                        "lng": item.get('gps_coordinates', {}).get('longitude')
                    })
                time.sleep(1)

        if all_leads:
            df = pd.DataFrame(all_leads).drop_duplicates(subset=['Name'])
            st.session_state['last_leads'] = df
            deduct_remote_credit(st.session_state.user_email, cost)
            st.session_state.user_credits -= cost
            status.update(label="Sniping Complete!", state="complete")

# --- 4. DISPLAY ---
if 'last_leads' in st.session_state:
    df = st.session_state['last_leads']
    st.dataframe(df.drop(columns=['lat', 'lng']))
    
    # Simple Map
    valid = df.dropna(subset=['lat', 'lng'])
    if not valid.empty:
        m = folium.Map(location=[valid.iloc[0]['lat'], valid.iloc[0]['lng']], zoom_start=12)
        for _, r in valid.iterrows():
            folium.Marker([r['lat'], r['lng']], popup=r['Name']).add_to(m)
        st_folium(m, height=300)
    
    st.download_button("📥 Download", df.to_csv(index=False), "leads.csv")
