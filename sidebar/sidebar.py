import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from tabs import culling, herd_overview, topAndBottom, visualizations, raw_data, logging

st.session_state.update(st.session_state)

def show_sidebar():
    cattlemax_csv = None
    st.sidebar.title("Sidebar Options")
    st.session_state.cattlemax_file = st.sidebar.file_uploader("Upload the Cattlemax Export File for the Herd, if you have issues be sure and save your herd file as a CSV UTF-8 file in Excel")
    
    placeholder = st.sidebar.empty()
    # st.sidebar.subheader("Industry Metrics Status")
    #If file exists then print success
    if os.path.exists(INDUSTRY_PERCENTILE_FILE):
        placeholder.info(f"Industry File Status: :white_check_mark:")
        st.session_state.appState = True
        industryPdfFile = INDUSTRY_PERCENTILE_FILE
        st.session_state.industryPdfFile = industryPdfFile
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
    if (st.session_state.cattlemax_file  is not None): 
        
        cattlemax_csv= pd.read_csv(st.session_state.cattlemax_file, index_col=False)

        # st.session_state.cattlemaxDf = cattlemaxDf
        st.sidebar.success("All Files uploaded successfully")
        st.session_state.cattleMaxCleanDf = clean_and_modify_CattlemaxDfs( cattlemax_csv)
        # st.session_state.cattleMaxCleanDf = cattleMaxCleanDf # Outer join to have all rows from both dataframes
        st.session_state.cattleMaxCleanDf.to_pickle("datafiles/cattleMaxCleanDf.pkl") #DEBUG
        return(st.session_state.cattleMaxCleanDf)
    if(cattlemax_csv is  None):
        st.warning("Please upload the Cattlemax Export File for the Herd")