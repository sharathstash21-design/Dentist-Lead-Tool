import streamlit as st
import pandas as pd
import requests
import re
import time

# --- 1. CONFIG ---
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"
# 🚨 THAMBI: You MUST replace this with a NEW SearchAPI key from your dashboard!
API_KEY = "E7PCYwNsJvWgmyGkqDcMdfYN" 

# --- 2. FUNCTIONS ---

def deduct_credit(email):
    try:
        requests.post(BRIDGE_URL, json={"email": email, "action": "deduct"}, timeout=10)
        return True
    except:
        return False

def fetch_leads(industry, pin):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "q": f"{industry} in {pin}, India",
        "api_key": API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Look for results in 'places' or 'local_results'
            return data.get('places', data.get('local_results', []))
        elif response.status_code == 402 or response.status_code == 429:
            st.error("❌ SearchAPI credits exhausted! Please recharge your API key.")
            return None
        else:
            st.error(f"❌ API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# --- 3. UI ---
st.divider()
st.subheader("🎯 Target Selection")
c1, c2 = st.columns(2)
with c1:
    ind = st.text_input("Category", placeholder="Dentist")
with c2:
    pin = st.text_input("PIN Code", placeholder="638001")

if st.button("🚀 Start Precious Extraction", use_container_width=True):
    if not ind or not pin:
        st.warning("Please fill both boxes, Thambi!")
    elif st.session_state.user_credits <= 0:
        st.error("🚫 No credits left in your account.")
    else:
        with st.status("💎 Sniping...", expanded=True) as status:
            # STEP 1: Fetch Data First
            results = fetch_leads(ind, pin)
            
            if results and len(results) > 0:
                # STEP 2: Only deduct if we found something!
                deduct_credit(st.session_state.user_email)
                
                leads = []
                for item in results:
                    phone = item.get('phone') or item.get('phone_number')
                    if phone:
                        leads.append({
                            "Business": item.get('title'),
                            "Rating": item.get('rating', 'N/A'),
                            "Phone": re.sub(r'\D', '', str(phone))[-10:],
                            "Address": item.get('address', 'N/A')
                        })
                
                status.update(label="✅ Success!", state="complete")
                st.success(f"Found {len(leads)} leads!")
                st.dataframe(pd.DataFrame(leads), use_container_width=True)
                
                # Update sidebar count
                st.session_state.user_credits -= 1
                time.sleep(2)
                st.rerun()
            else:
                status.update(label="❌ No Data Found", state="error")
                st.info("💡 Your credit was NOT deducted. Check your SearchAPI dashboard.")
