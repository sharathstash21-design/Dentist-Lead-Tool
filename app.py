# --- 4. THE LOGIN GATE (Clean Version) ---
if not st.session_state.logged_in:
    st.title("🔐 Nuera Pro Login")
    
    email_input = st.text_input("Email")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        # We use a placeholder so we can clear errors instantly
        message_placeholder = st.empty()
        
        payload = {"action": "login", "email": email_input, "password": pass_input}
        try:
            response = requests.post(BRIDGE_URL, json=payload, timeout=15)
            res_data = response.json()
            
            if res_data.get("status") == "success":
                # CLEAR EVERYTHING AND SAVE
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.session_state.user_credits = res_data.get("credits")
                message_placeholder.success("✅ Welcome, Thambi! Entering Dashboard...")
                time.sleep(1)
                st.rerun() # This force-refreshes to the tools
            else:
                message_placeholder.error("❌ Invalid Credentials")
        except Exception as e:
            # Only show this if the connection actually fails
            message_placeholder.error(f"⚠️ Connection Error: {e}")
    st.stop()
