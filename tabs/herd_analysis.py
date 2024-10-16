import streamlit as st
from lib.helper_functions import *

def show():
    st.title("Herd Analysis")
    if st.session_state.filteredDf is not None:
        df = st.session_state.filteredDf
        st.write("Perform analysis of the herd EPDs and compare to industry benchmarks.")
         # Load the EPD data and perform analysis (you can expand this later)
         # Since 'CM_Date of Birth' is in datetime format, we need to calculate age by subtracting the date from the current year
        df['CM_Age'] = (pd.to_datetime('today').year) - df['CM_Date of Birth'].dt.year

        # Apply the filters based on the given criteria
        damsDf = df[(df['CM_Type or Sex'] == 'C') & (df['CM_Age'] >= 2)]
        sireDf = df[(df['CM_Type or Sex'] == 'B') & (df['CM_Age'] >= 2)]
        nonParentDf = df[df['CM_Age'] < 2]
        
        st.write(f"Number of Cows in Analysis: {damsDf.shape[0]}")
        st.write(f"Number of Bulls in Analysis: {sireDf.shape[0]}")
        st.write(f"Number of Non-Parents in Analysis: {nonParentDf.shape[0]}")
        

        # Display the dataframes to the user
        