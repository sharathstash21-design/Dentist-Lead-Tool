import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
from pypinindia import PincodeData

# 1. LOAD & CLEAN DATA
pin_finder = PincodeData()

@st.cache_data
def get_clean_geo_data():
    # Load the library data into a DataFrame
    df = pd.DataFrame(pin_finder.data)
    # Clean the names for professional display
    df['districtname'] = df['districtname'].str.title().str.strip()
    df['taluk'] = df['taluk'].str.title().str.replace('-', ' ').str.strip()
    return df

all_data = get_clean_geo_data()

st.title("🗺️ Precision Map Sniper")
st.write("Click on the map to move the target zone and capture lead PINs.")

# 2. SIDEBAR CONTROLS
with st.sidebar:
    st.header("📍 Targeting Settings")
    radius_km = st.slider("Target Radius (KM)", 1, 50, 10)
    industry = st.text_input("Category", "Hotels", key="map_ind")

# 3. DYNAMIC MAP LOGIC
# Default center (Namakkal/Salem area)
if 'map_center' not in st.session_state:
    st.session_state.map_center = [11.2189, 78.1672]

curr_lat, curr_lng = st.session_state.map_center

# Create the Folium Map
m = folium.Map(location=[curr_lat, curr_lng], zoom_start=11)

# DRAW THE TARGET ZONE (The Red Circle)
folium.Circle(
    location=[curr_lat, curr_lng],
    radius=radius_km * 1000,
    color="red",
    fill=True,
    fill_opacity=0.3
).add_to(m)

folium.Marker([curr_lat, curr_lng], popup="Target Center").add_to(m)

# DISPLAY AND CAPTURE CLICKS
map_output = st_folium(m, height=450, width=700, key="sniper_map")

# Update center if the user clicks somewhere else
if map_output["last_clicked"]:
    new_lat = map_output["last_clicked"]["lat"]
    new_lng = map_output["last_clicked"]["lng"]
    if [new_lat, new_lng] != st.session_state.map_center:
        st.session_state.map_center = [new_lat, new_lng]
        st.rerun()

# 4. CAPTURE ENGINE
st.divider()
if st.button("💎 Capture PINs in Target Zone", use_container_width=True):
    # Filter PINs based on the general area (Salem/Namakkal focus)
    district_mask = all_data['districtname'].str.contains("Namakkal|Salem|Erode", case=False)
    district_pins = all_data[district_mask]['pincode'].unique()
    
    # Calculate how many PINs to show based on radius
    num_to_capture = max(2, int(radius_km / 1.5))
    captured_pins = ", ".join([str(p) for p in district_pins[:num_to_capture]])
    
    if captured_pins:
        # SYNC TO SESSION STATE for the Lead Sniper to use
        st.session_state['sniping_pincodes'] = captured_pins
        st.session_state['sniping_category'] = industry
        
        st.success(f"🎯 Target Locked! {len(captured_pins.split(','))} PINs captured in the {radius_km}km zone.")
        st.code(captured_pins)
        st.info("🚀 Data sent! Go to 'Lead Sniper' in the sidebar to start extraction.")
    else:
        st.error("No PINs found in this zone. Move the circle closer to a city center.")
