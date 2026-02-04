import streamlit as st

st.title("📝 PIN Code Prompt Generator")
st.write("Generate a ready-to-use PIN code list for your Sniper.")

# Simple database of TN Districts and their PIN ranges
# (In a real app, you can use the 'pypinindia' library)
district_pins = {
    "Salem": ["636001", "636002", "636003", "636004", "636005", "636006", "636007"],
    "Chennai": ["600001", "600002", "600003", "600004", "600005"],
    "Coimbatore": ["641001", "641002", "641003", "641004"]
}

col1, col2 = st.columns(2)
with col1:
    industry = st.text_input("Industry", "Dentist")
    district = st.selectbox("Target District", list(district_pins.keys()))

if st.button("Generate Prompt"):
    pins = district_pins.get(district, [])
    pin_string = ", ".join(pins)
    
    # Create the final prompt
    final_prompt = f"Scrape {industry} in the following areas: {pin_string}"
    
    st.success("Prompt Generated!")
    st.code(pin_string, language="text") # User can copy this directly to the Sniper
    st.info("💡 Copy the PIN codes above and paste them into the 'Lead Sniper' tab.")
