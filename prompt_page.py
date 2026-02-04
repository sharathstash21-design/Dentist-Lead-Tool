import streamlit as st
import pandas as pd

st.title("📝 Nuera Prompt Generator")
st.markdown("---")

# --- Layout into two columns ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📍 Selection Criteria")
    
    # Business Categories
    category = st.selectbox("Business Category", 
        ["Dentist", "Hotels", "Schools", "Gyms", "Hospitals", "Real Estate"],
        index=0)
    
    # Location Details
    district = st.text_input("Enter District", value="Salem")
    taluk = st.text_input("Enter Taluk", value="Salem South")
    pin_code = st.text_input("Enter PIN Code", value="636001")
    
    # Extraction Source
    source = st.radio("Target Source", ["Google Maps", "Google Search"], horizontal=True)

with col2:
    st.subheader("🗺️ Geographic View")
    # This creates the Map visual you wanted
    # coordinates for Salem area as default
    map_data = pd.DataFrame({
        'lat': [11.6643], 
        'lon': [78.1460]
    })
    st.map(map_data)

# --- Action Button ---
st.markdown("---")
if st.button("✨ Generate Pro Prompt", use_container_width=True):
    if category and pin_code:
        final_prompt = f"Extract all {category} details in {taluk}, {district} - {pin_code} using {source}."
        
        st.success("✅ Prompt Generated Successfully!")
        st.code(final_prompt, language="markdown")
        
        # Saving to session state so other tools can use it if needed
        st.session_state['current_category'] = category
        st.session_state['current_pin'] = pin_code
    else:
        st.error("Please fill in the Category and PIN Code, Thambi!")
