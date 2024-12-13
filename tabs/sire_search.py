import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from functools import partial
from lib.helper_functions import *
import plotly.express as px
from tabs import coi_analyzer2, culling, herd_overview, topAndBottom, visualizations, raw_data, logging, sire_search
from sidebar import sidebar

st.session_state.update(st.session_state)
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = pd.DataFrame()

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

    def buildSearchQuery(options, formatted_sliderValue, rowsReturnedSlider):
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
            color = 'background-color: #ff6666'
        elif 2 <= val < 5:
            color = 'background-color: #ffcc66'
        elif 5 <= val < 8:
            color = 'background-color: #66ff66'
        else:
            color = 'background-color: #6666ff'
        return color

    def download_column_as_csv(df, column_name,label,  filename="data.csv", include_header=False):
        column_df = df[[column_name]]
        csv = column_df.to_csv(
            index=False, 
            header=include_header,
            encoding='utf-8'
        )
        csv_with_bom = '\ufeff' + csv
        st.download_button(
            label=label,
            data=csv_with_bom,
            file_name=filename,
            mime='text/csv'
        )

    def style_rank_columns(df):
        def highlight_low_ranks(series):
            return [f'font-weight: bold; color: green; font-size: 150pt' if (str(series.name).endswith('_Rank') and v < 5) else '' 
                    for v in series]
        styled_df = df.style.apply(highlight_low_ranks).format(precision=2)
        return styled_df

    # Initialize session states
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = pd.DataFrame()
    if 'current_df' not in st.session_state:
        st.session_state.current_df = None
    if 'show_editor' not in st.session_state:
        st.session_state.show_editor = False

    # UI Elements
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
    rowsReturnedSlider = st.select_slider('Select number of Sires to Evaluate', 
                                        options=[10, 50, 100, 500], 
                                        value=50)
    
    sireSearchButton = st.button("Search Sire Database")
    includeWeightsToggle = st.checkbox("Include Accuracy Weights?", value=False)

    if includeWeightsToggle:
        st.write("Weights will be included in the composite score calculation.")
    else:
        st.write("Weights will not be included in the composite score calculation.")

    # Main search and display logic
    if sireSearchButton:
        st.session_state.show_editor = True
        soup = buildSearchQuery(options, formatted_sliderValue, rowsReturnedSlider)
        df = searchSoup(soup)
        df = epd_composite_score_app(df, includeWeightsToggle)
        
        # Clean up columns
        if 'TM_ACC' in df.columns:
            df = df.drop('TM_ACC', axis=1)
        if 'Growth_ACC' in df.columns:
            df = df.drop('Growth_ACC', axis=1)
        if 'Tattoo' in df.columns:
            df = df.drop('Tattoo', axis=1)
        df = df.loc[:, ~df.columns.str.endswith('_CNG')]

        df["Save_Sire"] = False
        df = df[['Save_Sire'] + [col for col in df.columns if col != 'Save_Sire']]
        st.session_state.current_df = df

    # Display editor if we have data
    if st.session_state.show_editor and st.session_state.current_df is not None:
        st.write("Select sires by editing cells in the table below:")
        



        st.write(st.session_state.current_df.head())
        editor_container = st.empty()
        editor_response = editor_container.data_editor(
            st.session_state.current_df,
            column_config={
                "Save_Sire": st.column_config.CheckboxColumn(
                    "Save_Sire",
                    help="Select sires to save",
                    default=False,
                )
            },
            hide_index=True,
            disabled=[col for col in st.session_state.current_df.columns if col != "Save_Sire"]
        )






        download_column_as_csv(st.session_state.current_df, "Registration","Download ALL Registration Numbers as csv", "AllSireRegNumList.csv")
        # # Handle selections
        checkboxButton = st.button("List Selected Sire(s)")
        if checkboxButton:
            selected_rows = editor_response[editor_response["Save_Sire"] == True].copy()
            if not selected_rows.empty:
                st.session_state.filtered_df = pd.concat(
                    [st.session_state.filtered_df, selected_rows]
                ).drop_duplicates()
            st.session_state.show_editor = False


        # Visualizations
        melted_df = st.session_state.current_df.melt(
            id_vars=["Name", "Registration", "Composite Score"],
            value_vars=['CED_EPD', "BW_EPD", "WW_EPD", "YW_EPD", "Milk_EPD", "TM_EPD", "Growth_EPD", "Composite Score"],
            var_name="EPD Type",
            value_name="EPD Value"
        )

        fig = px.line(melted_df, x="EPD Type", y="EPD Value", color="Name", markers=True)
        fig.update_layout(width=1500)
        st.plotly_chart(fig)

        fig = px.scatter(st.session_state.current_df, x="Name", y="Composite Score", 
                        hover_data=["Registration"], color="Name")
        fig.update_layout(width=1500)
        st.plotly_chart(fig)

        

    # Display saved selections
    if 'filtered_df' in st.session_state and not st.session_state.filtered_df.empty:
        st.write("Saved Selections:")
        st.write(st.session_state.filtered_df)
        download_column_as_csv(st.session_state.current_df, "Registration", "Download Selected Registration Numbers as csv" ,"SelectedSireRegNums.csv")
    
    # Clear button
    if st.button("Clear Saved Selections"):
        st.session_state.filtered_df = pd.DataFrame()
        st.session_state.current_df = None
        st.session_state.show_editor = False
        st.rerun()