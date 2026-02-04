import streamlit as st
import pandas as pd
from pypinindia import PincodeData

# Load the local Indian PIN database
# Note: You'll need to run 'pip install pypinindia' first
pin_finder = PincodeData()

st.title("📝 Precision Prompt Generator")
st.markdown("### *Find every PIN code in your target area*")

# 1. THE DRILL-DOWN FILTERS
st.header("📍 Step 1: Define Target Area")
col1, col2 = st.columns(2)

with col1:
    state = st.selectbox("Select State", pin_finder.get_states(), index=pin_finder.get_states().index("TAMIL NADU") if "TAMIL NADU" in pin_finder.get_states() else 0)
    
    # Dynamically get districts based on selected state
    available_districts = pin_finder.get_districts(state_name=state)
    district = st.selectbox("Select District", available_districts)

with col2:
    # Upgrade: Sub-district (Taluk) filter
    # This grabs all Taluks belonging to that district
    all_data = pd.DataFrame(pin_finder.data)
    taluks = all_data[all_data['districtname'].str.upper() == district.upper()]['taluk'].unique()
    sub_district = st.selectbox("Select Sub-District (Taluk/Block)", ["All Taluks"] + list(taluks))

# 2. RADIUS OPTION (Simulation)
st.divider()
st.header("📏 Step 2: Search Radius")
use_radius = st.toggle("Enable Radius Search (Coming Soon API)", False)
if use_radius:
    center_pin = st.text_input("Center PIN Code", "636001")
    radius_km = st.slider("Radius (KM)", 1, 50, 5)
    st.info("💡 Radius search will use GPS coordinates to find nearby PINs.")

# 3. GENERATE PROMPT
st.divider()
industry = st.text_input("Business Category to Scrape", "Dentist")

if st.button("💎 Generate Precious PIN List"):
    # Filter PINs based on District and Sub-District
    if sub_district == "All Taluks":
        results = pin_finder.search_by_district(district, state)
    else:
        # Precision filter for specific Taluk
        mask = (all_data['districtname'].str.upper() == district.upper()) & \
               (all_data['taluk'].str.upper() == sub_district.upper())
        results = all_data[mask]['pincode'].unique().tolist()
    
    if results:
        pin_string = ", ".join([str(p) for p in results])
        st.success(f"✅ Found {len(results)} Precision PIN Codes!")
        
        # Display the prompt for the user
        st.subheader("Your Ready-to-Use PIN List:")
        st.code(pin_string, language="text")
        
        st.info("🚀 Copy the PIN codes above and paste them into the **Lead Sniper** tab.")
    else:
        st.error("No PIN codes found for this combination.")
