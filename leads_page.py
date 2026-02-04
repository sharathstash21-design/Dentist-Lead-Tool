import streamlit as st
import pandas as pd
import re
import requests
import json
import time
import folium
from streamlit_folium import st_folium

# --- 1. BRIDGE CONFIG ---
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

def deduct_remote_credit(email, amount=1):
    try:
        for _ in range(amount):
            requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=10)
        return True
    except: return False

def fetch_precious_data(query, api_key, page_num=1):
    url = "https://www.searchapi.io/api/v1/search"
    
    # EXACT PARAMETERS FROM OFFICIAL DOCS
    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "page": page_num  # Documentation says use 'page' for Google Maps
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        
        # Check if API returned an error message
        if "error" in data:
            st.error(f"⚠️ API Error: {data['error']}")
            return []
            
        return data.get('local_results', [])
    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        return []

# --- 2. THE UI ---
st.title("🎯 Nuera Google Maps Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    industry = st.text_input("Business Category", value="Hospital")
    city = st.text_input("District / City", value="Namakkal")
    state = st.text_input("State", value="Tamil Nadu")
    
    pages_to_scan = st.number_input("Total Pages (1 page = 20 leads)", 1, 5, 1)
    total_cost = 2 * pages_to_scan

    st.divider()
    if st.session_state.user_credits < total_cost:
        st.error(f"⚠️ Low Balance! (Need {total_cost}, Have {st.session_state.user_credits})")
        start_btn = st.button("🚀 Start Sniper", disabled=True)
    else:
        start_btn = st.button("🚀 Start Sniper", use_container_width=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping...", expanded=True) as status:
        all_temp_leads = []
        
        # Build the exact query Google Maps likes
        full_query = f"{industry} in {city}, {state}, India"
        
        for p in range(1, pages_to_scan + 1):
            status.write(f"🛰️ Scanning Page {p}...")
            raw_items = fetch_precious_data(full_query, api_key_val, p)
            
            if not raw_items:
                status.write(f"⚠️ No more results on page {p}")
                break

            for item in raw_items:
                phone = item.get('phone')
                addr = item.get('address', '')
                
                # Filter: Must have a phone AND be in the right City/State
                if phone and (city.lower() in addr.lower() or state.lower() in addr.lower()):
                    gps = item.get('gps_coordinates', {})
                    all_temp_leads.append({
                        "Name": item.get('title', 'Unknown'),
                        "Rating": item.get('rating', 0),
                        "Phone": re.sub(r'\D', '', str(phone))[-10:],
                        "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone))[-10:]}",
                        "Address": addr,
                        "Website": item.get('website', 'N/A'),
                        "lat": gps.get('latitude'),
                        "lng": gps.get('longitude')
                    })
            time.sleep(1)

        if all_temp_leads:
            df_final = pd.DataFrame(all_temp_leads).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            
            # Finalize payment
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label=f"🎯 Success! {len(df_final)} leads saved.", state="complete")
        else:
            status.update(label="❌ No leads found.", state="error")

# --- 4. DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ {len(df)} Leads Ready!")
    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    
    # Map and Download logic
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Name']).add_to(m)
        st_folium(m, width=700, height=400)
        
    st.download_button("📥 Download", df.to_csv(index=False).encode('utf-8'), "leads.csv")
