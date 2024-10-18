import streamlit as st

def show():
    st.write("View the raw data.")
    with st.expander("Industry Percentile Rank Tables"):
        
        st.write(f"activeDamsPercentileDf : {st.session_state.activeDamsPercentileRankDf.shape}")
        st.dataframe(st.session_state.activeDamsPercentileRankDf)
        st.write(f"activeSiresPercentileDf : {st.session_state.activeSiresPercentileRankDf.shape}")
        st.dataframe(st.session_state.activeSiresPercentileRankDf)
        st.write(f"nonParentsPercentileDf : {st.session_state.nonParentsPercentileRankDf.shape}")
        st.dataframe(st.session_state.nonParentsPercentileRankDf)
    
    
    with st.expander("Merged Outer (ALL ROWS From Both Data Sets) Data"):
        st.write(f"Merged Data : {st.session_state.cattleMaxCleanDf.shape}")
        st.dataframe(st.session_state.cattleMaxCleanDf)
        
    with st.expander("Filtered Data"):
        st.write(f"Filtered Data : {st.session_state.filteredDf.shape}")
        st.dataframe(st.session_state.filteredDf)
        
 
    # Add logic to display raw data in table format