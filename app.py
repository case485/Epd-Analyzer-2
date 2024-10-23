import streamlit as st
from tabs import coi_analyzer2, culling, home, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar

st.session_state.update(st.session_state)
st.set_page_config(layout="wide")
# Initialize session state variables only if they don't exist
if 'cattleMaxCleanDf' not in st.session_state:
    st.session_state.cattleMaxCleanDf = None
if 'cattlemax_file' not in st.session_state:
    st.session_state.cattlemax_file = None
if 'filteredDf' not in st.session_state:
    st.session_state.filteredDf = None
if "industryPdfFile" not in st.session_state:
    st.session_state.industryPdfFile = None
if "appState" not in st.session_state:
    st.session_state.appState = None

# Define the tabs using `st.tabs`
st.session_state.tabs = st.tabs(["Home", "Culling Scenario", "EPD Deep Dive", "Top/Bottom Performers","Sire Search", "Raw Data", "Logging", "COI Analyzer"])
st.session_state.cattlemax_file = sidebar.show_sidebar()

# Load the appropriate content in each tab
with st.session_state.tabs[0]:
    home.show()

if st.session_state.cattleMaxCleanDf is not None or st.session_state.filteredDf is not None:
    with st.session_state.tabs[1]:
        culling.show()

    with st.session_state.tabs[2]:
        visualizations.show()

    with st.session_state.tabs[3]:
        topAndBottom.show()

    with st.session_state.tabs[4]:
        sire_search.show()
    with st.session_state.tabs[5]:
        raw_data.show()

    with st.session_state.tabs[6]:
        logging.show()
    with st.session_state.tabs[7]:
        coi_analyzer2.show()
