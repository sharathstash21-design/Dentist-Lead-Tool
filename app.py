import streamlit as st
import requests

# --- STEP 1: INITIALIZE SESSION STATE (The Fix!) ---
# This must come BEFORE you check "if not st.session_state.logged_in"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_credits = 0

# --- STEP 2: THE GATEKEEPER ---
if not st.session_state.logged_in:
    st.title("🔐 Nuera Pro Login")
    # ... your login code ...
