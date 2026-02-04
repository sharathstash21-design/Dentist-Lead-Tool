import streamlit as st
import pandas as pd
import requests
import re
import time

# --- 1. THE BRIDGE CONFIG ---
# This talks to your Google Sheet
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"
# 🚨 THAMBI: Replace this with your NEW key if the old one is empty!
SEARCH_API_KEY = "E7PCYwNsJvWgmyGkqDcMdfYN" 

# --- 2. THE FUNCTIONS ---

def deduct_remote_credit(email):
    """Tells Google Sheet to minus 1 credit"""
    try:
        payload = {"email": email, "action": "deduct"}
        requests.post(BRIDGE_URL, json=payload, timeout=10)
        return True
    except:
        return False

def fetch_precious_data(industry, pin):
    """Tells SearchAPI to find leads"""
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "q": f"{industry} in {pin}, India",
        "api_key": SEARCH_API_KEY,
        "num": 20 
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('places', data.get('local_results', []))
        else:
            st.error(f"API Error: {response.status_code}. Check your SearchAPI credits!")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- 3. THE UI ---

st.divider()
st.subheader("🎯 Lead Sniper Settings")

# Creating 3 columns for inputs
col1, col2, col3 = st.columns(3)
with col1:
    industry = st.text_input("Business Category", placeholder="e.g. Dentist, Hotel")
with col2:
    pin_input = st.text_input("Target PIN Code", placeholder="e.g. 638001")
with col3:
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])

# --- 4. THE EXTRACTION LOGIC ---

if st.button("🚀 Start Precious Extraction", use_container_width=True):
    if not industry or not pin_input:
        st.warning("⚠️ Please enter both Category and PIN Code, Thambi!")
    elif st.session_state.user_credits <= 0:
        st.error("🚫 No credits left! Please contact admin to recharge.")
    else:
        with st.status("💎 Sniping leads... please wait", expanded=True) as status:
            # STEP A: Try to get data first
            status.write("📡 Connecting to Google Maps...")
            raw_data = fetch_precious_data(industry, pin_input)
            
            if raw_data and len(raw_data) > 0:
                status.write("✅ Data Found! Deducting 1 Credit...")
                
                # STEP B: Data is found, so NOW we deduct the credit
                deduct_success = deduct_remote_credit(st.session_state.user_email)
                
                if deduct_success:
                    # STEP C: Process and Show Data
                    leads = []
                    for item in raw_data:
                        phone = item.get('phone') or item.get('phone_number')
                        if phone:
                            leads.append({
                                "Business Name": item.get('title'),
                                "Rating": item.get('rating', 'N/A'),
                                "Phone": re.sub(r'\D', '', str(phone))[-10:],
                                "Address": item.get('address', 'N/A'),
                                "Website": item.get('website', 'N/A')
                            })
                    
                    status.update(label="🎯 Extraction Successful!", state="complete", expanded=False)
                    
                    st.success(f"Found {len(leads)} Precious Leads in {pin_input}!")
                    
                    # Display Table
                    df = pd.DataFrame(leads)
                    st.dataframe(df, use_container_width=True)
                    
                    # Update local credit count and refresh
                    st.session_state.user_credits -= 1
                    time.sleep(2)
                    st.rerun()
                else:
                    status.update(label="❌ Failed to update credits in Sheet", state="error")
            else:
                status.update(label="❌ No leads found or API Key empty.", state="error")
                st.info("💡 Your Google Sheet credit was NOT deducted because no leads were found.")
