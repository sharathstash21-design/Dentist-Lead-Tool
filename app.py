import streamlit as st
import requests
import time

# 1. THE VERY FIRST COMMAND
st.set_page_config(page_title="Nuera Pro Dashboard", layout="wide")

# 2. YOUR GOOGLE BRIDGE URL
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

# 3. INITIALIZE SESSION STATE (Prevents NameError/AttributeError)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_credits = 0

# 4. THE LOGIN GATE
if not st.session_state.logged_in:
    st.title("🔐 Nuera Pro Login")
    st.write("Welcome back, Thambi! Please sign in to access your tools.")
    
    email_input = st.text_input("Email Address")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        if not email_input or not pass_input:
            st.warning("Please enter both email and password.")
        else:
            with st.spinner("Connecting to Google Database..."):
                payload = {"action": "login", "email": email_input, "password": pass_input}
                try:
                    response = requests.post(BRIDGE_URL, json=payload, timeout=15)
                    res_data = response.json()
                    
                    if res_data.get("status") == "success":
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_input
                        st.session_state.user_credits = res_data.get("credits")
                        st.success("✅ Login Successful! Opening Dashboard...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Email or Password. Check your Google Sheet!")
                except Exception as e:
                    st.error(f"⚠️ Connection Error: {e}")
    st.stop() # Prevents the app from loading further until login is True

# 5. THE MAIN DASHBOARD (Only runs after login)
st.sidebar.title("🎮 Nuera Command Center")
choice = st.sidebar.radio("Go To:", ["Prompt Generator", "Lead Sniper", "Admin Panel"])

st.sidebar.divider()
st.sidebar.metric("Your Credits", st.session_state.user_credits)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# 6. LOADING YOUR TOOL FILES
if choice == "Prompt Generator":
    st.title("📝 Prompt Generator")
    try:
        with open("prompt_page.py", encoding="utf-8") as f:
            exec(f.read())
    except FileNotFoundError:
        st.info("Please ensure 'prompt_page.py' is uploaded to your GitHub folder.")

elif choice == "Lead Sniper":
    st.title("🎯 Lead Sniper")
    try:
        with open("leads_page.py", encoding="utf-8") as f:
            exec(f.read())
    except FileNotFoundError:
        st.info("Please ensure 'leads_page.py' is uploaded to your GitHub folder.")

elif choice == "Admin Panel":
    # Only you can see this (based on your email)
    if st.session_state.user_email == "ngo.senthil@gmail.com":
        st.title("👨‍💼 Admin Control Room")
        st.write("Manage credits and users here.")
    else:
        st.error("🚫 Access Denied. Admins only.")

