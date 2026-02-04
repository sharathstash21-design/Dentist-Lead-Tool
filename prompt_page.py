import streamlit as st
import pandas as pd
import requests
import re
import time

# --- 1. THE EXTRACTION ENGINE (Make sure this is at the top) ---
def fetch_from_api(query, pin, api_key, target_source):
    # This uses your SearchAPI.io key
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps" if target_source == "Google Maps" else "google",
        "q": f"{query} {pin} India",
        "api_key": api_key,
        "gl": "in"
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        return data.get('places', []) or data.get('local_results', []) or data.get('organic_results', [])
    except:
        return []

# --- 2. THE UI LOGIC ---
st.title("🎯 Nuera Pro Lead Sniper")

# Get inputs from your sidebar (as seen in your screenshot)
industry = st.session_state.get('business_type', "Hotels")
pin_input = st.session_state.get('pin_codes', "638007")
target_src = st.session_state.get('source', "Google Maps")

if st.button("🚀 Start Precious Extraction"):
    # First, check if Thambi has enough credits
    if st.session_state.user_credits > 0:
        
        with st.spinner("💎 Sniping Precious Leads... Please Wait"):
            # A. DEDUCT CREDIT FIRST (Your working logic)
            # deduct_remote_credit(st.session_state.user_email)
            
            # B. RUN THE ACTUAL SEARCH
            # Using your provided SearchAPI key
            API_KEY = "E7PCYwNsJvWgmyGkqDcMdfYN" 
            raw_results = fetch_from_api(industry, pin_input, API_KEY, target_src)
            
            if raw_results:
                # C. PROCESS THE DATA
                leads = []
                for rank, item in enumerate(raw_results, 1):
                    phone = item.get('phone') or item.get('phone_number')
                    if phone:
                        leads.append({
                            "Rank": rank,
                            "Business": item.get('title'),
                            "Rating": item.get('rating', 'N/A'),
                            "Phone": re.sub(r'\D', '', str(phone))[-10:],
                            "Website": item.get('website', 'N/A')
                        })
                
                # D. SHOW THE SUCCESS MESSAGE & TABLE
                st.success(f"✅ Found {len(leads)} Precious Leads!")
                df = pd.DataFrame(leads)
                st.dataframe(df, use_container_width=True)
                
                # Update the session state so the sidebar shows the new credit count
                st.session_state.user_credits -= 1
                st.rerun() # Refresh to show new credit count
            else:
                st.error("❌ No results found for this PIN. Try another category.")
    else:
        st.error("🚫 Out of credits! Please recharge.")
