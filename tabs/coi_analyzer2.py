#Streamlit app for Graph Pedigree Testing

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import seaborn as sns
import networkx as nx
import time
import streamlit.components.v1 as components
import plotly.graph_objs as go
from config import *
from tabs import culling, home, topAndBottom, visualizations, raw_data, logging
from lib.helper_functions import *


def show(): 
    def import_row_and_format(row_wide):
        row_wide_copy = row_wide.copy()
        pedigree_list = []
        flatten_pedigree_row(row_wide_copy, pedigree_list)
        # Create a DataFrame from the pedigree list for this single row
        df_long = pd.DataFrame(pedigree_list)
        # Clean and strip the data in the resulting DataFrame
        def clean_and_strip(df):
            df = df.replace({'': None, 'None': None})
            df['animal_id'] = df['animal_id'].astype(str).str.strip()
            df['animal_name'] = df['animal_name'].astype(str).str.strip()
            df['sire_id'] = df['sire_id'].astype(str).str.strip()
            df['dam_id'] = df['dam_id'].astype(str).str.strip()
            return df
        df_long = clean_and_strip(df_long)
        return df_long

    def flatten_pedigree_row(row, pedigree_list, prefix=''):
        if prefix == '':
            animal_id_col = 'animal_registration'
            animal_name_col = 'animal_name'
            sire_id_col = 'sire'
            dam_id_col = 'dam'
        else:
            # For ancestors, the animal ID is in the column prefix without the trailing '_'
            animal_id_col = prefix[:-1]  # Remove trailing '_'
            animal_name_col = prefix[:-1] + '_name'
            sire_id_col = prefix + 'sire'
            dam_id_col = prefix + 'dam'

        # Retrieve the animal's information
        animal_id = row.get(animal_id_col)
        animal_name = row.get(animal_name_col)
        sire_id = row.get(sire_id_col)
        dam_id = row.get(dam_id_col)

        # Convert IDs to strings and strip whitespace
        animal_id = str(animal_id).strip() if pd.notna(animal_id) else None
        animal_name = str(animal_name).strip() if pd.notna(animal_name) else None
        sire_id = str(sire_id).strip() if pd.notna(sire_id) else None
        dam_id = str(dam_id).strip() if pd.notna(dam_id) else None

        # Check if the animal ID is present
        if animal_id:
            # Add the animal to the pedigree list
            pedigree_list.append({
                'animal_id': animal_id,
                'animal_name': animal_name,
                'sire_id': sire_id,
                'dam_id': dam_id
            })
            # Recurse for sire and dam
            if sire_id and sire_id != animal_id:
                flatten_pedigree_row(row, pedigree_list, prefix=prefix + 'sire_')
            if dam_id and dam_id != animal_id:
                flatten_pedigree_row(row, pedigree_list, prefix=prefix + 'dam_')

    def build_pedigree_graph(df, graph, type=None):
        for idx, row in df.iterrows():
            animal_id = row['animal_id']
            animal_name = row['animal_name']
            sire_id = row['sire_id']
            dam_id = row['dam_id']

            # Skip None or empty values for sire and dam
            if sire_id and sire_id != animal_id and sire_id != 'None' and pd.notna(sire_id):
                graph.add_edge(sire_id, animal_id)
                graph.nodes[animal_id]["label"] = animal_name
                graph.nodes[animal_id]['Fa'] = 0.5
            elif not sire_id or sire_id == 'None' or pd.isna(sire_id):
                graph.add_node(animal_id, label=animal_name, Fa=None)

            # Add dam edge
            if dam_id and dam_id != animal_id and dam_id != 'None' and pd.notna(dam_id):
                graph.add_edge(dam_id, animal_id)
                graph.nodes[animal_id]["label"] = animal_name
                graph.nodes[animal_id]['Fa'] = 0
            elif not dam_id or dam_id == 'None' or pd.isna(dam_id):
                graph.add_node(animal_id, label=animal_name, Fa=None)

    def st_Build_Sidebar():
        # st.sidebar.title("Sidebar Options")
        # st.sidebar.write("")
        st.session_state.sirePedigreeFile = st.file_uploader("Upload Sire(s) Pedigree File")
        st.session_state.damPedigreeFile = st.file_uploader("Upload Dam(s) Pedigree File")
        placeholder = st.empty()

    def import_data_and_format(row_wide):
        # Create a deep copy of the row to prevent changes to the original dataframe
        row_wide_copy = row_wide.copy()
        # List to hold the flattened pedigree data for this row
        pedigree_list = []
        # Flatten the pedigree for this single row
        flatten_pedigree_row(row_wide_copy, pedigree_list)
        # Create a DataFrame from the pedigree list
        df_long = pd.DataFrame(pedigree_list)
        # Function to clean and strip the data
        def clean_and_strip(df):
            df = df.replace({'': None, 'None': None})
            df['animal_id'] = df['animal_id'].astype(str).str.strip()
            df['animal_name'] = df['animal_name'].astype(str).str.strip()
            df['sire_id'] = df['sire_id'].astype(str).str.strip()
            df['dam_id'] = df['dam_id'].astype(str).str.strip()
            return df

        # Clean the long-format dataframe
        df_long = clean_and_strip(df_long)
        return df_long

    def assign_generations_to_edges(G):
        root_candidates = [node for node in G.nodes if G.out_degree(node) == 0]
        root = root_candidates[0] if root_candidates else None

        if root is None:
            print("No valid root node found.")
        else:
            # Step 2: Use DFS to assign generation distances
            def dfs(node, current_generation):
                for predecessor in G.predecessors(node):
                    G[predecessor][node]["Generation"] = current_generation + 1
                    dfs(predecessor, current_generation + 1)
            # Start DFS from the root node with generation 0
            dfs(root, 0)

        return G

    def create_graph_plot(G, title):
        # Generate labels for edges, defaulting if 'Generation' is missing
        edge_generation_labels = {
            (u, v): f"Generation {attributes.get('Generation', 'Unknown')}" 
            for u, v, attributes in G.edges(data=True)
        }
        
        # Generate custom labels for nodes, showing both 'animal_name' and 'Fa'
        node_labels = {
            node: f"{G.nodes[node].get('label', '')}\nFa: {G.nodes[node].get('COI', 'N/A')}"
            for node in G.nodes()
        }
        
        # Use graphviz layout to create a vertical tree structure
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot')  # 'dot' produces a hierarchical layout
        
        plt.figure(figsize=(12, 8))
        
        # Draw the graph with custom node labels
        nx.draw(G, pos, with_labels=True, labels=node_labels, node_size=3000, node_color='skyblue', font_size=10)
        
        # Draw edge labels for generation info
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_generation_labels)
        
        plt.title(title)
        return plt

    def create_graphViz_Plot(G_sire):
        pos = graphviz_layout(G_sire, prog='dot')

        # Extract node positions
        x_nodes = [pos[node][0] for node in G_sire.nodes()]
        y_nodes = [pos[node][1] for node in G_sire.nodes()]  # Negative y to flip the direction for better visualization
        node_ids = [node for node in G_sire.nodes()]  # Node IDs as labels on the graph
        labels_name = [node for node in G_sire.nodes()]  # Animal names for hover

        # Create edge traces
        edge_x = []
        edge_y = []
        for u, v in G_sire.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])  # Negative y to flip direction

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create node traces
        node_trace = go.Scatter(
            x=x_nodes, y=y_nodes,
            text=labels_name,  # Node IDs as labels on the graph
            mode='markers+text',
            textposition='top center',
            hoverinfo='text',  # Show animal names on hover
            hovertext=node_ids,  # Animal names for hover text
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Generation Level',
                    xanchor='left',
                    titleside='right'
                )
            ),
            textfont=dict(
                size=10,  # Set the font size of the labels here
            )
        )

        # Create the layout for the plot
        layout = go.Layout(
            title='Interactive Pedigree Graph',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        # Create the figure with edge and node traces
        fig = go.Figure(data=[edge_trace, node_trace], layout=layout)

        # Display the interactive graph
        return(fig)

    def calculate_pedigree_coi_ORIGINAL(graph):
        def calculate_wright_coi_corrected(graph, node, generations=6):
            predecessors = list(graph.predecessors(node))
            if len(predecessors) != 2:
                # Node must have exactly two parents to calculate COI
                return 0.0, []
            sire, dam = predecessors
            sire_ancestors = nx.ancestors(graph, sire)
            dam_ancestors = nx.ancestors(graph, dam)
            common_ancestors = sire_ancestors.intersection(dam_ancestors)
            coi = 0.05
            calculation_steps = []

            for ancestor in common_ancestors:
                # Get all paths from the ancestor to both sire and dam
                paths_sire = list(nx.all_simple_paths(graph.reverse(), source=sire, target=ancestor, cutoff=generations))
                paths_dam = list(nx.all_simple_paths(graph.reverse(), source=dam, target=ancestor, cutoff=generations))

                # Calculate contribution for each pair of paths
                for path_sire in paths_sire:
                    for path_dam in paths_dam:
                        n_sire = len(path_sire) - 1
                        n_dam = len(path_dam) - 1
                        # Calculate inbreeding coefficient of the ancestor (Fa)
                        Fa = graph.nodes[ancestor].get('COI', 0.05)
                        contribution = (0.5 ** (n_sire + n_dam + 1)) * (1 + Fa)
                        coi += contribution
                        # print(f"Contribution: {contribution}")
                        # print(f"COI: {coi}")
                        if contribution > 0:
                            graph.nodes[ancestor]['COI'] = contribution
                        calculation_steps.append({
                            'ancestor': ancestor,
                            'Fa': contribution,
                            'n_sire': n_sire,
                            'n_dam': n_dam,
                            'contribution': contribution
                        })

            return coi, calculation_steps

        # Initialize all nodes with COI of 0 and empty steps
        for node in graph.nodes:
            graph.nodes[node]['COI'] = 0.0
            graph.nodes[node]['steps'] = []

        # Recalculate COI for nodes with both a sire and a dam and overwrite if COI is greater than 0
        for node in graph.nodes:
            if graph.in_degree(node) == 2:  # Only calculate COI for offspring with both sire and dam
                coi_value, steps = calculate_wright_coi_corrected(graph, node)
                if coi_value > 0:
                    graph.nodes[node]['COI'] = coi_value
                    graph.nodes[node]['steps'] = steps
            else:
                print(f"Skipping node: {node} due to missing parents")

        return graph

    # Global cache for COI values
    coi_cache = {}

    def calculate_pedigree_coi(graph):
        def calculate_wright_coi_corrected(graph, node, generations=6):
            # Check if COI has already been calculated for this node and is greater than 0
            # if node in coi_cache and coi_cache[node]['coi'] > 0:
            #     # Return cached COI and steps
            #     return coi_cache[node]['coi'], coi_cache[node]['steps']
            
            predecessors = list(graph.predecessors(node))
            if len(predecessors) != 2:
                # Node must have exactly two parents to calculate COI
                return 0.5, []
            
            sire, dam = predecessors
            # Find common ancestors of sire and dam within the specified number of generations
            sire_ancestors = nx.ancestors(graph, sire)
            dam_ancestors = nx.ancestors(graph, dam)
            common_ancestors = sire_ancestors.intersection(dam_ancestors)
            coi = 0.05  # Start with a base COI
            calculation_steps = []
            
            for ancestor in common_ancestors:
                # Get all paths from the ancestor to both sire and dam
                paths_sire = list(nx.all_simple_paths(graph.reverse(), source=sire, target=ancestor, cutoff=generations))
                paths_dam = list(nx.all_simple_paths(graph.reverse(), source=dam, target=ancestor, cutoff=generations))
                for path_sire in paths_sire:
                    for path_dam in paths_dam:
                        n_sire = len(path_sire) - 1
                        n_dam = len(path_dam) - 1
                        Fa = graph.nodes[ancestor].get('COI', 0.05)
                        contribution = (0.5 ** (n_sire + n_dam + 1)) * (1 + Fa) 
                        coi += contribution
                        graph.nodes[ancestor]['COI'] = coi
                        calculation_steps.append({
                            'ancestor': ancestor,
                            'Fa': coi,
                            'n_sire': n_sire,
                            'n_dam': n_dam,
                            'contribution': coi
                        })
            # Cache the COI value and the steps if COI is greater than 0
            if coi > 0:
                coi_cache[node] = {'coi': coi, 'steps': calculation_steps}
            return coi, calculation_steps

        # Initialize all nodes with COI of 0 and empty steps
        for node in graph.nodes:
            graph.nodes[node]['COI'] = 0.0
            graph.nodes[node]['steps'] = []

        # Recalculate COI for nodes with both a sire and a dam and overwrite if COI is greater than 0
        for node in graph.nodes:
            if graph.in_degree(node) == 2:  # Only calculate COI for offspring with both sire and dam
                coi_value, steps = calculate_wright_coi_corrected(graph, node)
                if coi_value > 0:
                    graph.nodes[node]['COI'] = coi_value
                    graph.nodes[node]['steps'] = steps
            # else:
                # print(f"Skipping node: {node} due to missing parents")

        return graph

    def createOffspringGraph(G_sire, G_dam):
        # Create a new directed graph for the combined pedigree
        G_combined = nx.DiGraph()
        print(f"Size of G_sire: {len(G_sire.edges())}")
        print(f"Size of G_dam: {len(G_dam.edges())}")
        # Add nodes and edges from G_sire
        for node in G_sire.nodes():
            G_combined.add_node(node)
        for edge in G_sire.edges(data=True):  # Preserve edge attributes
            G_combined.add_edge(edge[0], edge[1], **edge[2])

        # Add nodes and edges from G_dam
        for node in G_dam.nodes():
            if not G_combined.has_node(node):
                G_combined.add_node(node)
        for edge in G_dam.edges(data=True):
            if not G_combined.has_edge(edge[0], edge[1]):
                G_combined.add_edge(edge[0], edge[1], **edge[2])

        # Find sire and dam based on out-degree of 0
        root_candidates_sire = [node for node in G_sire.nodes() if G_sire.out_degree(node) == 0]
        sire_to_breed = root_candidates_sire[0] if root_candidates_sire else None

        root_candidates_dam = [node for node in G_dam.nodes() if G_dam.out_degree(node) == 0]
        dam_to_breed = root_candidates_dam[0] if root_candidates_dam else None

        print(f"Sire  to breed: {sire_to_breed}")
        print(f"Dam to breed: {dam_to_breed}")

        if sire_to_breed is None or dam_to_breed is None:
            raise ValueError("Cannot determine sire or dam to breed from the given graphs.")

        # Add offspring node and edges from sire and dam to the offspring
        offspring_node = sire_to_breed + "_" +  dam_to_breed  # You can change this to be more descriptive
        G_combined.add_node(offspring_node)
        G_combined.add_edge(sire_to_breed, offspring_node)
        G_combined.add_edge(dam_to_breed, offspring_node)
        print(f"Size of offspring graph: {len(G_combined.nodes())}")

        return G_combined, offspring_node


        components.html(js_code)

    def highlight_gradient(val, cmap_name='gist_heat', vmin=20, vmax=50):
    
        if val <= vmin:
            return ''
        
        # Normalize the value between 0 and 1
        norm_val =  1- (val - vmin) / (vmax - vmin)
        
        # Get the colormap
        cmap = plt.cm.get_cmap(cmap_name)
        
        # Get RGB values (returns rgba, we'll drop the alpha)
        rgba = cmap(norm_val)
        
        # Convert RGB values from 0-1 scale to 0-255 scale
        rgb = [int(x * 255) for x in rgba[:3]]
        
        return f'background-color: rgb({rgb[0]},{rgb[1]},{rgb[2]})'

    def plot_avg_row_plotly(df):
        # Extract the Avg row
        avg_values = df.loc['Avg']
        
        # Create a Plotly line plot
        fig = go.Figure(
            data=[go.Scatter(x=avg_values.index, y=avg_values.values, mode='lines+markers', line=dict(color='blue'))]
        )
        
        # Update layout for better readability
        fig.update_layout(
            title='Average COI Values by Sire',
            xaxis_title='Sire Names',
            yaxis_title='Average Values',
            xaxis_tickangle=-45,
            width = 1200,
            autosize=True
        )
        
        # Show the plot
        st.plotly_chart(fig)

    def grey_background(val):
        return 'background-color: grey; border: 1px solid white'

   
    # log_to_console("Starting the application...")
    st.title('Cattle Pedigree Graphing')
    st.write("This is a tool to graph cattle pedigrees.")
    st_Build_Sidebar()
    if st.session_state.sirePedigreeFile and st.session_state.damPedigreeFile: 
        start_sire_time = time.time()
        # Load sire and dam data in wide format
        # sire_df_wide = pd.read_csv('data_files/5gen_AF33641_FatherOf_7A01.csv')
        # sire_df_wide = pd.read_csv('data_files/5gen_8_Bulls.csv')     
        # dam_df_wide = pd.read_csv('data_files/5GenPedigree_SingleFemale7A01_ArtesianRanch.csv')
        # dam_df_wide = pd.read_csv('data_files/5GenArtesianFullBloodDams.csv')
        sire_df_wide = pd.read_csv(st.session_state.sirePedigreeFile)
        dam_df_wide = pd.read_csv(st.session_state.damPedigreeFile)
        resultsList = []
        sireRowLen = len(sire_df_wide)
        damRowLen = len(dam_df_wide)
        st.write(f"Sires Processing : {sireRowLen}")
        st.write(f"Dams Processing : {damRowLen}")
        # Iterate over each sire and dam
        for index_sire, sire_row in sire_df_wide.iterrows():
            sire_id = str(sire_row['animal_registration']).strip()
            sire_name = str(sire_row['animal_name']).strip()  # Assuming column 'animal_name'
            # Import and process the row for this sire in long format
            df_long_sire = import_data_and_format(sire_row)
            G_sire = nx.DiGraph()
            build_pedigree_graph(df_long_sire, G_sire, type='sire')
            # Calculate COI and display the graph
            G_sire = calculate_pedigree_coi(G_sire)
            # Iterate over each dam for this sire
            for index_dam, dam_row in dam_df_wide.iterrows():
                print(f"Processing sire: {sire_row['animal_registration']} and dam: {dam_row['animal_registration']}**************")
                dam_id = str(dam_row['animal_registration']).strip()
                dam_name = str(dam_row['animal_name']).strip()
                df_long_dam = import_data_and_format(dam_row)
                G_dam = nx.DiGraph()
                build_pedigree_graph(df_long_dam, G_dam, type='dam')
                G_dam = assign_generations_to_edges(G_dam)
                G_dam = calculate_pedigree_coi(G_dam)
                G_offspring, offspringNode = createOffspringGraph(G_sire, G_dam)
                G_offspring = calculate_pedigree_coi(G_offspring)
                resultsDict  = {
                    "offspring" : offspringNode,
                    "sire" : sire_id,
                    "dam" : dam_id,
                    "sire_name" : sire_name,
                    "dam_name" : dam_name,
                    "sire_coi" : G_sire.nodes[sire_id]['COI'],
                    "dam_coi": G_dam.nodes[dam_id]['COI'],
                    "offspring_coi": G_offspring.nodes[offspringNode]['COI'],
                    "sire_Graph": G_sire,
                    "dam_Graph": G_dam,
                    "offspring_Graph": G_offspring
                    
                }
                resultsList.append(resultsDict)
        coi_df = pd.DataFrame()
        # Assuming resultsList is populated with your resultsDict entries
        for result in resultsList:
            sire_name = result['sire_name']
            dam_name = result['dam_name']
            offspring_coi = result['offspring_coi']
            
            # Set the COI value for the offspring in the corresponding sire column and dam row
            coi_df.at[dam_name, sire_name] = offspring_coi
        # Fill any missing values with NaN if needed
        coi_df = coi_df.fillna(float('nan'))
        sorted_coi_df = pd.DataFrame()
        for column in coi_df.columns:
            # Sort the column values in descending order
            sorted_coi_df[column] = coi_df[column].sort_values(ascending=False).values
        sorted_coi_df.to_pickle("data_files/sorted_coi_df.pkl")
        # Set the index back to the original row names (dam names)
        sorted_coi_df.index = coi_df.index
        sorted_coi_df = sorted_coi_df.apply(pd.to_numeric, errors='coerce')  # Convert columns to numeric, coercing errors to NaN
        # sorted_coi_df = sorted_coi_df.round(2)
        # Convert to percentages and append '%' symbol
        sorted_coi_df = sorted_coi_df * 100  # Convert to percentage
        high_row= sorted_coi_df.max()
        low_row = sorted_coi_df.min()
        avg_row = sorted_coi_df.mean()
        summary_df = pd.DataFrame([high_row, avg_row, low_row], index=['High', 'Avg', 'Low'])
        df_with_summary = pd.concat([summary_df, sorted_coi_df], ignore_index=False)
        df_with_summary = df_with_summary[df_with_summary.loc['Avg'].sort_values(ascending=False).index]
        
        styled_df = df_with_summary.style.applymap(
        highlight_gradient, 
        subset=pd.IndexSlice[df_with_summary.index[3:], :]
        )
        # styled_df = sorted_coi_df.style.applymap(highlight_gradient)
        print(type(styled_df))
        
        styled_df = df_with_summary.style.applymap(
            highlight_gradient, 
            subset=pd.IndexSlice[df_with_summary.index[3:], :]
        ).applymap(
            grey_background, 
            subset=pd.IndexSlice[['High', 'Avg', 'Low'], :]
        )
        # sorted_coi_df = sorted_coi_df.round(2).astype(str) + '%' 
        # Display the sorted DataFrame
        styled_df.format(precision=2)
        styled_df = styled_df.format("{:.2f}%")
        stop_sire_time = time.time()
        st.write(f"Time taken: {round(stop_sire_time - start_sire_time, 2)} seconds")
        st.table(styled_df)
        
        plot_avg_row_plotly(df_with_summary)
    else:
        st.warning("Please upload a valid pedigree files.")
