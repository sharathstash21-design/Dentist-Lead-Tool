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

def fetch_precious_data(query, pin, api_key, target_source):
    url = "https://www.searchapi.io/api/v1/search"
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
        return data.get('places', data.get('local_results', [])) if is_maps else data.get('organic_results', [])
    except: return []

# --- 2. THE UI & SIDEBAR ---
st.title("🎯 Nuera Precious Lead Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    # Auto-fill from Map Page if available
    default_industry = st.session_state.get('sniping_category', "Hotel")
    default_pins = st.session_state.get('sniping_pincodes', "")
    
    industry = st.text_input("Business Type", value=default_industry)
    pin_input = st.text_area("Target PIN Codes", value=default_pins, help="Enter PINs separated by commas")
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])
    
    # --- 3. DYNAMIC CREDIT PREVIEW ---
    pins_list = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    num_pins = len(pins_list)
    
    st.divider()
    if num_pins > 0:
        st.info(f"📊 **Extraction Plan**\n- PINs detected: {num_pins}\n- Cost: {num_pins} Credits")
        
        if st.session_state.user_credits < num_pins:
            st.error(f"⚠️ Low Credits! You need {num_pins} but have {st.session_state.user_credits}.")
            start_btn = st.button("🚀 Start Strict Extraction", disabled=True)
        else:
            st.success(f"✅ Balance OK ({st.session_state.user_credits} avail)")
            start_btn = st.button("🚀 Start Strict Extraction", use_container_width=True)
    else:
        st.warning("Please capture/enter PINs to calculate cost.")
        start_btn = st.button("🚀 Start Strict Extraction", disabled=True)

# --- 4. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping Leads...", expanded=True) as status:
        temp_leads = []
        
        for pin in pins_list:
            status.write(f"🛰️ Scanning PIN: {pin}...")
            raw_items = fetch_precious_data(industry, pin, api_key_val, target_src)
            
            for rank, item in enumerate(raw_items, 1):
                address = item.get('address', 'N/A')
                phone_raw = item.get('phone') or item.get('phone_number')
                
                # STRICT PIN FILTER
                if phone_raw and (pin in address):
                    gps = item.get('gps_coordinates', {})
                    temp_leads.append({
                        "PIN": pin,
                        "Name": item.get('title', 'Unknown'),
                        "Rating": item.get('rating', 0),
                        "Reviews": item.get('reviews', 0),
                        "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                        "Website": item.get('website', 'Not Available'),
                        "Address": address,
                        "lat": gps.get('latitude'),
                        "lng": gps.get('longitude'),
                        "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}"
                    })

        if temp_leads:
            # SAVE TO MEMORY
            df_final = pd.DataFrame(temp_leads).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            
            # SYNC CREDITS (1 Credit per PIN)
            status.write(f"💳 Finalizing Payment for {num_pins} PINs...")
            for _ in range(num_pins):
                deduct_remote_credit(st.session_state.user_email)
            
            st.session_state.user_credits -= num_pins
            status.update(label="🎯 Extraction Successful!", state="complete")
        else:
            status.update(label="❌ No Strict Matches Found", state="error")
            st.info("Try moving the map circle to a different area or check your SearchAPI balance.")

# --- 5. PERMANENT DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    
    st.success(f"✅ Total {len(df)} Strict Leads Extracted!")
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Leads Found", len(df))
    # Safe mean calculation
    avg_r = round(pd.to_numeric(df['Rating'], errors='coerce').mean(), 1) if not df.empty else 0
    m2.metric("Avg Rating", f"{avg_r} ⭐")
    m3.metric("Your Balance", st.session_state.user_credits)

    # Map View
    st.subheader("📍 Precise Location Map")
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            color = "blue" if row['Rating'] >= 4 else "red"
            folium.Marker(
                [row['lat'], row['lng']], 
                popup=f"<b>{row['Name']}</b><br>{row['Phone']}",
                icon=folium.Icon(color=color)
            ).add_to(m)
        st_folium(m, width=700, height=400)

    # Data Table
    st.divider()
    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    
    # Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Precious Leads", csv, "nuera_leads.csv", "text/csv")
