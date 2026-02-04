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
st.write("Strict Extraction: Only leads matching your PIN will be saved.")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Hotel"))
    pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])
    start_btn = st.button("🚀 Start Strict Extraction", use_container_width=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    if st.session_state.user_credits <= 0:
        st.error("🚫 Out of credits!")
    elif not pin_input:
        st.warning("⚠️ Please enter or capture PINs first!")
    else:
        # Convert text input into a list of PINs
        pins = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        
        with st.status("💎 Sniping Leads...", expanded=True) as status:
            temp_leads = []
            for pin in pins:
                status.write(f"🛰️ Scanning PIN: {pin}...")
                raw_items = fetch_precious_data(industry, pin, api_key_val, target_src)
                
                for rank, item in enumerate(raw_items, 1):
                    address = item.get('address', 'N/A')
                    phone_raw = item.get('phone') or item.get('phone_number')
                    
                    # --- THE DISTRICT SHIELD (STRICT FILTER) ---
                    # Only accept if the lead has a phone AND the PIN matches the address
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
                # Deduplicate based on phone number
                final_df = pd.DataFrame(temp_leads).drop_duplicates(subset=['Phone'])
                st.session_state['last_extracted_leads'] = final_df
                
                # Deduct from Google Sheets
                deduct_remote_credit(st.session_state.user_email)
                st.session_state.user_credits -= 1
                status.update(label="🎯 Extraction Complete!", state="complete")
            else:
                status.update(label="❌ No Strict Matches Found", state="error")
                st.info(f"No businesses found physically located in PIN {pin_input}.")

# --- 4. DISPLAY LOGIC (Permanent View) ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    
    st.success(f"✅ Extracted {len(df)} Strict Leads!")
    
    # Quick Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Leads", len(df))
    c2.metric("Nearby Competition", f"{df['Rating'].mean():.1f} ⭐")
    c3.metric("Remaining Credits", st.session_state.user_credits)

    # Interactive Map
    st.subheader("📍 Precise Location Map")
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        # Center map on the first lead
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=13)
        for _, row in valid_map.iterrows():
            folium.Marker(
                [row['lat'], row['lng']], 
                popup=f"<b>{row['Name']}</b><br>Rating: {row['Rating']}",
                tooltip=row['Name']
            ).add_to(m)
        st_folium(m, width=700, height=400)

    # Lead Table
    st.divider()
    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    
    # Export Option
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Precious Leads (CSV)", csv, "nuera_leads.csv", "text/csv")
