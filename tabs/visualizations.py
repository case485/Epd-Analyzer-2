import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from tabs import coi_analyzer2, culling, herd_overview, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar

def show():
    st.title('Interactive Cattle EPD Scatter Plot with Industry Trend Lines')

    # Sidebar options for cattle type selection
    cattle_type = st.selectbox(
        'Select Cattle Type',
        ['Active Sires', 'Active Dams', 'Non-Parents']
    )
    
    # EPD selection
    epd = st.selectbox(
        'Select EPD for Scatter Plot',
        ['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth']
    )
    
    # Calculate age in years
    st.session_state.filteredDf['Age (Years)'] = (datetime.now() - st.session_state.filteredDf['Date of Birth']).dt.days / 365.25

    # Filter data based on the selected cattle type
    
    if cattle_type == 'Active Sires':
        filtered_data = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'B') & (st.session_state.filteredDf['Age (Years)'] >= 2)]
    elif cattle_type == 'Active Dams':
        filtered_data = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'C') & (st.session_state.filteredDf['Age (Years)'] >= 2)]
    else:
        filtered_data = st.session_state.filteredDf[st.session_state.filteredDf['Age (Years)'] < 2]    
    
    if st.session_state.filteredDf is not None:
        def add_industry_trend_lines(fig, cattle_type, epd, filtered_data):
            # Dictionary to map the EPD column names between the filtered and industry data
            epd_map = {
                'MK': 'MK',
                'TM': 'TM',
                'Growth': 'Growth',
                'CED': 'CED',
                'BW': 'BW',
                'WW': 'WW',
                'YW': 'YW',
            }
            
            # Get the corresponding column name for the industry data
            industry_epd = epd_map.get(epd, epd)
            
            # Select the correct dataframe based on cattle type
            if cattle_type == 'Active Sires':
                industry_df = st.session_state.activeSiresPercentileRankDf
            elif cattle_type == 'Active Dams':
                industry_df = st.session_state.activeDamsPercentileRankDf
            else:
                industry_df = st.session_state.nonParentsPercentileRankDf
            
            # Get the average, top 5%, and bottom 95% industry values for the selected EPD
            industry_avg = float(industry_df[industry_df['Categories'] == 'Average'][industry_epd].values[0])
            industry_top_5 = float(industry_df[industry_df['Categories'] == '1%'][industry_epd].values[0])  # Assuming '1%' row
            industry_bottom_95 = float(industry_df[industry_df['Categories'] == 'Low'][industry_epd].values[0])  # Assuming 'Low' is bottom

            # Add the industry average trend line (red dash)
            fig.add_trace(go.Scatter(
                x=filtered_data['Name'], 
                y=[industry_avg] * len(filtered_data),  # Create a flat line at the industry average
                mode='lines',
                name=f'Industry Avg {epd}: {industry_avg:.2f}',  # Include value in the legend
                line=dict(color='yellow', dash='dash')  # Customize the appearance
            ))

            # Add the top 5% trend line (green)
            fig.add_trace(go.Scatter(
                x=filtered_data['Name'], 
                y=[industry_top_5] * len(filtered_data),  # Flat line at the top 5%
                mode='lines',
                name=f'Top 5% {epd}: {industry_top_5:.2f}',  # Include value in the legend
                line=dict(color='green', dash='dot')  # Customize the appearance
            ))

            # Add the bottom 95% trend line (dark red)
            fig.add_trace(go.Scatter(
                x=filtered_data['Name'], 
                y=[industry_bottom_95] * len(filtered_data),  # Flat line at the bottom 95%
                mode='lines',
                name=f'Bottom 95% {epd}: {industry_bottom_95:.2f}',  # Include value in the legend
                line=dict(color='darkred', dash='dot')  # Customize the appearance
            ))

            return fig

        def interactive_scatterplot_with_trend(data):


            # Check if filtered data is available
            if filtered_data.empty:
                st.write("No data available for the selected filter.")
                return

            # Create the scatter plot using Plotly
            fig = px.scatter(
                filtered_data, 
                width=1000,
                x='Name', 
                y=epd, 
                color='Type or Sex',
                title=f'Scatter Plot of {epd} vs Cattle Names for {cattle_type}',
                labels={'Name': 'Cattle Name', epd: epd},
            )
            
            # Add industry trend lines
            fig = add_industry_trend_lines(fig, cattle_type, epd, filtered_data)
            fig.update_layout(xaxis_tickangle=-45, title_font_size=30)  # Rotate x-axis labels for readability
            st.plotly_chart(fig)
        
        def plot_epd_bar_chart(df, epd, cattle_type):
            st.subheader(f"{epd} Bar Chart for the {cattle_type} ")
            
            # Extract the specific EPD columns
            epd_columns = [epd]
            
            # Iterate over each EPD column and plot bar graph
            for epd in epd_columns:
                if epd in df.columns:
                    st.write(f"##### Bar Chart for {epd}")
                    
                    # Group the data by EPD values and gather cow names for each group
                    df_copy = df.copy()
                    df_grouped = df_copy.groupby(epd).agg({
                        'Name': lambda x: ', '.join(x),  # Join cow names for hover info
                        'Registration Number': 'count'  # Count of cows per EPD value
                    }).reset_index()
                    
                    # Create the bar chart with hover info showing cow names
                    fig = px.bar(df_grouped, x=epd, y='Registration Number',
                                hover_data={'Name': True}, title=f"Distribution of {epd}")
                    fig.update_layout(yaxis_title="Cows per EPD Value")
                    # Calculate statistics
                    mean = df[epd].mean()
                    std_dev = df[epd].std()
                    
                    # Add lines for mean and ±2 standard deviations
                    fig.add_vline(x=mean, line_dash="dash", line_color="green", annotation_text="Mean", annotation_position="top left")
                    fig.add_vline(x=mean + 2 * std_dev, line_dash="dash", line_color="red", annotation_text=f"+2 SD ({std_dev:.2f})", annotation_position="top left")
                    fig.add_vline(x=mean - 2 * std_dev, line_dash="dash", line_color="blue", annotation_text=f"-2 SD ({std_dev:.2f})", annotation_position="top left")
                    
                    fig.update_layout(bargap=0.1, title_x=0.5, title_font_size=30)
                    st.plotly_chart(fig)

        interactive_scatterplot_with_trend(filtered_data, )
        plot_epd_bar_chart(filtered_data, epd, cattle_type)