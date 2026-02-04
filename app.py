import streamlit as st
import requests

# 1. YOUR APPS SCRIPT URL
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

# 2. SESSION STATE SETUP
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_credits = 0

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔐 Nuera Pro Login")
    st.markdown("### *Enter your credentials to start sniping*")
    
    email_input = st.text_input("Email Address")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        with st.spinner("Authenticating..."):
            # We send a 'login' action to your URL
            payload = {
                "action": "login",
                "email": email_input,
                "password": pass_input
            }
            try:
                response = requests.post(BRIDGE_URL, json=payload, timeout=15)
                res_data = response.json()
                
                if res_data.get("status") == "success":
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.session_state.user_credits = res_data.get("credits")
                    st.success("✅ Login Successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Email or Password. Please try again.")
            except Exception as e:
                st.error("⚠️ Connection Error. Please check your internet or Apps Script deployment.")

# --- PROTECTED APP CONTENT ---
else:
    # Sidebar with Logout and Credit Info
    with st.sidebar:
        st.header("👤 Account Info")
        st.write(f"User: **{st.session_state.user_email}**")
        st.metric("Available Credits", st.session_state.user_credits)
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Now we show the rest of the app (Prompt Generator & Sniper)
    st.title("🎯 Nuera Precious Sniper Dashboard")
    st.write(f"Welcome back, Thambi! You are ready to find some leads.")
    
    # YOUR SNIPER AND PROMPT CODE GOES HERE...
