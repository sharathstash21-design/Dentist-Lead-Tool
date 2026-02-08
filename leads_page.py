import streamlit as st
import pandas as pd
import re
import requests
import json
import time
import folium
from streamlit_folium import st_folium
from collections import Counter

# --- 1. BRIDGE CONFIG ---
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

def deduct_remote_credit(email, amount=1):
    try:
        for _ in range(amount):
            requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=10)
        return True
    except: return False

def fetch_precious_data(api_key, query=None, google_url=None, page_num=1):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "api_key": api_key,
        "gl": "in",
        "hl": "en"
    }
    
    # POWER FEATURE: Handle direct URL or Keyword
    if google_url:
        params["google_url"] = google_url
    else:
        params["q"] = query
        params["offset"] = (page_num - 1) * 20  # offset is often safer for pagination
    
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

# --- 2. AUDIT LOGIC (The Omkar "Power") ---
def perform_audit(item):
    reasons = []
    score = 100
    
    if not item.get('website'):
        reasons.append("❌ No Website")
        score -= 30
    if item.get('rating', 0) < 4.0:
        reasons.append("📉 Low Rating")
        score -= 20
    if item.get('reviews', 0) < 15:
        reasons.append("⚠️ Few Reviews")
        score -= 20
    if not item.get('phone'):
        reasons.append("📵 No Phone")
        score -= 10
        
    status = "🔥 High Value Lead" if score < 70 else "✅ Optimized"
    return status, ", ".join(reasons) if reasons else "Perfect Profile", score

# --- 3. THE UI ---
st.title("🎯 Nuera Google Maps Sniper")

# Initialize session state for credits if not exists (for testing)
if 'user_credits' not in st.session_state: st.session_state.user_credits = 100
if 'user_email' not in st.session_state: st.session_state.user_email = "sharath@nuera.space"

with st.sidebar:
    st.header("⚙️ Sniper Settings")
    api_key_val = st.text_input("SearchAPI Key", value="E7PCYwNsJvWgmyGkqDcMdfYN", type="password")
    
    search_mode = st.radio("Search Mode", ["Keyword (Safe)", "Google Maps URL (Exact)"])
    
    if search_mode == "Keyword (Safe)":
        industry = st.text_input("Business Category", value="Hospital")
        city = st.text_input("District / City", value="Namakkal")
        state = st.text_input("State", value="Tamil Nadu")
        full_query = f"{industry} in {city}, {state}, India"
        target_url = None
    else:
        target_url = st.text_input("Paste Google Maps URL here")
        full_query = None

    pages_to_scan = st.number_input("Total Pages (1 page = 20 leads)", 1, 5, 1)
    total_cost = 2 * pages_to_scan
    st.divider()
    
    start_btn = st.button("🚀 Start Sniper", use_container_width=True, disabled=(st.session_state.user_credits < total_cost))

# --- 4. EXTRACTION ACTION ---
if start_btn:
    all_temp_leads = []
    with st.status("💎 Sniping...", expanded=True) as status:
        for p in range(1, pages_to_scan + 1):
            status.write(f"🛰️ Scanning Page {p}...")
            raw_items = fetch_precious_data(api_key_val, query=full_query, google_url=target_url, page_num=p)
            
            if not raw_items:
                status.write(f"⚠️ No more results on page {p}")
                break

            for item in raw_items:
                phone = item.get('phone')
                # Smart Audit logic
                audit_status, audit_reasons, health_score = perform_audit(item)
                
                gps = item.get('gps_coordinates', {})
                all_temp_leads.append({
                    "Name": item.get('title', 'Unknown'),
                    "Audit Status": audit_status,
                    "Health Score": f"{health_score}%",
                    "Weaknesses": audit_reasons,
                    "Phone": re.sub(r'\D', '', str(phone))[-10:] if phone else "N/A",
                    "WhatsApp": f"https://wa.me/91{re.sub(r'\D', '', str(phone))[-10:]}" if phone else "N/A",
                    "Rating": item.get('rating', 0),
                    "Reviews": item.get('reviews', 0),
                    "Website": item.get('website', 'N/A'),
                    "Address": item.get('address', ''),
                    "lat": gps.get('latitude'),
                    "lng": gps.get('longitude')
                })
            time.sleep(1)

        if all_temp_leads:
            df_final = pd.DataFrame(all_temp_leads).drop_duplicates(subset=['Name'])
            st.session_state['last_extracted_leads'] = df_final
            deduct_remote_credit(st.session_state.user_email, total_cost)
            st.session_state.user_credits -= total_cost
            status.update(label=f"🎯 Success! {len(df_final)} leads saved.", state="complete")

# --- 5. DISPLAY ---
if 'last_extracted_leads' in st.session_state:
    df = st.session_state['last_extracted_leads']
    
    # Filter only High Value Leads if user wants
    if st.checkbox("Show only High Value Leads (Low Health Score)"):
        df = df[df['Audit Status'] == "🔥 High Value Lead"]

    st.dataframe(df.drop(columns=['lat', 'lng']), use_container_width=True)
    
    # Map and Download
    valid_map = df.dropna(subset=['lat', 'lng'])
    if not valid_map.empty:
        m = folium.Map(location=[valid_map.iloc[0]['lat'], valid_map.iloc[0]['lng']], zoom_start=12)
        for _, row in valid_map.iterrows():
            folium.Marker([row['lat'], row['lng']], popup=f"{row['Name']} ({row['Health Score']})").add_to(m)
        st_folium(m, width=700, height=400)
        
    st.download_button("📥 Download Audited Leads", df.to_csv(index=False).encode('utf-8'), "nuera_leads.csv")
