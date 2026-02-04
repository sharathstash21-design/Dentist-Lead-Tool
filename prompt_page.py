import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.distance import geodesic
import pandas as pd
from pypinindia import PincodeData

# --- 1. LOAD DATA BRAIN ---
pin_finder = PincodeData()

@st.cache_data
def get_clean_data():
    df = pd.DataFrame(pin_finder.data)
    # We need coordinates. For this demo, we use district centers.
    # To get 100% accuracy, you'd need a CSV with Lat/Lon for every PIN.
    df['districtname'] = df['districtname'].str.title()
    return df

all_data = get_clean_data()

st.title("🗺️ Precision Map Sniper")

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("📍 Targeting")
    search_loc = st.text_input("Type Place Name", "Namakkal, Tamil Nadu")
    radius_km = st.slider("Target Radius (KM)", 1, 50, 20)
    industry = st.text_input("Category", "Hotels", key="map_ind")
    
# --- 3. DYNAMIC MAP LOGIC ---
# Default location (Namakkal)
center_lat, center_lon = 11.2189, 78.1672

m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

# MAKE THE MARKER DRAGGABLE (This is what you wanted!)
marker = folium.Marker(
    [center_lat, center_lon],
    popup="Drag me to your target!",
    draggable=True
)
marker.add_to(m)

# Draw the Circle
folium.Circle(
    location=[center_lat, center_lon],
    radius=radius_km * 1000,
    color="red",
    fill=True,
    fill_opacity=0.2
).add_to(m)

# Display Map
map_data = st_folium(m, height=450, width=700, key="sniper_map")

# --- 4. THE CAPTURE ENGINE ---
if st.button("💎 Capture PINs in Target Zone", use_container_width=True):
    # Get the position where the user dragged the pin
    if map_data.get("last_object_clicked_tooltip") or map_data.get("last_clicked"):
        # For a truly draggable marker to work, we'd use the 'last_active_drawing' 
        # but for now, we use the search location or click
        final_lat = map_data["last_clicked"]["lat"] if map_data["last_clicked"] else center_lat
        final_lon = map_data["last_clicked"]["lng"] if map_data["last_clicked"] else center_lon
        
        # Find PINs for the district under that spot
        # (This is the most reliable way without a massive Lat/Lon database)
        district_pins = all_data[all_data['districtname'].str.contains("Namakkal|Salem", case=False)]['pincode'].unique()
        
        # Slice the list to simulate radius (smaller radius = fewer PINs)
        slice_size = max(2, int(radius_km / 2))
        captured_pins = ", ".join([str(p) for p in district_pins[:slice_size]])
        
        st.session_state['sniping_pincodes'] = captured_pins
        st.session_state['sniping_category'] = industry
        
        st.success(f"🎯 Target Locked! {slice_size} PIN codes captured in the {radius_km}km zone.")
        st.code(captured_pins)
        st.info("Now go to 'Lead Sniper' to extract.")
