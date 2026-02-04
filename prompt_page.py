import streamlit as st
import pandas as pd
from pypinindia import PincodeData

pin_finder = PincodeData()

st.title("📝 Precision Prompt Generator")

# ... (Previous filter code here) ...

if st.button("💎 Generate & Send to Sniper"):
    # (Your logic to get results)
    results = pin_finder.search_by_district(district, state)
    
    if results:
        pin_string = ", ".join([str(p) for p in results])
        
        # THIS IS THE MAGIC: Save it to the shared brain
        st.session_state['shared_pins'] = pin_string
        
        st.success(f"✅ Found {len(results)} PINs and sent them to the Lead Sniper!")
        st.info("🎯 Now click on 'Lead Sniper' in the sidebar to start extracting.")
