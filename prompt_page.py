import streamlit as st
import pandas as pd
from pypinindia import PincodeData

# Load the database
pin_finder = PincodeData()

st.title("📝 Precision Prompt Generator")

with st.sidebar:
    st.header("⚙️ Admin")
    # Unique key for this page
    st.text_input("API Key", value="7ab11ec8...", type="password", key="api_gen")

# 1. Selection UI
col1, col2 = st.columns(2)
with col1:
    state_list = pin_finder.get_states()
    state = st.selectbox("State", state_list, index=state_list.index("TAMIL NADU") if "TAMIL NADU" in state_list else 0)
    district = st.selectbox("District", pin_finder.get_districts(state_name=state))

with col2:
    all_data = pd.DataFrame(pin_finder.data)
    mask = (all_data['districtname'].str.upper() == district.upper())
    taluks = all_data[mask]['taluk'].unique()
    sub_district = st.selectbox("Sub-District (Taluk)", ["All Taluks"] + list(taluks))

# 2. Industry input
industry = st.text_input("Business Category (e.g., Hotels, Dentist)", "Hotels", key="ind_gen")

if st.button("💎 Send to Sniper", use_container_width=True):
    if sub_district == "All Taluks":
        results = pin_finder.search_by_district(district, state)
    else:
        results = all_data[mask & (all_data['taluk'].str.upper() == sub_district.upper())]['pincode'].unique().tolist()
    
    if results:
        pin_string = ", ".join([str(p) for p in results])
        
        # --- THE SYNC LOGIC ---
        st.session_state['sniping_pincodes'] = pin_string
        st.session_state['sniping_category'] = industry 
        
        st.success(f"✅ Sent {len(results)} PINs for {industry} to the Sniper!")
        st.info("🎯 Now switch to 'Lead Sniper' in the sidebar.")
