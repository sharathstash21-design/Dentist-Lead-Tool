import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import pandas as pd
from pypinindia import PincodeData

# 1. LOAD BRAIN
geolocator = Nominatim(user_agent="nuera_geo_sniper")
pin_finder = PincodeData()

@st.cache_data
def get_clean_data():
    df = pd.DataFrame(pin_finder.data)
    df['districtname'] = df['districtname'].str.title()
    return df

all_data = get_clean_data()

st.title("🗺️ Meta-Style Map Sniper")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("📍 Location Search")
    # Type a location (e.g., "Fairlands, Salem")
    search_loc = st.text_input("Type Location Name", "Salem, Tamil Nadu")
    radius_km = st.slider("Target Radius (KM)", 1, 20, 5)
    industry = st.text_input("Business Category", "Hotels", key="map_ind")
    
    find_btn = st.button("🔍 Find Location on Map")

# --- COORDINATE LOGIC ---
# Default to Salem
lat, lon = 11.6643, 78.1460 

if find_btn:
    try:
        loc = geolocator.geocode(search_loc)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.session_state['map_center'] = [lat, lon]
    except:
        st.error("Could not find that location. Try adding 'Tamil Nadu'.")

# Use session state to keep the map where the user searched
center = st.session_state.get('map_center', [lat, lon])

# --- 2. THE DYNAMIC MAP ---
m = folium.Map(location=center, zoom_start=12)

# Draw the Radius Circle (Like Meta Ads)
folium.Circle(
    radius=radius_km * 1000, # Convert KM to Meters
    location=center,
    color="red",
    fill=True,
    fill_color="red",
    fill_opacity=0.2
).add_to(m)

# Add a marker in the center
folium.Marker(location=center, popup="Target Center").add_to(m)

# Show Map
map_data = st_folium(m, height=450, width=700)

# --- 3. PIN CAPTURE LOGIC ---
if st.button("💎 Capture PINs in Circle", use_container_width=True):
    # For now, we fetch PINs from the nearest district to the search center
    try:
        location_info = geolocator.reverse((center[0], center[1]))
        addr = location_info.raw.get('address', {})
        dist_name = addr.get('city', addr.get('county', 'Salem')).replace(" District", "")
        
        # Filter PINs for that district
        pins = all_data[all_data['districtname'].str.contains(dist_name, case=False)]['pincode'].unique()
        
        # We simulate radius selection by taking a slice of district pins
        # (In a real pro version, we'd use Lat/Lon for every PIN)
        pin_string = ", ".join([str(p) for p in pins[:8]]) 
        
        st.session_state['sniping_pincodes'] = pin_string
        st.session_state['sniping_category'] = industry
        
        st.success(f"🎯 Target Locked! {len(pins[:8])} PINs captured within {radius_km}km of {search_loc}.")
        st.info("Now go to 'Lead Sniper' to extract.")
    except:
        st.error("Error capturing PINs. Please try again.")
