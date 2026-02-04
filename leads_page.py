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

def deduct_remote_credit(email):
    try:
        requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=10)
        return True
    except: return False

def fetch_precious_data(query, pin, api_key, target_source, search_url=None):
    url = "https://www.searchapi.io/api/v1/search"
    
    # If URL Mode is used, we send the URL directly to the API
    if search_url:
        params = {
            "engine": "google_maps",
            "google_domain": "google.co.in",
            "q": query, # The API uses the query to refine URL results
            "api_key": api_key
        }
    else:
        # Standard PIN Mode
        is_maps = (target_source == "Google Maps")
        params = {
            "engine": "google_maps" if is_maps else "google",
            "q": f"{query} {pin} India",
            "api_key": api_key,
            "gl": "in"
        }
        
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', data.get('local_results', []))
    except: return []

# --- 2. THE UI & SIDEBAR ---
st.title("🎯 Nuera Dual-Engine Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Configuration")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    # --- NEW: CHOOSE YOUR ATTACK METHOD ---
    method = st.radio("Select Extraction Method", ["PIN Code Mode", "Google URL Mode"])
    st.divider()

    industry = st.text_input("Business Category", value=st.session_state.get('sniping_category', "Hospital"))

    if method == "PIN Code Mode":
        pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
        target_src = st.selectbox("Search Source", ["Google Maps", "Google Search"])
        pins_list = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        cost = len(pins_list)
    else:
        target_url = st.text_area("Paste Google Search URL", placeholder="Paste the long Google Maps link here...")
        st.info("URL Mode costs 2 credits per deep scan.")
        cost = 2

    st.divider()
    # Credit Check Logic
    if (method == "PIN Code Mode" and len(pins_list) > 0) or (method == "Google URL Mode" and target_url):
        st.info(f"📊 **Plan:** {method}\n- Cost: {cost} Credits")
        if st.session_state.user_credits < cost:
            st.error("⚠️ Insufficient Credits!")
            start_btn = st.button("🚀 Start Extraction", disabled=True)
        else:
            start_btn = st.button("🚀 Start Extraction", use_container_width=True)
    else:
        st.warning("Awaiting Input...")
        start_btn = st.button("🚀 Start Extraction", disabled=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping Leads...", expanded=True) as status:
        temp_leads = []
        
        if method == "PIN Code Mode":
            for pin in pins_list:
                status.write(f"🛰️ Scanning PIN: {pin}...")
                raw_items = fetch_precious_data(industry, pin, api_key_val, target_src)
                for item in raw_items:
                    address = item.get('address', 'N/A')
                    phone = item.get('phone') or item.get('phone_number')
                    if phone and (pin in address): # Strict Filter
                        temp_leads.append(item)
        else:
            status.write("📡 Extracting from URL...")
            # For URL mode, we pass the data differently
            raw_items = fetch_precious_data(industry, None, api_key_val, None, search_url=target_url)
            temp_leads = raw_items

        if temp_leads:
            # Format results
            formatted_leads = []
            for item in temp_leads:
                phone_raw = item.get('phone') or item.get('phone_number')
                if phone_raw:
                    gps = item.get('gps_coordinates', {})
                    formatted_leads.append({
                        "Name": item.get('title', 'Unknown'),
                        "Rating": item.get('rating', 0),
                        "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                        "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}",
                        "Address": item.get('address', 'N/A'),
                        "Website": item.get('website', 'N/A'),
                        "lat": gps.get('latitude'),
                        "lng": gps.get('longitude')
                    })
            
            df_final = pd.DataFrame(formatted_leads).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            
            # Sync Credits
            for _ in range(cost):
                deduct_remote_credit(st.session_state.user_email)
            st.session_state.user_credits -= cost
            status.update(label=f"🎯 Success! {len(df_final)} Leads found.", state="complete")
        else:
            status.update(label="❌ No Leads Extracted", state="error")

# --- 4. PERMANENT DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ {len(df)} Leads Ready for Business!")

    st.dataframe(
        df.drop(columns=['lat', 'lng']), 
        use_container_width=True,
        column_config={
            "WhatsApp": st.column_config.LinkColumn("Chat"),
            "Website": st.column_config.LinkColumn("Visit")
        }
    )
    
    # Map
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Name']).add_to(m)
        st_folium(m, width=700, height=400)

    st.download_button("📥 Download Excel/CSV", df.to_csv(index=False).encode('utf-8'), "nuera_leads.csv")
