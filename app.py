import streamlit as st

# Define the pages
pg = st.navigation([
    st.Page("leads_page.py", title="Lead Sniper", icon="🎯"),
    st.Page("prompt_page.py", title="Prompt Generator", icon="📝")
])

pg.run()
