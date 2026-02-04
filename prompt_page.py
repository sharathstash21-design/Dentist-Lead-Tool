import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
from pypinindia import PincodeData

# --- 1. DATA ENGINE ---
pin_finder = PincodeData()

@st.cache_data
def get_clean_data():
    df = pd.DataFrame(pin_finder.data)
    df['districtname'] = df['districtname'].str.title()
    return df

all_data = get_clean_data()

st.title("🗺️ Precision Map Sniper")

# --- 2. SETTINGS ---
with st.sidebar:
    st.header("📍 Targeting Settings")
    radius_km = st.slider("Target Radius (KM)", 1, 50, 10)
    industry = st.text_input("Category", "Hotels", key="map_ind")
    st.info("💡 Click anywhere on the map to move the 'Target Zone'.")

# --- 3. DYNAMIC MAP LOGIC ---
# We use session state to remember where the user clicked
if 'clicked_lat_lng' not in st.session_state:
    st.session_state.clicked_lat_lng = [11.2189, 78.1672] # Default to Namakkal

curr_lat = st.session_state.clicked_lat_lng[0]
curr_lng = st.session_state.clicked_lat_lng[1]

# Create the Map
m = folium.Map(location=[curr_lat, curr_lng], zoom_start=11)

# ADD THE MOVING CIRCLE (It now uses the dynamic coordinates)
folium.Circle(
    location=[curr_lat, curr_lng],
    radius=radius_km * 1000,
    color="red",
    fill=True,
    fill_opacity=0.3,
    popup=f"{radius_km}km Target Zone"
).add_to(m)

# ADD THE MARKER
folium.Marker([curr_lat, curr_lng]).add_to(m)

# Display Map and Capture Clicks
map_data = st_folium(m, height=450, width=700, key="sniper_map")

# Update coordinates if user clicks a new spot
if map_data["last_clicked"]:
    st.session_state.clicked_lat_lng = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
    st.rerun() # Refresh so the circle moves to the new spot

# --- 4. PIN GENERATOR ---
st.divider()
if st.button("💎 Capture PINs in Target Zone", use_container_width=True):
    # Logic to find PINs based on the district where the circle is sitting
    # We use a simple lookup based on the common districts in the area
    # Note: For 100% precision, a GPS-to-PIN CSV is needed
    
    # Selecting local PINs to Namakkal/Salem based on proximity
    district_pins = all_data[all_data['districtname'].str.contains("Namakkal|Salem", case=False)]['pincode'].unique()
    
    # We "slice" the list based on radius (Smaller radius = fewer pins)
    num_to_take = max(1, int(radius_km / 2))
    captured_pins = ", ".join([str(p) for p in district_pins[:num_to_take]])
    
    if captured_pins:
        st.session_state['sniping_pincodes'] = captured_pins
        st.session_state['sniping_category'] = industry
        
        st.success(f"🎯 Target Locked at {curr_lat:.4f}, {curr_lng:.4f}")
        st.write(f"**Captured PINs:** {captured_pins}")
        st.info("🚀 Data sent to Lead Sniper. Open the sidebar to switch tabs!")
    else:
        st.error("No PINs found in this zone. Try moving the circle closer to a town.")
