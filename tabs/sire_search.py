import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from lib.helper_functions import *
import plotly.express as px
from tabs import coi_analyzer2, culling, home, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar  # Import the sidebar

st.session_state.update(st.session_state)
def show():
    
    def searchSoup(soup):
        # Find all rows with cow data
        cow_rows = soup.find_all('tr', id=lambda x: x and x.startswith('tr_'))
        cows_data = []
        for row in cow_rows:
            cow_info = row.find_all('td')
            # Extract registration number, tattoo, and name
            reg_no = cow_info[0].find('a').text.strip()
            tattoo = cow_info[0].find('b', text='Tattoo:').next_sibling.strip()
            name = cow_info[0].find('b', text='Name:').next_sibling.strip()
            # Extract EPDs
            epds = {}
            epd_headers = ['CED', 'BW', 'WW', 'YW', 'Milk', 'TM', 'Growth']
            for i, header in enumerate(epd_headers):
                epd_cell = cow_info[i + 2]
                epd_values = [val.strip() for val in epd_cell.strings if val.strip()]
                epds[f'{header}_EPD'] = epd_values[0] if len(epd_values) > 0 else ''
                epds[f'{header}_CNG'] = epd_values[1] if len(epd_values) > 0 else ''
                epds[f'{header}_ACC'] = epd_values[2] if len(epd_values) > 3 else ''
                epds[f'{header}_Rank'] = epd_values[3] if len(epd_values) > 3 else ''
                if len(epd_values) < 3:
                    epds[f'{header}_Rank'] = epd_values[1]
            cow_data = {
                'Registration': reg_no,
                'Tattoo': tattoo,
                'Name': name,
                **epds
            }
            cows_data.append(cow_data)
        # Create a DataFrame from the parsed data
        df = pd.DataFrame(cows_data)
        df = df.applymap(lambda x: x.replace('>', '').replace('<', ''))
        return df

    def epd_composite_score_app(df, includeWeightsToggle):
                # Load your dataframe
                # Define a function to calculate composite score
                columns_with_underscore = [col for col in df.columns if '_' in col]
                industryRowHigh = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "High"]
                industryRowLow = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "Low"]
                for col in columns_with_underscore:
                    df[col] = pd.to_numeric(df[col], errors='coerce') 
                    
                def calculate_composite_score(row, includeWeights):
                    if includeWeights == True:
                        composite_score = (
                            row['CED_EPD'] /  float(industryRowHigh["CED"][1])* row['CED_ACC'] +
                            # row['BW_EPD'] / float(industryRow["BW"][1])* row['BW_ACC'] +
                            (float(industryRowHigh.loc[1, "BW"]) - row['BW_EPD']) / (float(industryRowHigh.loc[1, "BW"]) - float(industryRowLow.loc[3, "BW"])) * row['BW_ACC'] +
                            row['WW_EPD'] / float(industryRowHigh["WW"][1])* row['WW_ACC'] +
                            row['YW_EPD'] / float(industryRowHigh["YW"][1]) * row['YW_ACC'] +
                            row['Milk_EPD'] / float(industryRowHigh["MK"][1])* row['Milk_ACC'] +
                            row['TM_EPD'] / float(industryRowHigh["TM"][1])+
                            row['Growth_EPD'] / float(industryRowHigh["Growth"][1])
                        )
                        composite_score = round(composite_score, 2)
                        return composite_score
                    else: 
                        composite_score = (
                            row['CED_EPD'] /  float(industryRowHigh["CED"][1]) +
                            # row['BW_EPD'] / float(industryRow["BW"][1])* row['BW_ACC'] +
                            (float(industryRowHigh.loc[1, "BW"]) - row['BW_EPD']) / (float(industryRowHigh.loc[1, "BW"]) - float(industryRowLow.loc[3, "BW"])) +
                            row['WW_EPD'] / float(industryRowHigh["WW"][1]) +
                            row['YW_EPD'] / float(industryRowHigh["YW"][1])  +
                            row['Milk_EPD'] / float(industryRowHigh["MK"][1]) +
                            row['TM_EPD'] / float(industryRowHigh["TM"][1])+
                            row['Growth_EPD'] / float(industryRowHigh["Growth"][1])
                        )
                        composite_score = round(composite_score, 2)
                        return composite_score
                        
                with st.spinner('Calculating...'):
                    df['Composite Score'] = df.apply(lambda row: calculate_composite_score(row, includeWeights=includeWeightsToggle), axis=1)
                    df_sorted = df.sort_values(by='Composite Score',ascending=False)
                return(df_sorted)

    def buildSearchQuery (options, formatted_sliderValue,rowsReturnedSlider):
        # Define the search form
        #Get industry Data: 
        minced = ""
        maxbwt = ""
        minwwt = ""
        minywt = ""
        mintm = ""
        minmilk = ""
        mingrowth = ""
        
        for option in options:
            epd = option
            
            value = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == formatted_sliderValue][epd].values[0]
            st.write(f"You selected: {epd} {value}")
            if epd == "CED":
                minced = value
            elif epd == "BW":
                maxbwt = value
            elif epd == "WW":
                minwwt = value
            elif epd == "YW":
                minywt = value
            elif epd == "TM":
                mintm = value
            elif epd == "Milk":
                minmilk = value
            elif epd == "Growth":
                mingrowth = value
            else:
                st.write("Invalid EPD selected.")
        

        if st.multiselect:
            params = {
                "minced": minced,
                "maxbwt": maxbwt,
                "minwwt": minwwt,
                "minywt": minywt,
                "minmilk": minmilk,
                "mintm": mintm,
                "mingrowth": mingrowth,
                "animal_sex": "B",
                "rows": rowsReturnedSlider,
            }
            # Filter out empty parameters
            params = {k: v for k, v in params.items() if v}
            # Simulate the API request (replace with actual API endpoint)
            url = "https://akaushi.digitalbeef.com/modules/DigitalBeef-Landing/ajax/search_results_epd.php" 
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    return(soup)
                else:
                    st.error(f"Error fetching results: {response.status_code}")
                    return None
            except requests.RequestException as e:
                st.error(f"Error fetching results: {e}")
                return None
   
    def score_color(val):
        color = ''
        if val < 2:
            color = 'background-color: #ff6666'  # Red for lower scores
        elif 2 <= val < 5:
            color = 'background-color: #ffcc66'  # Orange for mid-range scores
        elif 5 <= val < 8:
            color = 'background-color: #66ff66'  # Green for higher scores
        else:
            color = 'background-color: #6666ff'  # Blue for top scores
        return color
   
    def download_column_as_csv(df, column_name, filename="data.csv", include_header=False):
        """
        Creates a download button in Streamlit to download a specific DataFrame column as CSV.
        
        Parameters:
        df (pandas.DataFrame): The source DataFrame
        column_name (str): Name of the column to export
        filename (str): Desired name of the downloaded file
        include_header (bool): Whether to include the column header in the CSV
        """
        # Extract the specified column and convert to DataFrame
        column_df = df[[column_name]]
        
        # Convert DataFrame to CSV with UTF-8 encoding
        csv = column_df.to_csv(
            index=False, 
            header=include_header,
            encoding='utf-8'
        )
        
        # Create the download button with UTF-8 BOM for Excel compatibility
        csv_with_bom = '\ufeff' + csv  # Add BOM for better UTF-8 compatibility
        
        st.download_button(
            label=f"Download {column_name} data",
            data=csv_with_bom,
            file_name=filename,
            mime='text/csv'
        )


   
    options = st.multiselect(
        "Select EPD(s) to optimize Bull Selection with:",
        ["CED", "BW", "WW", "YW","TM", "MK", "Growth"],
        ["TM"],
    )
    custom_values = list(range(1, 6)) + list(range(10, 96, 5))
    slider_value = st.select_slider(
        "Select the Industry Association Percentile Rank you would like to use for your search:",
        options=custom_values,
        value=5,
    )
    formatted_sliderValue = f"{slider_value}%"
    rowsReturnedSlider  = st.select_slider('Select number of Sires to Evalaute', options=[10, 50, 100, 500], value=50)
    sireSearchButton = st.button("Search Sire Database")
    includeWeightsToggle = st.checkbox("Include Accuracy Weights?", value=False)
    
    if includeWeightsToggle:
        st.write("Weights will be included in the composite score calculation.")
        includeWeightsToggle = True
    else:
        st.write("Weights will not be included in the composite score calculation.")
        includeWeightsToggle = False
    # Save the profiling stats to a file or display it
    # Start profiling when the search button is clicked
    if sireSearchButton:
        # Call functions to search and process data
        soup = buildSearchQuery(options, formatted_sliderValue, rowsReturnedSlider)
        df = searchSoup(soup)
        df = epd_composite_score_app(df, includeWeightsToggle)
        # Display dataframe and plots
        col_to_move = 'Composite Score'
        cols = list(df.columns)
        cols.remove(col_to_move)
        df = df[[col_to_move] + cols]
        styled_df = df.style.applymap(score_color, subset=['Composite Score'])
        st.data_editor(df, column_config={
            "Composite Score": st.column_config.ProgressColumn(
                "Composite Score",
                help="Indexed value across all EPDs",
                format="%f",
                min_value=0,
                max_value=8,
            ),
        }, hide_index=True)
        

        # st.dataframe(df)
        melted_df = df.melt(id_vars=["Name","Registration", "Composite Score"], 
                            value_vars=['CED_EPD', "BW_EPD", "WW_EPD", "YW_EPD", "Milk_EPD", "TM_EPD", "Growth_EPD", "Composite Score"],
                            var_name="EPD Type", value_name="EPD Value")

        # Create the line plot
        fig = px.line(melted_df, x="EPD Type", y="EPD Value", color="Name", markers=True)
        fig.update_layout(width=1500)
        st.plotly_chart(fig)

        fig = px.scatter(df, x="Name", y="Composite Score", hover_data=["Registration"], color="Name")
        fig.update_layout(width=1500)
        st.plotly_chart(fig)
        st.dataframe(df)
        download_column_as_csv(df, "Registration", "SireRegNumList.csv")
