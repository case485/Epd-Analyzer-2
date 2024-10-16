import streamlit as st
from tabs import home, herd_analysis, visualizations, individual_analysis, raw_data, logging
from sidebar import sidebar  # Import the sidebar

st.session_state.mergedDf = None
st.session_state.epdDf = None
# Display the sidebar
sidebar.show_sidebar()

# Define the tabs using `st.tabs`
tabs = st.tabs(["Home", "Herd Analysis", "Visualizations", "Individual Cattle Analysis", "Raw Data", "Logging"])

# Load the appropriate content in each tab
with tabs[0]:
    home.show()

if st.session_state.mergedDf is not None:
    with tabs[1]:
        herd_analysis.show()

    with tabs[2]:
        visualizations.show()

    with tabs[3]:
        individual_analysis.show()

    with tabs[4]:
        raw_data.show()

    with tabs[5]:
        logging.show()
