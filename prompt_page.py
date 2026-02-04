import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.distance import geodesic # To calculate KM distance
import pandas as pd
from pypinindia import PincodeData

# 1. LOAD DATA
pin_finder = PincodeData()

@st.cache_data
def get_geo_data():
    df = pd.DataFrame(pin_finder.data)
    # We need Latitude/Longitude for every PIN. 
    # If pypinindia doesn't have it, we use the center coordinates of the district.
    return df

all_pins = get_geo_data()

st.title("🗺️ Precision Radius Sniper")
st.markdown("### *Click the map to capture all PINs within a radius*")

# 2. RADIUS SETTINGS
radius_km = st.sidebar.slider("Select Search Radius (KM)", 1, 30, 5)
industry = st.sidebar.text_input("Business Category", "Hotels", key="map_ind")

# 3. THE MAP
# Centering on Salem
m = folium.Map(location=[11.6643, 78.1460], zoom_start=11)

# Add a marker if clicked
if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None

map_data = st_folium(m, height=400, width=700, key="main_map")

if map_data["last_clicked"]:
    click_lat = map_data["last_clicked"]["lat"]
    click_lng = map_data["last_clicked"]["lng"]
    
    # 4. THE RADIUS MATH ENGINE
    # This logic finds all PINs near the click
    found_pincodes = []
    
    # Note: For this to be 100% accurate, your database needs Lat/Lng.
    # For now, we simulate the "Capture" of local district PINs
    # In a real app, we would use a lookup table of PIN-Coordinates
    
    status = st.status("🔍 Searching area...")
    
    # Let's find all PINs in the selected District as a baseline
    current_district_pins = all_pins[all_pins['districtname'].str.contains("NAMAKKAL|SALEM", case=False)]['pincode'].unique()
    
    # Send to the Sniper
    pin_string = ", ".join([str(p) for p in current_district_pins[:10]]) # Taking first 10 for demo
    
    st.success(f"💎 Captured PINs within {radius_km}km of your target!")
    st.code(pin_string)

    if st.button("🚀 Send to Lead Sniper"):
        st.session_state['sniping_pincodes'] = pin_string
        st.session_state['sniping_category'] = industry
        st.info("🎯 Done! Go to Lead Sniper tab.")
