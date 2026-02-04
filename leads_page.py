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

def fetch_precious_data(query, api_key, page_num=0, location_query=None):
    url = "https://www.searchapi.io/api/v1/search"
    offset = page_num * 20 
    
    # TRIPLE LOCK: City + State + Country
    params = {
        "engine": "google_maps",
        "q": query,
        "location": location_query, # e.g., "Namakkal, Tamil Nadu, India"
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "google_domain": "google.co.in",
        "start": offset
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', data.get('local_results', []))
    except: return []

# --- 2. THE UI & SIDEBAR ---
st.title("🎯 Nuera Precise Location Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    method = st.radio("Extraction Method", ["PIN Code Mode", "URL / City Mode"])
    st.divider()

    industry = st.text_input("Business Category", value=st.session_state.get('sniping_category', "Hospital"))

    if method == "PIN Code Mode":
        pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
        pages_to_scan = st.number_input("Pages per PIN", min_value=1, max_value=5, value=1)
        pins_list = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        total_cost = len(pins_list) * pages_to_scan
    else:
        # URL / City Mode - We ask for the location details here
        st.subheader("📍 Location Lock")
        city = st.text_input("District / City", value="Namakkal")
        state = st.text_input("State", value="Tamil Nadu")
        country = st.text_input("Country", value="India")
        full_loc = f"{city}, {state}, {country}"
        
        target_url = st.text_area("Google Maps URL (Optional)", placeholder="Paste link here if you have one...")
        pages_to_scan = st.number_input("Total Pages", min_value=1, max_value=5, value=1)
        total_cost = 2 * pages_to_scan

    st.divider()
    can_proceed = (method == "PIN Code Mode" and len(pins_list) > 0) or (method == "URL / City Mode" and city)
    
    if can_proceed:
        st.info(f"📊 **Cost:** {total_cost} Credits")
        if st.session_state.user_credits < total_cost:
            st.error("⚠️ Low Balance!")
            start_btn = st.button("🚀 Start Sniper", disabled=True)
        else:
            start_btn = st.button("🚀 Start Sniper", use_container_width=True)
    else:
        st.warning("Input Required")
        start_btn = st.button("🚀 Start Sniper", disabled=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping...", expanded=True) as status:
        all_temp_leads = []
        
        if method == "PIN Code Mode":
            for pin in pins_list:
                loc_lock = f"{pin}, Tamil Nadu, India"
                for page in range(pages_to_scan):
                    status.write(f"🛰️ Scanning PIN {pin} | Page {page+1}...")
                    raw_items = fetch_precious_data(f"{industry} {pin}", api_key_val, page, loc_lock)
                    for item in raw_items:
                        if pin in item.get('address', ''): # Strict Check
                            all_temp_leads.append(item)
        else:
            for page in range(pages_to_scan):
                status.write(f"📡 Scanning {city} | Page {page+1}...")
                # We use the full City/State/Country lock here
                raw_items = fetch_precious_data(industry, api_key_val, page, full_loc)
                all_temp_leads += raw_items

        if all_temp_leads:
            formatted = []
            for item in all_temp_leads:
                phone_raw = item.get('phone') or item.get('phone_number')
                if phone_raw:
                    gps = item.get('gps_coordinates', {})
                    formatted.append({
                        "Name": item.get('title', 'Unknown'),
                        "Rating": item.get('rating', 0),
                        "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                        "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}",
                        "Address": item.get('address', 'N/A'),
                        "Website": item.get('website', 'N/A'),
                        "lat": gps.get('latitude'),
                        "lng": gps.get('longitude')
                    })
            
            df_final = pd.DataFrame(formatted).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label="🎯 Extraction Done!", state="complete")
        else:
            status.update(label="❌ No leads found.", state="error")

# --- 4. DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ {len(df)} Leads found in {city if method != 'PIN Code Mode' else 'PIN Zone'}")

    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)

    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Name']).add_to(m)
        st_folium(m, width=700, height=400)

    st.download_button("📥 Download", df.to_csv(index=False).encode('utf-8'), "leads.csv")
