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
    if st.session_state.mergedOuterDf is not None:
        st.caption("Data loaded successfully.")
        # Streamlit toggle for "Alive Only or All"
        alive_only = st.checkbox('Alive Only', value=True)
        if alive_only:
            # Filter the dataframe to show only alive (CM_Status = 'active')
            st.session_state.filteredDf = st.session_state.mergedOuterDf[st.session_state.mergedOuterDf['CM_Status'] == 'Active']
        else:
            # Show all entries
            st.session_state.filteredDf = st.session_state.mergedOuterDf

        # Streamlit toggle for "All Cattle or Fullblood Only"
        fullblood_only = st.checkbox('Fullblood Only', value=False)
        if fullblood_only:
            # Filter the dataframe to show only fullblood (CM_Breed 1 == 'AA' and CM_Breed Comp 1 == 100)
            st.session_state.filteredDf = st.session_state.filteredDf[(st.session_state.filteredDf['CM_Breed 1'] == 'AA') & 
                                                                      (st.session_state.filteredDf['CM_Breed Comp 1'] == 100)]

        
        # Dropdown for selecting multiple owners (CM_Owner)
        owners = st.multiselect('Select Owner(s)', options=st.session_state.mergedOuterDf['CM_Owner'].unique(), default=None, placeholder="Select Ranch Owner(s)")
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

        
        def calculate_cow_herd_count_by_sex(sex, filterToApply='CM_Type or Sex'):
            # Define time periods for filtering
            two_years_ago = datetime.now() - timedelta(days=2*365)  # Two years ago from today
            one_year_ago = datetime.now() - timedelta(days=365)      # One year ago from today
            three_years_ago = datetime.now() - timedelta(days=3*365) # Three years ago from today

            # Filter the dataframe for cows of specified sex and also by date of birth (>= 2 years old)
            cows_df = st.session_state.filteredDf[
                (st.session_state.filteredDf[filterToApply] == sex) &
                (st.session_state.filteredDf['CM_Date of Birth'] <= two_years_ago)
            ]

            # Total number of cows
            total_cows = cows_df.shape[0]

            # Count the number of cows that were <= 2 years old last year but are >= 2 years old now
            new_cows_last_year = st.session_state.filteredDf[
                (st.session_state.filteredDf[filterToApply] == sex) &
                (st.session_state.filteredDf['CM_Date of Birth'] > three_years_ago) &
                (st.session_state.filteredDf['CM_Date of Birth'] <= two_years_ago)
            ].shape[0]

            return total_cows, new_cows_last_year
        
       
       
       
        col1, col2, col3 = st.columns(3)
        with col1:
            total_cows,  new_cows_last_year = calculate_cow_herd_count_by_sex("C")
            st.metric(label="Total Active Dams", value=total_cows, delta=new_cows_last_year)
        with col2:    
            total_cows, new_cows_last_year = calculate_cow_herd_count_by_sex("B")
            st.metric(label="Total Active Sires", value=total_cows, delta=new_cows_last_year)
        
        def calculate_cow_herd_count_by_age():
            current_year = datetime.now().year

            # Calculate current age based on 'CM_Date of Birth' column
            st.session_state.filteredDf.loc[:, 'CM_Age'] = current_year - pd.to_datetime(st.session_state.filteredDf['CM_Date of Birth'], errors='coerce').dt.year


            # Non-Parents This Year: Cows that are currently less than 2 years old
            non_parents_this_year = st.session_state.filteredDf[st.session_state.filteredDf['CM_Age'] < 2].shape[0]

            # Non-Parents Last Year: Cows that were less than 2 years old a year ago
            st.session_state.filteredDf.loc[:, 'Age_1_Year_Ago'] = st.session_state.filteredDf['CM_Age'] + 1
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
            st.session_state.filteredDf['Year_Born'] = pd.to_datetime(st.session_state.filteredDf['CM_Date of Birth'], errors='coerce').dt.year

            # Drop rows where 'Year_Born' is NaN
            year_counts = st.session_state.filteredDf.groupby(['Year_Born', 'CM_Type or Sex']).size().reset_index(name='Count')
            year_counts = year_counts.pivot(index='Year_Born', columns='CM_Type or Sex', values='Count').fillna(0)
            year_counts = year_counts.sort_values('Year_Born')

            # Check if year_counts is empty
            if year_counts.empty:
                st.warning("No data available for the selected range of dates.")
                return

            # Fit a trend line using numpy for linear regression based on total counts
            year_counts['Total'] = year_counts.sum(axis=1)
            z = np.polyfit(year_counts.index, year_counts['Total'], 1)
            trend = np.poly1d(z)

            # Create a bar chart with stacked bars for bulls and cows
            fig = go.Figure()

            # Add bars for bulls (blue)
            if 'B' in year_counts.columns:
                fig.add_trace(go.Bar(
                    x=year_counts.index,
                    y=year_counts['B'],
                    name='Bulls',
                    marker_color='blue'
                ))

            # Add bars for cows (pink)
            if 'C' in year_counts.columns:
                fig.add_trace(go.Bar(
                    x=year_counts.index,
                    y=year_counts['C'],
                    name='Cows',
                    marker_color='pink'
                ))

            # Add a trend line (linear regression line)
            fig.add_trace(go.Scatter(
                x=year_counts.index,
                y=trend(year_counts.index),
                name='Trend Line',
                mode='lines',
                line=dict(color='red')
            ))

            # Update layout for better readability
            fig.update_layout(
                title='Number of Cows and Bulls by Year of Birth with Trend Line',
                xaxis_title='Year of Birth',
                yaxis_title='Number of Cows and Bulls',
                xaxis=dict(tickmode='linear'),
                yaxis=dict(showgrid=True),
                barmode='stack',
                showlegend=True
            )

            # Display the figure
            st.plotly_chart(fig)

        plot_year_born_histogram()
        
       



        

     
        
        
        
        
        
        
        
        
        
        
    else:
        st.write("Please upload the required files.")
    