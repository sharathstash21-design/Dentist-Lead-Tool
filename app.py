# --- AFTER SUCCESSFUL LOGIN ---
st.sidebar.title("🎮 Nuera Command Center")
choice = st.sidebar.radio("Go To:", ["Prompt Generator", "Lead Sniper", "Admin Panel"])

# Sidebar Credits Display
st.sidebar.divider()
st.sidebar.metric("Your Credits", st.session_state.user_credits)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- THE LOGIC TO LOAD YOUR TOOLS ---

if choice == "Prompt Generator":
    # This runs the code from your prompt_page.py file
    try:
        with open("prompt_page.py", encoding="utf-8") as f:
            exec(f.read())
    except FileNotFoundError:
        st.error("Prompt Page file not found, Thambi! Check your GitHub files.")

elif choice == "Lead Sniper":
    # This runs the code from your leads_page.py file
    try:
        with open("leads_page.py", encoding="utf-8") as f:
            exec(f.read())
    except FileNotFoundError:
        st.error("Lead Sniper file not found! Ensure leads_page.py is in the main folder.")

elif choice == "Admin Panel":
    if st.session_state.user_email == "ngo.senthil@gmail.com":
        st.title("👨‍💼 Admin Control Room")
        # Add your credit management here
    else:
        st.error("🚫 Access Denied. Only for Akka's Thambi!")
