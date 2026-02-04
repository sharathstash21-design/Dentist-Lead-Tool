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
    
    # FORCING GOOGLE MAPS ENGINE ONLY - This stops the Maharashtra jumping
    params = {
        "engine": "google_maps",
        "q": query,
        "location": location_query, 
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "google_domain": "google.co.in",
        "start": offset
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', [])
    except: return []

# --- 2. THE UI ---
st.title("🎯 Nuera Location-Locked Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    method = st.radio("Target Method", ["PIN Code Mode", "City/District Mode"])
    st.divider()

    industry = st.text_input("Business Category", value=st.session_state.get('sniping_category', "Hospital"))

    if method == "PIN Code Mode":
        pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
        pages_to_scan = st.number_input("Pages per PIN", 1, 5, 1)
        targets = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        total_cost = len(targets) * pages_to_scan
    else:
        # CITY MODE - Strict Location Lock
        st.subheader("📍 Target Area")
        city = st.text_input("District / City", value="Namakkal")
        state = st.text_input("State", value="Tamil Nadu")
        full_loc = f"{city}, {state}, India"
        pages_to_scan = st.number_input("Total Pages", 1, 5, 1)
        total_cost = 2 * pages_to_scan
        targets = [city]

    st.divider()
    if len(targets) > 0:
        st.info(f"📊 **Cost:** {total_cost} Credits")
        if st.session_state.user_credits < total_cost:
            st.error("⚠️ Low Balance!")
            start_btn = st.button("🚀 Start Sniper", disabled=True)
        else:
            start_btn = st.button("🚀 Start Sniper", use_container_width=True)
    else:
        start_btn = st.button("🚀 Start Sniper", disabled=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping...", expanded=True) as status:
        all_temp_leads = []
        
        for t in targets:
            # We create a specific lock for every scan
            lock = f"{t}, Tamil Nadu, India" if method == "PIN Code Mode" else full_loc
            
            for page in range(pages_to_scan):
                status.write(f"🛰️ Scanning {t} | Page {page+1}...")
                raw_items = fetch_precious_data(f"{industry} {t}", api_key_val, page, lock)
                
                for item in raw_items:
                    addr = item.get('address', '')
                    phone = item.get('phone') or item.get('phone_number')
                    
                    # --- THE "MAHARASHTRA BLOCKER" ---
                    # Check if the target state is actually in the address
                    target_state = "Tamil Nadu" if method == "PIN Code Mode" else state
                    
                    if phone and (target_state.lower() in addr.lower()):
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
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label=f"🎯 Success! {len(df_final)} local leads found.", state="complete")
        else:
            status.update(label="❌ No local leads found. Google restricted this area.", state="error")

# --- 4. DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ {len(df)} Leads Ready!")

    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)

    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=row['Name']).add_to(m)
        st_folium(m, width=700, height=400)

    st.download_button("📥 Download", df.to_csv(index=False).encode('utf-8'), "leads.csv")
