import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from tabs import home, herd_analysis, visualizations, individual_analysis, raw_data, logging

def show_sidebar():
    st.sidebar.title("Sidebar Options")
    epd_file = st.sidebar.file_uploader("Upload the EPD File for the Herd")
    cattlemax_file = st.sidebar.file_uploader("Upload the Cattlemax Export File for the Herd")
    placeholder = st.sidebar.empty()
    st.sidebar.subheader("Industry Metrics Status")
    #If file exists then print success
    if os.path.exists(INDUSTRY_PERCENTILE_FILE):
        placeholder.info(f"Industry File Status: :white_check_mark:")
        industryPdfFile = INDUSTRY_PERCENTILE_FILE
    else:
        placeholder.info(f"Industry File Status: :x:")
        industryPdfFile = get_percentile_rank_url_by_pattern()
        if industryPdfFile != None:
            st.sidebar.success("Metrics refreshed")
            placeholder.info(f"Industry File Status: :white_check_mark:")
        else:
            st.sidebar.error("Failed to refresh metrics")
    st.session_state.activeSiresPercentileRankDf, st.session_state.activeDamsPercentileRankDf, st.session_state.nonParentsPercentileRankDf = extract_IndustryPercentileRankTables_from_pdf()
    if st.sidebar.button("Refresh Industry Metrics"):
        industryPdfFile = get_percentile_rank_url_by_pattern()
        if industryPdfFile != None:
            st.session_state.activeSiresPercentileRankDf, st.session_state.activeDamsPercentileRankDf, st.session_state.nonParentsPercentileRankDf = extract_IndustryPercentileRankTables_from_pdf()
        else:
            st.sidebar.error("Failed to refresh metrics")
    if epd_file is not None and cattlemax_file is not None and industryPdfFile is not None: 
        #All 3 datafiles are now uploaded and can be analyzed. 
        # First we need to compbine the 2 cattle dataframes into one
        epdDf = pd.read_csv(epd_file)
        epdDf.to_pickle("datafiles/epdDf.pkl")
        cattlemaxDf = pd.read_csv(cattlemax_file)
        cattlemaxDf.to_pickle("datafiles/cattlemaxDf.pkl")
        st.session_state.epdDf = epdDf
        st.session_state.cattlemaxDf = cattlemaxDf
        st.sidebar.success("All Files uploaded successfully")
        mergedLeftJoinDf, mergedOuterDf = mergeEpdAndCattlemaxDfs(epdDf, cattlemaxDf)
        st.session_state.mergedLeftDf = mergedLeftJoinDf # Left Join to only have rows where EPD data exists
        st.session_state.mergedOuterDf = mergedOuterDf # Outer join to have all rows from both dataframes
        st.session_state.mergedOuterDf.to_pickle("datafiles/mergedOuterDf.pkl") #DEBUG
        
    else:
        st.error("Please upload the required files")