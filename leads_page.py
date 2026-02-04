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
        # Deduct multiple credits if scanning multiple pages/PINs
        for _ in range(amount):
            requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=10)
        return True
    except: return False

def fetch_precious_data(query, pin, api_key, page_num=0):
    url = "https://www.searchapi.io/api/v1/search"
    # Logic: Start at 0, then 20, then 40 for next pages
    offset = page_num * 20 
    
    params = {
        "engine": "google_maps",
        "q": f"{query} {pin} India",
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "start": offset # This tells Google to go to the NEXT PAGE
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', data.get('local_results', []))
    except: return []

# --- 2. THE UI & SIDEBAR ---
st.title("🎯 Nuera Multi-Page Lead Sniper")

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Hospital"))
    pin_input = st.text_area("Target PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    
    # --- NEXT PAGE CONTROL ---
    pages_to_scan = st.number_input("Pages per PIN (1 page = ~20 leads)", min_value=1, max_value=5, value=1)
    
    pins_list = [p.strip() for p in pin_input.replace("\n", ",").split(",") if p.strip()]
    num_pins = len(pins_list)
    total_cost = num_pins * pages_to_scan # Charge per page scanned

    st.divider()
    if num_pins > 0:
        st.info(f"📊 **Plan:**\n- PINs: {num_pins}\n- Depth: {pages_to_scan} Pages\n- Cost: {total_cost} Credits")
        if st.session_state.user_credits < total_cost:
            st.error("⚠️ Insufficient Credits!")
            start_btn = st.button("🚀 Start Deep Extraction", disabled=True)
        else:
            start_btn = st.button("🚀 Start Deep Extraction", use_container_width=True)
    else:
        st.warning("Enter PINs first.")
        start_btn = st.button("🚀 Start Deep Extraction", disabled=True)

# --- 3. EXTRACTION ACTION ---
if start_btn:
    with st.status("💎 Deep Sniping in Progress...", expanded=True) as status:
        all_temp_leads = []
        
        for pin in pins_list:
            for page in range(pages_to_scan):
                status.write(f"🛰️ Scanning {pin} | Page {page+1}...")
                raw_items = fetch_precious_data(industry, pin, api_key_val, page)
                
                if not raw_items:
                    status.write(f"⚠️ No more results on Page {page+1}")
                    break # Stop if a page is empty
                
                for rank, item in enumerate(raw_items, 1):
                    address = item.get('address', 'N/A')
                    phone_raw = item.get('phone') or item.get('phone_number')
                    
                    if phone_raw and (pin in address):
                        gps = item.get('gps_coordinates', {})
                        all_temp_leads.append({
                            "PIN": pin,
                            "Name": item.get('title', 'Unknown'),
                            "Rating": item.get('rating', 0),
                            "Phone": re.sub(r'\D', '', str(phone_raw))[-10:],
                            "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone_raw))[-10:]}",
                            "Website": item.get('website', 'Not Available'),
                            "Address": address,
                            "lat": gps.get('latitude'),
                            "lng": gps.get('longitude')
                        })
                time.sleep(1) # Small delay to be safe

        if all_temp_leads:
            df_final = pd.DataFrame(all_temp_leads).drop_duplicates(subset=['Phone'])
            st.session_state['last_extracted_leads'] = df_final
            
            # DEDUCT TOTAL COST
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label=f"🎯 Done! Found {len(df_final)} leads.", state="complete")
        else:
            status.update(label="❌ No matches found.", state="error")

# --- 4. DISPLAY LOGIC ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    st.success(f"✅ Total {len(df)} Leads Ready!")

    # Table
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
