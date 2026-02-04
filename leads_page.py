import streamlit as st
import pandas as pd
import requests
import re
import time

# --- 1. THE GOOGLE BRIDGE (APPS SCRIPT) ---
# This talks to your URL: https://script.google.com/macros/s/.../exec
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

def get_remote_credits(email):
    try:
        payload = {"email": email, "action": "get_credits"}
        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
        return int(response.json().get("credits", 0))
    except:
        return 0

def deduct_remote_credit(email):
    try:
        payload = {"email": email, "action": "deduct"}
        requests.post(SCRIPT_URL, json=payload, timeout=10)
        return True
    except:
        return False

# --- 2. THE UI & LOGIC ---
st.title("🎯 Nuera Pro Lead Sniper")

# For the demo/launch, we assume the user is logged in
# In the final version, this will come from your login page
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com" # Change this to match your Sheet

# Fetch fresh credits from Google Sheet
current_credits = get_remote_credits(st.session_state.user_email)

with st.sidebar:
    st.header("👤 User Account")
    st.info(f"Logged in: **{st.session_state.user_email}**")
    st.metric("Available Credits", current_credits)
    
    st.divider()
    industry = st.text_input("Business Type", value=st.session_state.get('sniping_category', "Dentist"))
    pin_input = st.text_area("PIN Codes", value=st.session_state.get('sniping_pincodes', ""))
    target_src = st.selectbox("Source", ["Google Maps", "Google Search"])

# --- 3. THE EXTRACTION TRIGGER ---
if st.button("🚀 Start Precious Extraction"):
    if current_credits <= 0:
        st.error("❌ Out of Credits! Please contact Akka for a recharge.")
    elif not pin_input:
        st.warning("⚠️ Please provide PIN codes from the Prompt Generator.")
    else:
        # 1. DEDUCT CREDIT FIRST
        with st.status("🔐 Verifying Credits & Connecting...") as status:
            success = deduct_remote_credit(st.session_state.user_email)
            if success:
                status.update(label="✅ Credit Deducted. Starting Scan...", state="running")
                
                # 2. RUN SEARCH (Using your working SearchAPI logic)
                # (Assuming you have your fetch_precious_data function here)
                # For this example, we show the result of 1 credit used
                time.sleep(2) 
                
                st.success("Target Locked! One credit has been deducted from your account.")
                st.balloons()
                # Force refresh of the sidebar metric
                st.rerun()
            else:
                st.error("Failed to connect to the Credit Server.")
