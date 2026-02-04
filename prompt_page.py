import streamlit as st
import pandas as pd

st.title("📝 Nuera Prompt Generator")

# --- UI Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Selection")
    category = st.selectbox("Business Category", ["Dentist", "Hotels", "Real Estate", "Gym", "Hospitals"])
    district = st.text_input("District", value="Salem")
    taluk = st.text_input("Taluk", value="Salem South")
    pin_code = st.text_input("PIN Code", value="636001")

with col2:
    st.subheader("Location View")
    # This creates the Map view you were missing
    # We use dummy coordinates based on Salem if PIN is detected
    map_data = pd.DataFrame({'lat': [11.6643], 'lon': [78.1460]})
    st.map(map_data)

# --- Generate Result ---
if st.button("Generate Precious Prompt"):
    final_prompt = f"Find the best {category} leads in {taluk}, {district} with PIN code {pin_code}."
    st.success("Prompt Generated!")
    st.code(final_prompt)
    
    # Store in session state so Lead Sniper can see it
    st.session_state['last_prompt'] = final_prompt
