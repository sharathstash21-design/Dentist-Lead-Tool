import streamlit as st
import requests
import re
import time

# 1. PAGE CONFIG (Must be the very first Streamlit command)
st.set_page_config(page_title="Nuera Sniper Pro", layout="wide")

# 2. THE BRIDGE URL (Your Apps Script)
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

# 3. INITIALIZE SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_credits = 0

# --- 4. THE LOGIN GATE ---
if not st.session_state.logged_in:
    st.title("🔐 Nuera Pro Login")
    
    email_input = st.text_input("Email")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        payload = {"action": "login", "email": email_input, "password": pass_input}
        try:
            response = requests.post(BRIDGE_URL, json=payload, timeout=15)
            res_data = response.json()
            
            if res_data.get("status") == "success":
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.session_state.user_credits = res_data.get("credits")
                st.success("✅ Welcome, Thambi! Entering Dashboard...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid Credentials")
        except:
            st.error("⚠️ Connection Error. Check Apps Script Deployment.")
    st.stop() # Prevents showing the dashboard until logged in

# --- 5. THE MAIN DASHBOARD (Only shows if logged_in is True) ---
st.sidebar.title("🎮 Nuera Command Center")
# This creates the navigation menu
choice = st.sidebar.radio("Go To:", ["Prompt Generator", "Lead Sniper", "Admin Panel"])

st.sidebar.divider()
st.sidebar.metric("Available Credits", st.session_state.user_credits)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. THE "UNLOCKER" LOGIC ---
# This part actually opens your other files and shows them on screen
if choice == "Prompt Generator":
    try:
        # This tells Python to read and run your prompt_page.py file
        with open("prompt_page.py", encoding="utf-8") as f:
            exec(f.read())
    except Exception as e:
        st.error(f"Thambi, I couldn't find prompt_page.py! Error: {e}")

elif choice == "Lead Sniper":
    try:
        # This tells Python to read and run your leads_page.py file
        with open("leads_page.py", encoding="utf-8") as f:
            exec(f.read())
    except Exception as e:
        st.error(f"Thambi, I couldn't find leads_page.py! Error: {e}")

elif choice == "Admin Panel":
    if st.session_state.user_email == "ngo.senthil@gmail.com":
        st.title("👨‍💼 Admin Control Room")
        st.write("Welcome, Boss. You can manage user credits here.")
    else:
        st.error("🚫 Access Denied. Only for the Master Sniper!")
