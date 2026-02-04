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

def fetch_precious_data(query, pin, api_key, page_num=0, search_url=None):
    url = "https://www.searchapi.io/api/v1/search"
    offset = page_num * 20 
    
    # Common settings to FORCE INDIA
    params = {
        "engine": "google_maps",
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "google_domain": "google.co.in",
        "start": offset
    }

    if search_url:
        # URL MODE: Uses the raw URL but forces India location params
        params["q"] = query
        # Note: SearchAPI allows passing a URL directly in some engines, 
        # but 'q' with local domain is more stable for India results.
    else:
        # PIN MODE
        params["q"] = f"{query} {pin} India"
    
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', data.get('local_results', []))
    except: return []

# --- 2. THE UI & SIDEBAR ---
st.title("🎯 Nuera Dual-Engine Deep Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    # --- METHOD SELECTION ---
    method = st.radio("Extraction Method", ["PIN Code Mode", "Google URL Mode"])
    st.divider()

    industry = st.text_input("Business Category", value=st.session_state.get('sniping_category', "Hospital"))

    if method == "PIN Code Mode":
        pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
        pages_to_scan = st.number_input("Pages per PIN (1 page ≈ 20 leads)", min_value=1, max_value=5, value=1)
        pins_list = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
        total_cost = len(pins_list) * pages_to_scan
    else:
        target_url = st.text_area("Paste Google Maps/Search URL", placeholder="Paste the Namakkal link here...")
        pages_to_scan = st.number_input("How many pages to deep-scan?", min_value=1, max_value=5, value=1)
        total_cost = 2 * pages_to_scan # URL mode is 2 credits per page

    st.divider()
    # Logic to enable/disable button
    can_proceed = (method == "PIN Code Mode" and len(pins_list) > 0) or (method == "Google URL Mode" and target_url)
    
    if can_proceed:
        st.info(f"📊 **Plan:** {method}\n- Cost: {total_cost} Credits")
        if st.session_state.user_credits < total_cost:
            st.error("⚠️ Insufficient Credits!")
            start_btn = st.button("🚀 Start Deep Extraction", disabled=True)
        else:
            start_btn = st.button("🚀 Start Deep Extraction", use_container_width=True)
    else:
        st.warning("Awaiting Input Data...")
        start_btn = st.button("🚀 Start Deep Extraction", disabled=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Sniping in Progress...", expanded=True) as status:
        all_temp_leads = []
        
        # Loop for PIN Mode
        targets = pins_list if method == "PIN Code Mode" else [None]
        
        for t in targets:
            for page in range(pages_to_scan):
                label = f"PIN {t}" if t else "URL Scan"
                status.write(f"🛰️ {label} | Page {page+1}...")
                
                raw_items = fetch_precious_data(
                    industry, t, api_key_val, 
                    page_num=page, 
                    search_url=target_url if method == "Google URL Mode" else None
                )
                
                if not raw_items:
                    break
                
                for item in raw_items:
                    address = item.get('address', 'N/A')
                    phone_raw = item.get('phone') or item.get('phone_number')
                    
                    # Apply Strict PIN filter ONLY in PIN Mode
                    is_valid = True
                    if method == "PIN Code Mode" and t not in address:
                        is_valid = False
                    
                    if phone_raw and is_valid:
                        gps = item.get('gps_coordinates', {})
                        all_temp_leads.append({
                            "Name": item.get('title', 'Unknown'),
                            "Rating": item.get('rating', 0),
                            "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                            "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}",
                            "Address": address,
                            "Website": item.get('website', 'N/A'),
                            "lat": gps.get('latitude'),
                            "lng": gps.get('longitude')
                        })
                time.sleep(1)

        if all_temp_leads:
            df_final = pd.DataFrame(all_temp_leads).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            
            # SYNC CREDITS
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label=f"🎯 Success! {len(df_final)} leads saved.", state="complete")
        else:
            status.update(label="❌ No leads found.", state="error")

# --- 4. DISPLAY LOGIC ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ {len(df)} Leads Ready!")

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

    st.download_button("📥 Download Excel", df.to_csv(index=False).encode('utf-8'), "nuera_leads.csv")
