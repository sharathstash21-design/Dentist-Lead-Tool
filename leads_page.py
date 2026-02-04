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

# --- 2. THE UI ---
st.title("🎯 Nuera Precious Lead Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Dentist"))
    pin_input = st.text_area("PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])
    start_btn = st.button("🚀 Start Precious Extraction", use_container_width=True)

# --- 3. THIS IS THE "ACTION PART" (What happens when you click) ---
if start_btn:
    if st.session_state.user_credits <= 0:
        st.error("🚫 Out of credits!")
    elif not pin_input:
        st.warning("⚠️ Please capture PINs first!")
    else:
        pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        
        with st.status("💎 Sniping Leads...", expanded=True) as status:
            temp_leads = []
            for pin in pins:
                status.write(f"🛰️ Checking PIN: {pin}...")
                raw_items = fetch_precious_data(industry, pin, api_key_val, target_src)
                
                for rank, item in enumerate(raw_items, 1):
                    phone_raw = item.get('phone') or item.get('phone_number')
                    if phone_raw:
                        gps = item.get('gps_coordinates', {})
                        temp_leads.append({
                            "Name": item.get('title', 'Unknown'),
                            "Rating": item.get('rating', 0),
                            "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                            "Website": item.get('website', 'Not Available'),
                            "Address": item.get('address', 'N/A'),
                            "lat": gps.get('latitude'),
                            "lng": gps.get('longitude'),
                            "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}"
                        })

            if temp_leads:
                # SAVE DATA TO MEMORY SO IT STAYS ON SCREEN
                st.session_state['last_extracted_leads'] = pd.DataFrame(temp_leads).drop_duplicates(subset=['Phone'])
                
                # DEDUCT CREDIT IN SHEET
                deduct_remote_credit(st.session_state.user_email)
                st.session_state.user_credits -= 1
                status.update(label="🎯 Extraction Successful!", state="complete")
            else:
                status.update(label="❌ No Leads Found", state="error")

# --- 4. DISPLAY LOGIC (This keeps the data visible!) ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    
    st.success(f"✅ Extracted {len(df)} Leads!")
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Found", len(df))
    c2.metric("No Website", len(df[df['Website'] == "Not Available"]))
    c3.metric("Avg Rating", f"{round(df['Rating'].astype(float).mean(), 1)} ⭐")

    # Map
    st.subheader("📍 Visual Lead Map")
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Name']).add_to(m)
        st_folium(m, width=700, height=400)

    # Table
    st.divider()
    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "leads.csv")
