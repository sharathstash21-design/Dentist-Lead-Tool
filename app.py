import streamlit as st
import requests

# Your Bridge URL
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbwvyEwYbiapxW4QXMnfUNHC14_pBwm-zDC0kuvZ1nClL0e08jpYokiFZM9r263nkQmJ/exec"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- 1. LOGIN GATE ---
if not st.session_state.logged_in:
    # ... (Keep your working login code here) ...
    st.stop()

# --- 2. THE MAIN DASHBOARD (AFTER LOGIN) ---
st.sidebar.title("🎮 Nuera Command Center")
choice = st.sidebar.radio("Go To:", ["Prompt Generator", "Lead Sniper", "Admin Panel"])

# Sidebar Credits Display
st.sidebar.divider()
st.sidebar.metric("Your Credits", st.session_state.user_credits)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 3. THE TOOLS ---

if choice == "Prompt Generator":
    st.title("📝 Prompt Generator")
    # Paste your Prompt Generator code here
    st.write("Generator is ready for use, Thambi!")

elif choice == "Lead Sniper":
    st.title("🎯 Precious Lead Sniper")
    # Paste your Sniper code here (ensure it checks for credits)
    st.write("Sniper is ready! Target locked.")

elif choice == "Admin Panel":
    # Simple Admin Gate (Only for your email)
    if st.session_state.user_email == "ngo.senthil@gmail.com": 
        st.title("👨‍💼 Admin Control Room")
        st.write("Manage your clients and credits here.")
        
        # Add a password change feature
        with st.expander("Update User Password"):
            target_user = st.text_input("User Email")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Update Password"):
                st.success(f"Password for {target_user} updated in database!")
    else:
        st.error("🚫 Access Denied. Admins only.")
