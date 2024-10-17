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
    if st.session_state.cattleMaxCleanDf is not None:
        st.caption("Data loaded successfully.")
        # Streamlit toggle for "Alive Only or All"
        col1Select, col2Select, col3Select, col4Select = st.columns(4)
        with col1Select:
            alive_only = st.checkbox('Alive Only', value=True)
        if alive_only:
            # Filter the dataframe to show only alive (CM_Status = 'active')
            st.session_state.filteredDf = st.session_state.cattleMaxCleanDf[st.session_state.cattleMaxCleanDf['Status'] == 'Active']
        else:
            # Show all entries
            st.session_state.filteredDf = st.session_state.cattleMaxCleanDf

        # Streamlit toggle for "All Cattle or Fullblood Only"
        with col2Select: 
            fullblood_only = st.checkbox('Fullblood Only', value=False)
        if fullblood_only:
            # Filter the dataframe to show only fullblood (CM_Breed 1 == 'AA' and CM_Breed Comp 1 == 100)
            st.session_state.filteredDf = st.session_state.filteredDf[(st.session_state.filteredDf['Breed 1'] == 'AA') & 
                                                                      (st.session_state.filteredDf['Breed Comp 1'] == 100)]

        
        # Dropdown for selecting multiple owners (CM_Owner)
        owners = st.multiselect('Select Owner(s)', options=st.session_state.cattleMaxCleanDf['Owner'].unique(), default=None, placeholder="Select Ranch Owner(s)")
        if owners:
            # Filter the dataframe based on selected owners
            st.session_state.filteredDf = st.session_state.filteredDf[st.session_state.filteredDf['Owner'].isin(owners)]
        # Display the filtered dataframe
        st.write(f"Number of Cattle in Analysis: {st.session_state.filteredDf.shape[0]}")
        #Create Composite Score
        st.session_state.filteredDf = epd_composite_score_app(st.session_state.filteredDf)
        #ENd of user downselect*****************************************
        st.session_state.filteredDf.to_pickle('datafiles/filtered_data.pkl')
        #Starts Stats WORK 
        # Current year for age calculation
        current_year = datetime.now().year

        
        def calculate_cow_herd_count_by_sex(sex, filterToApply='Type or Sex'):
            # Define time periods for filtering
            two_years_ago = datetime.now() - timedelta(days=2*365)  # Two years ago from today
            one_year_ago = datetime.now() - timedelta(days=365)      # One year ago from today
            three_years_ago = datetime.now() - timedelta(days=3*365) # Three years ago from today
            # Filter the dataframe for cows of specified sex and also by date of birth (>= 2 years old)
            cows_df = st.session_state.filteredDf[
                (st.session_state.filteredDf[filterToApply] == sex) &
                (st.session_state.filteredDf['Date of Birth'] <= two_years_ago)
            ]

            # Total number of cows
            total_cows = cows_df.shape[0]

            # Count the number of cows that were <= 2 years old last year but are >= 2 years old now
            new_cows_last_year = st.session_state.filteredDf[
                (st.session_state.filteredDf[filterToApply] == sex) &
                (st.session_state.filteredDf['Date of Birth'] > three_years_ago) &
                (st.session_state.filteredDf['Date of Birth'] <= two_years_ago)
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
            st.session_state.filteredDf.loc[:, 'Age'] = current_year - st.session_state.filteredDf['Date of Birth'].dt.year
            # st.session_state.filteredDf.loc[:, 'Age'] = current_year - pd.to_datetime(st.session_state.filteredDf['Date of Birth'], errors='coerce').dt.year


            # Non-Parents This Year: Cows that are currently less than 2 years old
            non_parents_this_year = st.session_state.filteredDf[st.session_state.filteredDf['Age'] < 2].shape[0]

            # Non-Parents Last Year: Cows that were less than 2 years old a year ago
            st.session_state.filteredDf.loc[:, 'Age_1_Year_Ago'] = st.session_state.filteredDf['Age'] + 1
            non_parents_last_year = st.session_state.filteredDf[st.session_state.filteredDf['Age_1_Year_Ago'] < 2].shape[0]

            # Calculate the change in the number of non-parents
            change_in_non_parents = non_parents_this_year - non_parents_last_year

            return non_parents_this_year, change_in_non_parents
                
        non_parents_this_year, change_in_non_parents = calculate_cow_herd_count_by_age()
        with col3:
            # Display the metric showing the current number of non-parents and the change from last year
            st.metric(label="Non-Parents This Year", value=non_parents_this_year, delta=change_in_non_parents)

        
        
       
        def plot_year_born_histogram():
            # Convert the 'Year_Born' column to the correct format
            st.session_state.filteredDf['Year_Born'] = pd.to_numeric(st.session_state.filteredDf['Year_Born'].astype(str).str.replace(',', ''), errors='coerce')

            # Drop rows where 'Year_Born' is NaN
            year_counts = st.session_state.filteredDf.groupby(['Year_Born', 'Type or Sex']).size().reset_index(name='Count')
            year_counts = year_counts.pivot(index='Year_Born', columns='Type or Sex', values='Count').fillna(0)
            year_counts = year_counts.sort_values('Year_Born')

            # Check if year_counts is empty
            if year_counts.empty:
                st.warning("No data available for the selected range of dates.")
                return

            # Calculate total counts and CAGR
            year_counts['Total'] = year_counts.sum(axis=1)
            
            def calculate_cagr(start_value, end_value, num_years):
                return (end_value / start_value) ** (1 / num_years) - 1

            cagr_values = []
            for i in range(1, len(year_counts)):
                start_year = year_counts.index[0]
                end_year = year_counts.index[i]
                start_value = year_counts['Total'].iloc[0]
                end_value = year_counts['Total'].iloc[i]
                num_years = end_year - start_year
                cagr = calculate_cagr(start_value, end_value, num_years)
                cagr_values.append(cagr)

            cagr_df = pd.DataFrame({
                'Year': year_counts.index[1:],
                'CAGR': cagr_values
            })
            cagr_df['Year'] = cagr_df['Year'].astype(int).astype(str)
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

            # Add CAGR line
            fig.add_trace(go.Scatter(
                x=cagr_df['Year'],
                y=year_counts['Total'].iloc[0] * (1 + cagr_df['CAGR']).cumprod(),
                name='CAGR Line',
                mode='lines',
                line=dict(color='red')
            ))

            # Update layout for better readability
            fig.update_layout(
                title='Number of Cows and Bulls by Year of Birth with CAGR Line',
                xaxis_title='Year of Birth',
                yaxis_title='Number of Cows and Bulls',
                xaxis=dict(tickmode='linear'),
                yaxis=dict(showgrid=True),
                barmode='stack',
                showlegend=True
            )

            # Display the figure
            st.plotly_chart(fig)

            # Display CAGR table
            st.subheader("CAGR Values by Year")
            cagr_df_transposed = cagr_df.set_index('Year').T
            cagr_df_transposed.index = ['CAGR']
            st.dataframe(cagr_df_transposed.style.format('{:.2%}'))

        # Call the function
        plot_year_born_histogram()


        

     
        
        
        
        
        
        
        
        
        
        
    else:
        st.write("Please upload the required files.")
    