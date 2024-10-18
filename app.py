import streamlit as st
from tabs import home, herd_analysis, visualizations, individual_analysis, raw_data, logging
from sidebar import sidebar  # Import the sidebar


st.set_page_config(layout="wide")
# Initialize session state variables only if they don't exist
if 'cattleMaxCleanDf' not in st.session_state:
    st.session_state.cattleMaxCleanDf = None
if 'cattlemax_file' not in st.session_state:
    st.session_state.cattleMaxCleanDf = None


st.write(f"CattleMaxCleanDf in session state: {st.session_state.cattleMaxCleanDf}")
for key, value in st.session_state.items():
    st.write(f"Key: {key}")
# Display the sidebar
st.session_state.cattlemax_file = sidebar.show_sidebar()

# Define the tabs using `st.tabs`
st.session_state.tabs = st.tabs(["Home", "Herd Analysis", "Visualizations", "Individual Cattle Analysis", "Raw Data", "Logging"])

# Load the appropriate content in each tab
with st.session_state.tabs[0]:
    home.show()

if st.session_state.cattleMaxCleanDf is not None:
    with st.session_state.tabs[1]:
        herd_analysis.show()

    with st.session_state.tabs[2]:
        visualizations.show()

    with st.session_state.tabs[3]:
        individual_analysis.show()

    with st.session_state.tabs[4]:
        raw_data.show()

    with st.session_state.tabs[5]:
        logging.show()
