import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from tabs import home, herd_analysis, visualizations, individual_analysis, raw_data, logging
from sidebar import sidebar  # Import the sidebar
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def show():
    industryPdfFile = None
    
    st.title("Welcome to Cattle EPD Analyzer")
    #User Selection to downfilter data 
    
    if st.session_state.mergedDf is not None:
        st.caption("Data loaded successfully.")
        # Streamlit toggle for "Alive Only or All"
        alive_only = st.checkbox('Alive Only', value=True)
        if alive_only:
            # Filter the dataframe to show only alive (CM_Status = 'active')
            st.session_state.filteredDf = st.session_state.mergedDf[st.session_state.mergedDf['CM_Status'] == 'Active']
        else:
            # Show all entries
            st.session_state.filteredDf = st.session_state.mergedDf

        # Streamlit toggle for "All Cattle or Fullblood Only"
        fullblood_only = st.checkbox('Fullblood Only', value=False)
        if fullblood_only:
            # Filter the dataframe to show only fullblood (CM_Breed 1 == 'AA' and CM_Breed Comp 1 == 100)
            st.session_state.filteredDf = st.session_state.filteredDf[(st.session_state.filteredDf['CM_Breed 1'] == 'AA') & (st.session_state.filteredDf['CM_Breed Comp 1'] == 100)]

        
        # Dropdown for selecting multiple owners (CM_Owner)
        owners = st.multiselect('Select Owner(s)', options=st.session_state.mergedDf['CM_Owner'].unique(), default=st.session_state.mergedDf['CM_Owner'].unique())
        if owners:
            # Filter the dataframe based on selected owners
            st.session_state.filteredDf = st.session_state.filteredDf[st.session_state.filteredDf['CM_Owner'].isin(owners)]
        # Display the filtered dataframe
        st.write(f"Number of Cattle in Analysis: {st.session_state.filteredDf.shape[0]}")
        # st.dataframe(st.session_state.filteredDf)
        
        #ENd of user downselect*****************************************
        st.session_state.filteredDf.to_pickle('datafiles/filtered_data.pkl')
        #Starts Stats WORK 
        # Current year for age calculation
        current_year = datetime.now().year

        
        def calculate_cow_herd_count_by_sex(sex, filterToApply = 'CM_Type or Sex'):
            # Filter the dataframe for cows ('C' in 'CM_Type or Sex')
            cows_df = st.session_state.filteredDf[st.session_state.filteredDf[filterToApply] == sex]
            # Total number of cows
            total_cows = cows_df.shape[0]
            # Calculate the date 12 months ago from today
            one_year_ago = datetime.now() - timedelta(days=365)
            # Count the number of cows born in the last 12 months
            new_cows_last_year = cows_df[cows_df['CM_Date of Birth'] > one_year_ago].shape[0]
            # Count the total number of cows from 12 months ago (cows born before this date)
            cows_last_year = cows_df[cows_df['CM_Date of Birth'] <= one_year_ago].shape[0]
            # Calculate the change in cow numbers over the last 12 months
            change_in_cows = total_cows - cows_last_year
            return(total_cows, change_in_cows, new_cows_last_year)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_cows, change_in_cows, new_cows_last_year = calculate_cow_herd_count_by_sex("C")
            st.metric(label="Total Dams", value=total_cows, delta=change_in_cows)
        with col2:    
            total_cows, change_in_cows, new_cows_last_year = calculate_cow_herd_count_by_sex("B")
            st.metric(label="Total Sires", value=total_cows, delta=change_in_cows)
        
        
        
        def calculate_cow_herd_count_by_age():
            current_year = datetime.now().year

            # Calculate current age based on 'CM_Date of Birth' column
            st.session_state.filteredDf['CM_Age'] = current_year - pd.to_datetime(st.session_state.filteredDf['CM_Date of Birth'], errors='coerce').dt.year

            # Non-Parents This Year: Cows that are currently less than 2 years old
            non_parents_this_year = st.session_state.filteredDf[st.session_state.filteredDf['CM_Age'] < 2].shape[0]

            # Non-Parents Last Year: Cows that were less than 2 years old a year ago
            st.session_state.filteredDf['Age_1_Year_Ago'] = st.session_state.filteredDf['CM_Age'] + 1
            non_parents_last_year = st.session_state.filteredDf[st.session_state.filteredDf['Age_1_Year_Ago'] < 2].shape[0]

            # Calculate the change in the number of non-parents
            change_in_non_parents = non_parents_this_year - non_parents_last_year

            return non_parents_this_year, change_in_non_parents
                
        non_parents_this_year, change_in_non_parents = calculate_cow_herd_count_by_age()

        with col3:
            # Display the metric showing the current number of non-parents and the change from last year
            st.metric(label="Non-Parents This Year", value=non_parents_this_year, delta=change_in_non_parents)


        def plot_year_born_histogram():
            # Ensure the 'CM_Date of Birth' is parsed as a datetime and extract the year
            data = st.session_state.filteredDf
            data['Year_Born'] = pd.to_datetime(data['CM_Date of Birth'], errors='coerce').dt.year
    
            # Drop rows where 'Year_Born' is NaN
            data = data.dropna(subset=['Year_Born'])
            
            # Group by Year_Born to get the count of cows born each year
            year_counts = data['Year_Born'].value_counts().reset_index()
            year_counts.columns = ['Year_Born', 'Count']
            year_counts = year_counts.sort_values('Year_Born')

            # Fit a trend line using numpy for linear regression (you can also use other models)
            z = np.polyfit(year_counts['Year_Born'], year_counts['Count'], 1)
            trend = np.poly1d(z)

            # Create a bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=year_counts['Year_Born'],
                y=year_counts['Count'],
                name='Number of Cows',
                marker_color='blue'
            ))

            # Add a trend line (linear regression line)
            fig.add_trace(go.Scatter(
                x=year_counts['Year_Born'],
                y=trend(year_counts['Year_Born']),
                name='Trend Line',
                mode='lines',
                line=dict(color='red')
            ))

            # Update layout for better readability
            fig.update_layout(
                title='Number of Cows by Year of Birth with Trend Line',
                xaxis_title='Year of Birth',
                yaxis_title='Number of Cows',
                xaxis=dict(tickmode='linear'),
                yaxis=dict(showgrid=True),
                showlegend=True
            )
            st.plotly_chart(fig)
        plot_year_born_histogram()




        

     
        
        
        
        
        
        
        
        
        
        
    else:
        st.write("Please upload the required files.")
    