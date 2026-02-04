import streamlit as st
import pandas as pd
from pypinindia import PincodeData

pin_finder = PincodeData()

st.title("📝 Precision Prompt Generator")

# 1. LOAD & CLEAN THE DATA (The "Cleaner" Logic)
@st.cache_data
def get_clean_data():
    df = pd.DataFrame(pin_finder.data)
    # Convert everything to Proper Case to fix "salem" vs "SALEM"
    df['districtname'] = df['districtname'].str.title()
    df['taluk'] = df['taluk'].str.title()
    df['statename'] = df['statename'].str.title()
    return df

all_data = get_clean_data()

# 2. SELECTION UI
col1, col2 = st.columns(2)

with col1:
    states = sorted(all_data['statename'].unique())
    state = st.selectbox("Select State", states, index=states.index("Tamil Nadu") if "Tamil Nadu" in states else 0)
    
    districts = sorted(all_data[all_data['statename'] == state]['districtname'].unique())
    district = st.selectbox("Select District", districts)

with col2:
    # Get Taluks ONLY for the selected district to remove "Salem/Erode" from Namakkal
    mask = (all_data['districtname'] == district)
    taluks = sorted(all_data[mask]['taluk'].unique())
    
    sub_district = st.selectbox("Select Sub-District (Taluk)", ["All Taluks"] + taluks)

# 3. INDUSTRY & GENERATE
st.divider()
industry = st.text_input("Business Category", "Hotels", key="ind_gen")

if st.button("💎 Send to Sniper", use_container_width=True):
    # Filter for the specific PINs
    if sub_district == "All Taluks":
        final_pins = all_data[all_data['districtname'] == district]['pincode'].unique()
    else:
        final_pins = all_data[(all_data['districtname'] == district) & 
                              (all_data['taluk'] == sub_district)]['pincode'].unique()
    
    if len(final_pins) > 0:
        pin_string = ", ".join([str(p) for p in final_pins])
        
        # Sync to the Sniper
        st.session_state['sniping_pincodes'] = pin_string
        st.session_state['sniping_category'] = industry 
        
        st.success(f"✅ Found {len(final_pins)} PINs for {sub_district} in {district}!")
        st.info("🎯 switch to 'Lead Sniper' tab now.")
    else:
        st.error("No PIN codes found. Try selecting 'All Taluks'.")
