import streamlit as st
import os
import pandas as pd
from lib.helper_functions import *
from datetime import datetime, timedelta
import plotly.express as px
from plotly.subplots import make_subplots
from tabs import coi_analyzer2, culling, herd_overview, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar
import numpy as np
import networkx as nx
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.graph_objs as go
from sklearn.metrics.pairwise import cosine_similarity



st.session_state.update(st.session_state)


        
def show():
    def clusterScenario(sireCSV, df, n_clusters=3):
        similarity_threshold= 0.7
        """
        Analyzes the breeding program by clustering dams, matching sires, and visualizing the results.

        Parameters:
        - df: pandas DataFrame containing the data.
        - epd_columns: List of EPD columns to use in the analysis.
        - desired_traits: Dictionary specifying desired trait preferences for each EPD.
        - desired_directions: Dictionary specifying desired direction ('increase' or 'decrease') for each EPD.
        - n_clusters: Number of clusters for dam clustering.
        - similarity_threshold: Threshold for similarity when creating edges in the network visualization.

        Returns:
        - None (visualizations and explanations are displayed)
        """
        desired_traits = {
            'CED': 'high',      # Higher Calving Ease Direct is better
            'BW': 'moderate',   # Moderate Birth Weight
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

        epd_columns = ['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth']
        dams_df = df[df['Designation'] == 'Dam'].copy()
        
        sireDf = pd.read_csv(sireCSV)
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

        dams_df = dams_df[['Registration Number', 'Name'] + epd_columns]
        dams_df.rename(columns={'Registration Number': 'Dam', 'Name': 'Dam Name'}, inplace=True)

        # Function to match sires to dam clusters
        def match_sires_to_dam_clusters(sires_df, dams_df, epd_columns, desired_traits, desired_directions, n_clusters):
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
            def sire_cluster_score(sire_epds, cluster_gaps, overall_means):
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
                        overall_means=overall_means
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
        def analyze_dam_clusters(dams_df, dam_clusters):
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
        def explain_sire_selection(cluster_analysis, best_sires):
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

        # Function to display dams in clusters
        def display_dams_in_clusters(dam_clusters):
            # Merge dam_clusters with additional dam information if needed
            dams_clustered = dam_clusters.merge(dams_df, on='Dam', how='left')

            # Group dams by cluster
            clusters = dams_clustered.groupby('Cluster')['Dam Name'].apply(list)

            # Display dams in each cluster
            
            for cluster_num, dam_list in clusters.items():
                with middleColumns[cluster_num]:
                    with st.expander(f"\nDams in Cluster {cluster_num}:"):
                        listBox = st.container(height=200)
                        st.write()
                        for dam in dam_list:
                            listBox.write(f"- {dam}")

        # Function to plot EPD improvements using Plotly #FIXED 
        def plot_epd_improvement(cluster_num, dam_mean_epds, offspring_epds, sire_name):
            # Ensure that the Series are aligned and ordered, and apply rounding
            dam_epds = dam_mean_epds[epd_columns].round(2)
            offspring_epds = offspring_epds[epd_columns].round(2)

            # Create traces with rounded values
            trace1 = go.Bar(
                x=epd_columns,
                y=dam_epds.values,
                name='Dam Average EPDs',
                text=[f'{val:.2f}' for val in dam_epds.values],
                textposition='auto'
            )
            trace2 = go.Bar(
                x=epd_columns,
                y=offspring_epds.values,
                name='Predicted Offspring EPDs',
                text=[f'{val:.2f}' for val in offspring_epds.values],
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
            with bottomColumns[cluster_num]:
                st.plotly_chart(fig)

        # Function to visualize clusters network
        def visualize_clusters_network(dam_clusters, similarity_threshold):
            # Merge dams_df with dam_clusters to include cluster information
            dams_clustered = dams_df.merge(dam_clusters, on='Dam', how='left')

            # Standardize EPDs for similarity calculation
            scaler = StandardScaler()
            epd_scaled = scaler.fit_transform(dams_clustered[epd_columns])

            # Compute similarity matrix
            similarity_matrix = cosine_similarity(epd_scaled)

            # Create a graph
            G = nx.Graph()

            # Add nodes with cluster information
            for idx, row in dams_clustered.iterrows():
                G.add_node(row['Dam'], cluster=row['Cluster'], name=row.get('Dam Name', row['Dam']))

            # Add edges based on similarity
            for i in range(len(dams_clustered)):
                for j in range(i + 1, len(dams_clustered)):
                    if similarity_matrix[i, j] > similarity_threshold:
                        G.add_edge(dams_clustered.iloc[i]['Dam'], dams_clustered.iloc[j]['Dam'], weight=similarity_matrix[i, j])

            # Get positions for nodes using spring layout
            pos = nx.spring_layout(G, k=0.5, iterations=50)
            for node in G.nodes():
                G.nodes[node]['pos'] = pos[node]

            # Generate a color map for clusters
            unique_clusters = dams_clustered['Cluster'].unique()
            color_palette = ['rgba(31, 119, 180, 1)', 'rgba(255, 127, 14, 1)', 'rgba(44, 160, 44, 1)', 'rgba(214, 39, 40, 1)', 'rgba(148, 103, 189, 1)']
            cluster_colors = {cluster_num: color_palette[i % len(color_palette)] for i, cluster_num in enumerate(unique_clusters)}

            # Create edge traces
            edge_x = []
            edge_y = []

            for edge in G.edges():
                x0, y0 = G.nodes[edge[0]]['pos']
                x1, y1 = G.nodes[edge[1]]['pos']
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )

            # Create node traces
            node_x = []
            node_y = []
            node_color = []
            node_text = []

            for node in G.nodes():
                x, y = G.nodes[node]['pos']
                node_x.append(x)
                node_y.append(y)
                cluster = G.nodes[node]['cluster']
                name = G.nodes[node]['name']
                node_color.append(cluster_colors[cluster])
                node_text.append(f"{name} (Cluster {cluster})")

            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                text=node_text,
                mode='markers+text',
                textposition='top center',
                hoverinfo='text',
                marker=dict(
                    showscale=False,
                    color=node_color,
                    size=10,
                    line_width=2
                )
            )

            # Create the figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Dam Clusters Network Visualization',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                annotations=[ dict(
                                    text="",
                                    showarrow=False,
                                    xref="paper", yref="paper"
                                ) ],
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )

            with footer.expander("Click to see the network cluster visualization"):
                st.plotly_chart(fig)    

        def visualize_clusters_network_3d_orig(dam_clusters, similarity_threshold):
            # Merge dams_df with dam_clusters to include cluster information
            dams_clustered = dams_df.merge(dam_clusters, on='Dam', how='left')

            # Standardize EPDs for similarity calculation
            scaler = StandardScaler()
            epd_scaled = scaler.fit_transform(dams_clustered[epd_columns])

            # Compute similarity matrix
            similarity_matrix = cosine_similarity(epd_scaled)

            # Create a graph
            G = nx.Graph()

            # Add nodes with cluster information
            for idx, row in dams_clustered.iterrows():
                G.add_node(row['Dam'], cluster=row['Cluster'], name=row.get('Dam Name', row['Dam']))

            # Add edges based on similarity
            for i in range(len(dams_clustered)):
                for j in range(i + 1, len(dams_clustered)):
                    if similarity_matrix[i, j] > similarity_threshold:
                        G.add_edge(dams_clustered.iloc[i]['Dam'], dams_clustered.iloc[j]['Dam'], 
                                weight=similarity_matrix[i, j])

            # Get positions for nodes using spring layout in 3D
            pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)
            for node in G.nodes():
                G.nodes[node]['pos'] = pos[node]

            # Generate a color map for clusters
            unique_clusters = dams_clustered['Cluster'].unique()
            color_palette = ['rgba(31, 119, 180, 1)', 'rgba(255, 127, 14, 1)', 
                            'rgba(44, 160, 44, 1)', 'rgba(214, 39, 40, 1)', 
                            'rgba(148, 103, 189, 1)']
            cluster_colors = {cluster_num: color_palette[i % len(color_palette)] 
                            for i, cluster_num in enumerate(unique_clusters)}

            # Create edge traces
            edge_x = []
            edge_y = []
            edge_z = []

            for edge in G.edges():
                x0, y0, z0 = G.nodes[edge[0]]['pos']
                x1, y1, z1 = G.nodes[edge[1]]['pos']
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])

            edge_trace = go.Scatter3d(
                x=edge_x,
                y=edge_y,
                z=edge_z,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines'
            )

            # Create node traces
            node_x = []
            node_y = []
            node_z = []
            node_color = []
            node_text = []

            for node in G.nodes():
                x, y, z = G.nodes[node]['pos']
                node_x.append(x)
                node_y.append(y)
                node_z.append(z)
                cluster = G.nodes[node]['cluster']
                name = G.nodes[node]['name']
                node_color.append(cluster_colors[cluster])
                node_text.append(f"{name} (Cluster {cluster})")

            node_trace = go.Scatter3d(
                x=node_x,
                y=node_y,
                z=node_z,
                text=node_text,
                mode='markers+text',
                textposition='top center',
                hoverinfo='text',
                marker=dict(
                    showscale=False,
                    color=node_color,
                    size=5,
                    line_width=1
                )
            )

            # Create the figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Dam Clusters Network Visualization (3D)',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                scene=dict(
                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    zaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                ),
                                scene_camera=dict(
                                    up=dict(x=0, y=0, z=1),
                                    center=dict(x=0, y=0, z=0),
                                    eye=dict(x=1.5, y=1.5, z=1.5)
                                )
                            ))

            with footer.expander("Click to see the 3D network cluster visualization"):
                st.plotly_chart(fig)   
       
       
        def visualize_clusters_network_3d(dam_clusters, similarity_threshold):
            # Merge dams_df with dam_clusters to include cluster information
            dams_clustered = dams_df.merge(dam_clusters, on='Dam', how='left')

            # Get unique clusters for the selector
            unique_clusters = sorted(dams_clustered['Cluster'].unique())
            
            # Create the cluster selector
            selected_clusters = st.multiselect(
                "Select clusters to display:",
                options=unique_clusters,
                default=unique_clusters,
                key='cluster_selector'
            )

            # Filter data based on selected clusters
            dams_filtered = dams_clustered[dams_clustered['Cluster'].isin(selected_clusters)]

            # Standardize EPDs for similarity calculation
            scaler = StandardScaler()
            epd_scaled = scaler.fit_transform(dams_filtered[epd_columns])

            # Compute similarity matrix
            similarity_matrix = cosine_similarity(epd_scaled)

            # Create a graph
            G = nx.Graph()

            # Add nodes with cluster information
            for idx, row in dams_filtered.iterrows():
                G.add_node(row['Dam'], cluster=row['Cluster'], name=row.get('Dam Name', row['Dam']))

            # Add edges based on similarity
            for i in range(len(dams_filtered)):
                for j in range(i + 1, len(dams_filtered)):
                    if similarity_matrix[i, j] > similarity_threshold:
                        G.add_edge(dams_filtered.iloc[i]['Dam'], dams_filtered.iloc[j]['Dam'], 
                                weight=similarity_matrix[i, j])

            # Get positions for nodes using spring layout in 3D
            pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)
            for node in G.nodes():
                G.nodes[node]['pos'] = pos[node]

            # Generate a color map for clusters
            color_palette = ['rgba(31, 119, 180, 1)', 'rgba(255, 127, 14, 1)', 
                            'rgba(44, 160, 44, 1)', 'rgba(214, 39, 40, 1)', 
                            'rgba(148, 103, 189, 1)']
            cluster_colors = {cluster_num: color_palette[i % len(color_palette)] 
                            for i, cluster_num in enumerate(unique_clusters)}

            # Create edge traces
            edge_x = []
            edge_y = []
            edge_z = []

            for edge in G.edges():
                x0, y0, z0 = G.nodes[edge[0]]['pos']
                x1, y1, z1 = G.nodes[edge[1]]['pos']
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])

            edge_trace = go.Scatter3d(
                x=edge_x,
                y=edge_y,
                z=edge_z,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines'
            )

            # Create node traces
            node_x = []
            node_y = []
            node_z = []
            node_color = []
            node_text = []

            for node in G.nodes():
                x, y, z = G.nodes[node]['pos']
                node_x.append(x)
                node_y.append(y)
                node_z.append(z)
                cluster = G.nodes[node]['cluster']
                name = G.nodes[node]['name']
                node_color.append(cluster_colors[cluster])
                node_text.append(f"{name} (Cluster {cluster})")

            node_trace = go.Scatter3d(
                x=node_x,
                y=node_y,
                z=node_z,
                text=node_text,
                mode='markers+text',
                textposition='top center',
                hoverinfo='text',
                marker=dict(
                    showscale=False,
                    color=node_color,
                    size=5,
                    line_width=1
                )
            )

            # Add a legend showing cluster colors
            legend_traces = []
            for cluster in selected_clusters:
                legend_traces.append(
                    go.Scatter3d(
                        x=[None], y=[None], z=[None],
                        mode='markers',
                        name=f'Cluster {cluster}',
                        marker=dict(size=10, color=cluster_colors[cluster]),
                        showlegend=True
                    )
                )

            # Create the figure with all traces including legend
            fig = go.Figure(data=[edge_trace, node_trace] + legend_traces,
                            layout=go.Layout(
                                title='Dam Clusters Network Visualization (3D)',
                                titlefont_size=16,
                                showlegend=True,  # Show legend for clusters
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                scene=dict(
                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    zaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                ),
                                scene_camera=dict(
                                    up=dict(x=0, y=0, z=1),
                                    center=dict(x=0, y=0, z=0),
                                    eye=dict(x=1.5, y=1.5, z=1.5)
                                ),
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                )
                            ))

            # Display the plot
            with footer.expander("Click to see the 3D network cluster visualization"):
                st.plotly_chart(fig)      
            
            
       
       
       
        # Execute the analysis
        dam_clusters, best_sires, offspring_epds, cluster_means, overall_means = match_sires_to_dam_clusters(
            sires_df, dams_df, epd_columns, desired_traits, desired_directions, n_clusters
        )

        cluster_analysis = analyze_dam_clusters(dams_df, dam_clusters)
        sire_explanations = explain_sire_selection(cluster_analysis, best_sires)

        display_dams_in_clusters(dam_clusters)

        # Print detailed explanations and plot results
        for cluster_num in sorted(cluster_analysis.keys()):
            with middleColumns[cluster_num]:
                with st.expander(f"Cluster {cluster_num} Dams Analysis"):
                    st.write(f"Mean EPDs for Cluster {cluster_num} Dams:")
                    st.write(cluster_analysis[cluster_num]['mean_epds'].round(2))
                    st.write("\nIdentified EPD Deficiencies (compared to overall means):")
                    st.write("Dam Cluster Average EPDs:")
                    if not cluster_analysis[cluster_num]['deficiencies'].empty:
                        st.write(cluster_analysis[cluster_num]['deficiencies'].round(2))
                    else:
                        st.write("No significant deficiencies.")

                    # Sire selection explanation
                    sire_info = sire_explanations[cluster_num]
                    st.write(f"\nBest Sire for Cluster {cluster_num}: {sire_info['sire_name']} (ID: {sire_info['sire_id']})")
                    st.write("Sire EPDs:")
                    st.write(sire_info['sire_epds'].round(2))
                    st.write("\nSire Addresses the Following Deficiencies:")
                    if sire_info['improvements']:
                        for epd, improvement in sire_info['improvements'].items():
                            st.write(f"- {epd}: Sire improves by {improvement:.2f} units over dam cluster average.")
                    else:
                        st.write("Sire does not address any deficiencies directly but was selected based on overall compatibility.")

                    # Calculate and display improvements
                    dam_mean_epds = cluster_analysis[cluster_num]['mean_epds'].round(2)
                    offspring_epd = offspring_epds[cluster_num].round(2)
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
            plot_epd_improvement(cluster_num, dam_mean_epds, offspring_epd, sire_name)

        # Visualize clusters network
        visualize_clusters_network_3d(dam_clusters, similarity_threshold)
        # visualize_clusters_network(dam_clusters, similarity_threshold)
    introContainer = st.container()
    with introContainer:
        st.title("Cluster Analysis")
        st.write("This application allows you to analyze and visualize clusters of dams based on their EPDs. You upload a list of potential sires you would like to evaluate against your dams, the application will break your Dams into discrete clusters based on similarities in EPD deficientices and match the sire that shows the strogest improvemnt to their EPDs")
    topRow = st.container()
    topColumns = topRow.columns(3)
    
    middleRow = st.container()
    
    
    bottomRow = st.container()
    
    
    footer = st.container()
    with topColumns[0]:
        sire_file2 = st.file_uploader("Upload Sire File2 List of EPDS")
    with topColumns[2]:
            n_clusters = st.number_input("Enter the number of clusters you would like divide your dams into:", min_value=2, max_value=5, value=3)
            middleColumns = middleRow.columns(n_clusters)
            bottomColumns = bottomRow.columns(n_clusters)
    if sire_file2:
        clusterScenario(sire_file2, st.session_state.filteredDf, n_clusters)

            
