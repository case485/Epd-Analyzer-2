import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tabs import coi_analyzer2, culling, herd_overview, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar

st.session_state.update(st.session_state)

def get_sires_by_breeder(sireOverviewDf):
    # Group by 'Breeder' to count the number of sires per breeder
    sire_counts_by_breeder = sireOverviewDf['Breeder'].value_counts().reset_index()
    sire_counts_by_breeder.columns = ['Breeder', 'Number of Sires']
    # Create an interactive bar chart using Plotly
    fig = px.bar(sire_counts_by_breeder, x='Breeder', y='Number of Sires', 
                title="Number of Sires by Breeder", labels={'Number of Sires': 'Number of Sires', 'Breeder': 'Breeder'})
    return(fig)
    
def show_age_distribution(sireOverviewDf):
    # Convert 'Date of Birth' to datetime and calculate age
    sireOverviewDf['Date of Birth'] = pd.to_datetime(sireOverviewDf['Date of Birth'], errors='coerce')
    sireOverviewDf['Age'] = (pd.Timestamp.now() - sireOverviewDf['Date of Birth']).dt.days / 365.25

    # Plot the age distribution using Plotly
    fig = px.histogram(sireOverviewDf, x='Age', nbins=20, title="Age Distribution of Sires",
                    labels={'Age': 'Age (Years)'}, template='plotly')

    # Display the chart in Streamlit
    return fig

def show_percentage_of_sires_by_sire(sireOverviewDf):
    sire_counts = sireOverviewDf['Sire'].value_counts(normalize=True) * 100  # Convert to percentage
    sire_counts_df = sire_counts.reset_index()
    sire_counts_df.columns = ['Sire', 'Percentage']

    # Create a Plotly pie chart to display the percentage of cows by each sire
    fig = px.pie(sire_counts_df, names='Sire', values='Percentage', title="Percentage of Sires by Sire")

    # Display the pie chart in Streamlit
    return fig

def show_percentage_of_sires_by_dam(sireOverviewDf):
    sire_counts = sireOverviewDf['Dam'].value_counts(normalize=True) * 100  # Convert to percentage
    sire_counts_df = sire_counts.reset_index()
    sire_counts_df.columns = ['Dam', 'Percentage']

    # Create a Plotly pie chart to display the percentage of cows by each sire
    fig = px.pie(sire_counts_df, names='Dam', values='Percentage', title="Percentage of Sires by Dam")

    # Display the pie chart in Streamlit
    return fig

def avgCompositeSoreByBreeder(sireOverviewDf):
    # Calculate the average "Composite Score" by "Breeder"
    avg_composite_score_by_breeder = sireOverviewDf.groupby('Breeder')['Composite Score'].mean().reset_index()

    # Create a scatter plot with average "Composite Score" by "Breeder"
    fig = px.scatter(avg_composite_score_by_breeder, x='Breeder', y='Composite Score', 
                    title="Sire Avg Composite Score by Breeder",
                    labels={'Breeder': 'Breeder', 'Composite Score': 'Average Composite Score'})

    # Adjust x-axis to manage overlapping labels
    fig.update_layout(xaxis_tickangle=-45)

    # Display the scatter plot in Streamlit
    return(fig)

def show():
    st.header("Sire Overview")
    
    sireOverviewDf = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'B') ]
    with st.expander("Sire Data Table"):
        st.dataframe(sireOverviewDf)
    sireOverviewDf.to_csv('sireOverviewDf.csv')
    containerOverview = st.container()
    with containerOverview:
        col1Overview, col2Overview, col3Overview, col4Overview = st.columns(4)
        with col1Overview:
            total_rows = sireOverviewDf.shape[0]
            st.metric(label="Total Bulls", value=total_rows)
            
        with col2Overview:
            sireOverviewDf['Date of Birth'] = pd.to_datetime(sireOverviewDf['Date of Birth'], errors='coerce')
            sireOverviewDf['Age'] = (pd.Timestamp.now() - sireOverviewDf['Date of Birth']).dt.days / 365.25
            # Calculate the average age of sires
            average_age = sireOverviewDf['Age'].mean()
            # Display the average age using st.metric
            st.metric(label="Average Age of Sires", value=f"{average_age:.2f}")
            
        with col3Overview:
            # Ensure 'Date of Birth' is in datetime format and calculate age
            sireOverviewDf['Date of Birth'] = pd.to_datetime(sireOverviewDf['Date of Birth'], errors='coerce')
            sireOverviewDf['Age'] = (pd.Timestamp.now() - sireOverviewDf['Date of Birth']).dt.days / 365.25

            # Count the number of sires older than 10 years
            sires_over_10_years = (sireOverviewDf['Age'] > 10).sum()

            # Display the count using st.metric
            st.metric(label="Number of Sires > 10 Years Old", value=sires_over_10_years)
        with col4Overview:
            # Ensure 'Date of Birth' is in datetime format and calculate age
            sireOverviewDf['Date of Birth'] = pd.to_datetime(sireOverviewDf['Date of Birth'], errors='coerce')
            sireOverviewDf['Age'] = (pd.Timestamp.now() - sireOverviewDf['Date of Birth']).dt.days / 365.25

            # Count the number of sires older than 10 years
            sires_under2_years = (sireOverviewDf['Age'] <= 2).sum()

            # Display the count using st.metric
            st.metric(label="Number of Sires <= 2 Years Old", value=sires_under2_years)      
            

    graphCols = st.columns(2)
    with graphCols[0]:
        st.plotly_chart(get_sires_by_breeder(sireOverviewDf))
        st.plotly_chart(show_percentage_of_sires_by_sire(sireOverviewDf))
        # Display the scatter plot in Streamlit
        st.plotly_chart(px.scatter(sireOverviewDf, x='Name', y='Composite Score', title="Scatter Plot of Composite Score",
                 labels={'Age': 'Age (Years)', 'Composite Score': 'Composite Score'}))
    with graphCols[1]:
        st.plotly_chart(show_age_distribution(sireOverviewDf)) 
        st.plotly_chart(show_percentage_of_sires_by_dam(sireOverviewDf))
        st.plotly_chart(avgCompositeSoreByBreeder(sireOverviewDf))


    

    


