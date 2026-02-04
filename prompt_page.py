import streamlit as st
import pandas as pd
from pypinindia import PincodeData

# Load the Indian PIN database
pin_finder = PincodeData()

st.title("📝 Precision Prompt Generator")
st.markdown("### *Find every PIN code in your target area*")

# 1. THE DRILL-DOWN FILTERS
st.header("📍 Step 1: Define Target Area")
col1, col2 = st.columns(2)

with col1:
    state_list = pin_finder.get_states()
    state = st.selectbox("Select State", state_list, index=state_list.index("TAMIL NADU") if "TAMIL NADU" in state_list else 0)
    
    available_districts = pin_finder.get_districts(state_name=state)
    district = st.selectbox("Select District", available_districts)

with col2:
    # Upgrade: Get Taluks for the selected district
    all_data = pd.DataFrame(pin_finder.data)
    mask = (all_data['districtname'].str.upper() == district.upper())
    taluks = all_data[mask]['taluk'].unique()
    sub_district = st.selectbox("Select Sub-District (Taluk)", ["All Taluks"] + list(taluks))

# 2. GENERATE & SEND
st.divider()
industry = st.text_input("Business Category to Scrape", "Dentist")

if st.button("💎 Generate & Send to Sniper"):
    if sub_district == "All Taluks":
        results = pin_finder.search_by_district(district, state)
    else:
        results = all_data[mask & (all_data['taluk'].str.upper() == sub_district.upper())]['pincode'].unique().tolist()
    
    if results:
        pin_string = ", ".join([str(p) for p in results])
        
        # SHARED BRAIN: Use the exact same key as the Sniper page
        st.session_state['sniping_pincodes'] = pin_string
        
        st.success(f"✅ Found {len(results)} PINs for {sub_district}!")
        st.info("🎯 Now click on 'Lead Sniper' in the sidebar to start.")
    else:
        st.error("No PIN codes found for this combination.")
