import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import pandas as pd
from pypinindia import PincodeData

# --- 1. THE BRAIN ---
geolocator = Nominatim(user_agent="nuera_lead_pro")
pin_finder = PincodeData()

st.title("🗺️ Map-Based PIN Sniper")
st.markdown("### *Click the map to grab PIN codes for that area*")

# --- 2. THE MAP VIEW ---
# Start the map centered on Salem, Tamil Nadu
m = folium.Map(location=[11.6643, 78.1460], zoom_start=11)

# Enable clicking on the map
m.add_child(folium.ClickForMarker(popup="Target Area"))

# Show the map in Streamlit
map_data = st_folium(m, height=400, width=700)

# --- 3. DATA EXTRACTION LOGIC ---
if map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lng = map_data["last_clicked"]["lng"]
    
    st.write(f"📍 Selected Coordinates: {lat:.4f}, {lng:.4f}")
    
    # Find the PIN code for this exact spot
    try:
        location = geolocator.reverse((lat, lng))
        address = location.raw.get('address', {})
        found_pin = address.get('postcode')
        
        if found_pin:
            st.success(f"💎 Found PIN Code: {found_pin}")
            
            # Send to Sniper
            if st.button("🚀 Send to Sniper"):
                st.session_state['sniping_pincodes'] = str(found_pin)
                st.info("Now switch to 'Lead Sniper' tab!")
        else:
            st.warning("No PIN found at this exact spot. Try clicking a nearby building.")
    except:
        st.error("Connection error. Please try again.")

# --- 4. RADIUS SEARCH (Bonus) ---
st.divider()
st.header("📏 Radius Search")
radius = st.slider("Search Radius (KM)", 1, 20, 5)
st.write(f"This will find all business within {radius}km of your map click.")
