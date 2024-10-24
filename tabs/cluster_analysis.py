import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from datetime import datetime, timedelta
import plotly.express as px
from plotly.subplots import make_subplots
from tabs import coi_analyzer2, culling, home, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.graph_objs as go


st.session_state.update(st.session_state)


def show():
    # Import necessary libraries
    st.title("Analysis of Poteintial Sires and Impact on Dynamic Cluster Selection of Dams")
    


    #This function will use the filteredDF for the df 
    def clusterScenario(sireCSV, df):
        epd_columns = ['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth']
        dams_df = df[df['Designation'] == 'Dam'].copy()
        
        #open csv file and convert to dataframe
        sireDf = pd.read_csv(sireCSV)
        #change column name from "Reg No" to "Registration"
        sireDf = sireDf.rename(columns={"Reg No": "Registration Number"})
        sireDf = sireDf.rename(columns={"Milk": "MK"})
        sireDf = sireDf.rename(columns={"Total Maternal": "TM"})
        sireDf = sireDf.rename(columns={"Growth Idx": "Growth"})
        sires_df = sireDf.dropna(subset=epd_columns)
        dams_df = df.dropna(subset=epd_columns)
        
        for col in epd_columns:
            sires_df[col] = pd.to_numeric(sires_df[col], errors='coerce')
            dams_df[col] = pd.to_numeric(dams_df[col], errors='coerce')

        # Select identifier columns and EPDs
        sires_df = sires_df[['Registration Number', 'Name'] + epd_columns]
        sires_df.rename(columns={'Registration Number': 'Sire', 'Name': 'Sire Name'}, inplace=True)

        dams_df = dams_df[['Registration Number'] + epd_columns]
        dams_df.rename(columns={'Registration Number': 'Dam'}, inplace=True)

        # Define desired traits and desired directions
        desired_traits = {
            'CED': 'high',      # Higher Calving Ease Direct is better
            'BW': 'low',   # Moderate Birth Weight
            'WW': 'high',       # Higher Weaning Weight
            'YW': 'high',       # Higher Yearling Weight
            'MK': 'moderate',   # Moderate Milk
            'TM': 'moderate',   # Moderate Total Maternal
            'Growth': 'high'    # Higher Growth
        }

        desired_directions = {
            'CED': 'increase',  # Higher CED is better
            'BW': 'decrease',   # Lower BW is better
            'WW': 'increase',   # Higher WW is better
            'YW': 'increase',   # Higher YW is better
            'MK': 'increase',   # Higher MK is better
            'TM': 'increase',   # Higher TM is better
            'Growth': 'increase' # Higher Growth is better
        }

        # Function to match sires to dam clusters
        def match_sires_to_dam_clusters(sires_df, dams_df, epd_columns, desired_traits, desired_directions, n_clusters=3):
            """
            Clusters dams based on their EPDs, scores sires for each cluster, and identifies the best sire for each cluster.
            """
            # Prepare dam data
            dams_epd = dams_df[['Dam'] + epd_columns].dropna(subset=epd_columns)
            dam_ids = dams_epd['Dam']
            dams_epd_data = dams_epd[epd_columns]
            
            # Standardize dam EPDs
            scaler = StandardScaler()
            dams_epd_scaled = scaler.fit_transform(dams_epd_data)
            
            # Perform clustering on dams
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(dams_epd_scaled)
            dams_epd['Cluster'] = cluster_labels
            
            # Calculate cluster means and EPD gaps
            cluster_means = dams_epd.groupby('Cluster')[epd_columns].mean()
            overall_means = dams_epd[epd_columns].mean()
            epd_gaps = cluster_means - overall_means
            
            # Prepare sire data
            sires_epd = sires_df[['Sire', 'Sire Name'] + epd_columns].dropna(subset=epd_columns)
            sire_ids = sires_epd['Sire']
            sires_epd_data = sires_epd[epd_columns]
            
            # Function to calculate sire score for a cluster
            def sire_cluster_score(sire_epds, cluster_gaps, overall_means, epd_columns, desired_traits, desired_directions):
                score = 0
                for epd in epd_columns:
                    trait_pref = desired_traits.get(epd)
                    desired_direction = desired_directions.get(epd)
            
                    # Calculate the difference between the sire's EPD and the overall mean
                    sire_diff = sire_epds[epd] - overall_means[epd]
                    gap = cluster_gaps[epd]
            
                    if trait_pref == 'high':
                        if desired_direction == 'increase':
                            score += sire_diff * gap
                        elif desired_direction == 'decrease':
                            score -= sire_diff * gap  # Since lower is better
                    elif trait_pref == 'moderate':
                        score -= abs(sire_diff) * abs(gap)
                    elif trait_pref == 'low':
                        if desired_direction == 'decrease':
                            score += (-sire_diff) * gap
                        elif desired_direction == 'increase':
                            score -= (-sire_diff) * gap
                    else:
                        continue
                return score
            
            # Score sires for each cluster
            sire_scores = {}
            for index, sire in sires_epd.iterrows():
                sire_id = sire['Sire']
                sire_epds = sire[epd_columns]
                scores = []
                for cluster_num in cluster_means.index:
                    cluster_gap = epd_gaps.loc[cluster_num]
                    score = sire_cluster_score(
                        sire_epds=sire_epds,
                        cluster_gaps=cluster_gap,
                        overall_means=overall_means,
                        epd_columns=epd_columns,
                        desired_traits=desired_traits,
                        desired_directions=desired_directions
                    )
                    scores.append(score)
                sire_scores[sire_id] = scores
            
            # Create a DataFrame of sire scores
            sire_scores_df = pd.DataFrame(sire_scores, index=cluster_means.index)
            
            # Identify best sire for each cluster
            best_sires = {}
            for cluster_num in cluster_means.index:
                best_sire_id = sire_scores_df.loc[cluster_num].idxmax()
                best_sires[cluster_num] = best_sire_id
            
            # Predict offspring EPDs for each cluster
            offspring_epds = {}
            for cluster_num in cluster_means.index:
                best_sire_id = best_sires[cluster_num]
                sire_epds = sires_epd[sires_epd['Sire'] == best_sire_id][epd_columns].iloc[0]
                dam_cluster_mean_epds = cluster_means.loc[cluster_num]
                offspring_epd = (sire_epds + dam_cluster_mean_epds) / 2
                offspring_epds[cluster_num] = offspring_epd
            
            # Prepare dam_clusters DataFrame
            dam_clusters = dams_epd[['Dam', 'Cluster']]
            
            return dam_clusters, best_sires, offspring_epds, cluster_means, overall_means

        # Function to analyze dam clusters
        def analyze_dam_clusters(dams_df, dam_clusters, epd_columns):
            """
            Analyzes each dam cluster to identify EPD deficiencies.
            """
            # Merge dams with their clusters
            dams_clustered = dams_df.merge(dam_clusters, on='Dam')
            
            # Calculate overall means
            overall_means = dams_df[epd_columns].mean()
            
            cluster_analysis = {}
            
            for cluster_num in dam_clusters['Cluster'].unique():
                cluster_dams = dams_clustered[dams_clustered['Cluster'] == cluster_num]
                cluster_mean_epds = cluster_dams[epd_columns].mean()
                epd_gaps = overall_means - cluster_mean_epds  # Positive values indicate deficiencies
                
                # Identify significant deficiencies (e.g., more than 5% below the overall mean)
                deficiencies = epd_gaps[epd_gaps > (0.05 * overall_means)]
                
                cluster_analysis[cluster_num] = {
                    'mean_epds': cluster_mean_epds,
                    'deficiencies': deficiencies
                }
            
            return cluster_analysis

        # Function to explain sire selection
        def explain_sire_selection(cluster_analysis, best_sires, sires_df, epd_columns):
            """
            Provides explanations for why each sire was selected for a cluster.
            """
            sire_explanations = {}
            
            for cluster_num, sire_id in best_sires.items():
                sire_row = sires_df[sires_df['Sire'] == sire_id].iloc[0]
                sire_epds = sire_row[epd_columns]
                sire_name = sire_row.get('Sire Name', sire_id)
                deficiencies = cluster_analysis[cluster_num]['deficiencies']
                
                # Check how sire's EPDs address deficiencies
                improvements = {}
                for epd in deficiencies.index:
                    sire_value = sire_epds[epd]
                    dam_cluster_mean = cluster_analysis[cluster_num]['mean_epds'][epd]
                    if desired_directions[epd] == 'increase':
                        if sire_value > dam_cluster_mean:
                            improvements[epd] = sire_value - dam_cluster_mean
                    elif desired_directions[epd] == 'decrease':
                        if sire_value < dam_cluster_mean:
                            improvements[epd] = dam_cluster_mean - sire_value
                
                sire_explanations[cluster_num] = {
                    'sire_id': sire_id,
                    'sire_name': sire_name,
                    'sire_epds': sire_epds,
                    'improvements': improvements
                }
            
            return sire_explanations

        # Function to plot EPD improvements using Plotly
        def plot_epd_improvement(cluster_num, dam_mean_epds, offspring_epds, epd_columns, sire_name):
            """
            Plots the average dam EPDs and predicted offspring EPDs for a cluster using Plotly.
            Includes data labels and the Sire's name in the title.
            """
            # Ensure that the Series are aligned and ordered
            dam_epds = dam_mean_epds[epd_columns].round(2)
            offspring_epds = offspring_epds[epd_columns].round(2)

            # Create traces
            trace1 = go.Bar(
                x=epd_columns,
                y=dam_epds.values,
                name='Dam Average EPDs',
                text=dam_epds.values,
                textposition='auto'
            )
            trace2 = go.Bar(
                x=epd_columns,
                y=offspring_epds.values,
                name='Predicted Offspring EPDs',
                text=offspring_epds.values,
                textposition='auto'
            )

            data = [trace1, trace2]

            # Create layout
            layout = go.Layout(
                title=f'Cluster {cluster_num} EPD Improvement with Sire {sire_name}',
                xaxis=dict(title='EPD Traits'),
                yaxis=dict(title='EPD Values'),
                barmode='group'
            )

            fig = go.Figure(data=data, layout=layout)
            st.plotly_chart(fig)

        def display_dams_in_clusters(dam_clusters, dams_df):
            """
            Displays the dams in each cluster.

            Parameters:
            - dam_clusters: DataFrame containing dams and their assigned clusters.
            - dams_df: Original dams DataFrame with additional information if needed.
            """
            # Merge dam_clusters with additional dam information if needed
            dams_clustered = dam_clusters.merge(dams_df, on='Dam', how='left')

            # Group dams by cluster
            clusters = dams_clustered.groupby('Cluster')['Dam'].apply(list)

            # Display dams in each cluster
            for cluster_num, dam_list in clusters.items():
                st.write(f"\nDams in Cluster {cluster_num}:")
                for dam in dam_list:
                    st.write(f"- {dam}")


        # Number of clusters
        n_clusters = 3  # Adjust based on your data

        # Call the function to match sires to dam clusters
        dam_clusters, best_sires, offspring_epds, cluster_means, overall_means = match_sires_to_dam_clusters(
            sires_df, dams_df, epd_columns, desired_traits, desired_directions, n_clusters=n_clusters
        )

        # Analyze dam clusters
        cluster_analysis = analyze_dam_clusters(dams_df, dam_clusters, epd_columns)

        # Explain sire selection
        sire_explanations = explain_sire_selection(cluster_analysis, best_sires, sires_df, epd_columns)

        # Print detailed explanations and plot results
        for cluster_num in sorted(cluster_analysis.keys()):
            st.write(f"\n### Cluster {cluster_num} Analysis ###")
            st.write("Dam Cluster Average EPDs:")
            st.write(cluster_analysis[cluster_num]['mean_epds'])
            st.write("\nIdentified EPD Deficiencies (compared to overall means):")
            if not cluster_analysis[cluster_num]['deficiencies'].empty:
                st.write(cluster_analysis[cluster_num]['deficiencies'])
            else:
                st.write("No significant deficiencies.")
            
            # Sire selection explanation
            sire_info = sire_explanations[cluster_num]
            st.write(f"\nSelected Sire for Cluster {cluster_num}: {sire_info['sire_name']} (ID: {sire_info['sire_id']})")
            st.write("Sire EPDs:")
            st.write(sire_info['sire_epds'])
            st.write("\nSire Addresses the Following Deficiencies:")
            if sire_info['improvements']:
                for epd, improvement in sire_info['improvements'].items():
                    st.write(f"- {epd}: Sire improves by {improvement:.2f} units over dam cluster average.")
            else:
                st.write("Sire does not address any deficiencies directly but was selected based on overall compatibility.")
            
            # Calculate and display improvements
            dam_mean_epds = cluster_analysis[cluster_num]['mean_epds']
            offspring_epd = offspring_epds[cluster_num]
            st.write("\nExpected Improvement in Offspring EPDs:")
            for epd in epd_columns:
                dam_value = dam_mean_epds[epd]
                offspring_value = offspring_epd[epd]
                improvement = offspring_value - dam_value
                percentage = (improvement / abs(dam_value)) * 100 if dam_value != 0 else 0

                desired_direction = desired_directions[epd]

                # Determine if the change is in the desired direction
                if desired_direction == 'increase':
                    is_improvement = improvement > 0
                    change_desc = 'increase'
                elif desired_direction == 'decrease':
                    is_improvement = improvement < 0
                    change_desc = 'decrease'

                # Format the improvement message accordingly
                if is_improvement:
                    st.write(f"- {epd}: Improved by {abs(improvement):.2f} units ({abs(percentage):.2f}% {change_desc})")
                else:
                    st.write(f"- {epd}: No improvement (change of {improvement:.2f} units, {percentage:.2f}% change)")
            
            # Retrieve the Sire's name for plotting
            sire_name = sire_info['sire_name']

            # Plot EPD improvements
            plot_epd_improvement(cluster_num, dam_mean_epds, offspring_epd, epd_columns, sire_name)
        # Display dams in clusters
        display_dams_in_clusters(dam_clusters, dams_df)
        
    sire_file = st.file_uploader("Upload Sire(s) Pedigree File")    
    if sire_file:
        clusterScenario(sire_file, st.session_state.filteredDf)