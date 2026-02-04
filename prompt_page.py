elif choice == "Admin Panel":
    # This ensures ONLY YOU (the boss) can see these settings
    if st.session_state.user_email == "ngo.senthil@gmail.com": 
        st.title("👨‍💼 Admin Control Room")
        st.markdown("---")
        
        # --- FEATURE 1: CHANGE PASSWORD ---
        st.subheader("🔐 User Management")
        with st.expander("Change a User's Password"):
            target_email = st.text_input("Enter Client Email")
            new_pass = st.text_input("Enter New Password", type="password")
            
            if st.button("Update Password", use_container_width=True):
                if target_email and new_pass:
                    payload = {
                        "action": "update_pass", 
                        "email": target_email, 
                        "new_password": new_pass
                    }
                    res = requests.post(BRIDGE_URL, json=payload)
                    st.success(f"✅ Success! Password for {target_email} updated in Google Sheets.")
                else:
                    st.warning("Please fill both fields, Thambi.")

        # --- FEATURE 2: ADD CREDITS ---
        st.subheader("💳 Credit Management")
        with st.expander("Add/Remove Credits"):
            c_email = st.text_input("Client Email for Credits")
            amount = st.number_input("Amount to Add (or minus)", value=500)
            
            if st.button("Add Credits", use_container_width=True):
                payload = {
                    "action": "add_credits", 
                    "email": c_email, 
                    "amount": amount
                }
                res = requests.post(BRIDGE_URL, json=payload)
                st.success(f"✅ Added {amount} credits to {c_email}!")
    else:
        # If a regular client clicks this, they see a warning
        st.error("🚫 Access Denied. This area is for Akka's Thambi only!")
