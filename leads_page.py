import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. CONNECTION TO GOOGLE SHEETS ---
# Use your service account JSON file or Streamlit Secrets
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open("Nuera_Users").sheet1

# --- 2. AUTHENTICATION FUNCTIONS ---
def check_login(email, password):
    data = sh.get_all_records()
    for row in data:
        if row['email'] == email and str(row['password']) == password:
            return row['credits']
    return None

def update_credits(email, new_total):
    cell = sh.find(email)
    sh.update_cell(cell.row, 3, new_total) # Update Column C (Credits)

# --- 3. LOGIN UI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Nuera Sniper Login")
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        credits = check_login(email, pwd)
        if credits is not None:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_credits = credits
            st.rerun()
        else:
            st.error("Invalid Email or Password")
else:
    # --- 4. THE SNIPER DASHBOARD ---
    st.sidebar.success(f"👤 {st.session_state.user_email}")
    st.sidebar.metric("Remaining Credits", st.session_state.user_credits)
    
    if st.session_state.user_credits <= 0:
        st.warning("⚠️ Out of credits! Please contact admin to recharge.")
        st.stop()

    # (Your existing Lead Sniper code goes here)
    if st.button("🚀 Start Sniper Scan"):
        # After successful search:
        st.session_state.user_credits -= 1
        update_credits(st.session_state.user_email, st.session_state.user_credits)
        st.sidebar.write("✅ 1 Credit Deducted")
