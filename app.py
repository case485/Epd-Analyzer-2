import streamlit as st
from tabs import coi_analyzer2, culling, herd_overview, topAndBottom, visualizations, sire_search, cluster_analysis, raw_data, logging, sire_overview, bcsRate
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
if "appStatus" not in st.session_state:
    st.session_state.appStatus = None

# Define the tabs using `st.tabs`
st.session_state.tabs = st.tabs(["Herd Overview", "Culling Scenario", "EPD Deep Dive", "Top/Bottom Performers","Sire Search" ,"COI Analyzer", "Cluster Analysis", "Raw Data", "Logging", "Sire Overview", "Phenotype Eval"])
st.session_state.cattlemax_file = sidebar.show_sidebar()

# Load the appropriate content in each tab
with st.session_state.tabs[0]:
    herd_overview.show()
with st.session_state.tabs[8]:
    logging.show()
with st.session_state.tabs[4]:
    sire_search.show()

if st.session_state.cattleMaxCleanDf is not None or st.session_state.filteredDf is not None:
    with st.session_state.tabs[1]:
        culling.show()
    with st.session_state.tabs[2]:
        visualizations.show()
    with st.session_state.tabs[3]:
        topAndBottom.show()
    with st.session_state.tabs[5]:
        coi_analyzer2.show()
    with st.session_state.tabs[6]:
        cluster_analysis.show()
    with st.session_state.tabs[7]:
        raw_data.show()
    with st.session_state.tabs[9]:
        sire_overview.show()
    with st.session_state.tabs[10]:
        bcsRate.show()


