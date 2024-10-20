import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from lib.helper_functions import *
import plotly.express as px

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


    def epd_composite_score_app(df):
                # Load your dataframe
                # Define a function to calculate composite score
                columns_with_underscore = [col for col in df.columns if '_' in col]
                industryRow = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "High"]
                for col in columns_with_underscore:
                    df[col] = pd.to_numeric(df[col], errors='coerce') 
                    
                def calculate_composite_score(row):
                    composite_score = (
                        row['CED_EPD'] /  float(industryRow["CED"][1])* row['CED_ACC'] +
                        row['BW_EPD'] / float(industryRow["BW"][1])* row['BW_ACC'] +
                        row['WW_EPD'] / float(industryRow["WW"][1])* row['WW_ACC'] +
                        row['YW_EPD'] / float(industryRow["YW"][1]) * row['YW_ACC'] +
                        row['Milk_EPD'] / float(industryRow["MK"][1])* row['Milk_ACC'] +
                        row['TM_EPD'] / float(industryRow["TM"][1])+
                        row['Growth_EPD'] / float(industryRow["Growth"][1])
                    )
                    composite_score = round(composite_score, 2)
                    return composite_score
                df['Composite Score'] = df.apply(calculate_composite_score, axis=1)
                df_sorted = df.sort_values(by='Composite Score',ascending=False)
                return(df_sorted)













    def buildSearchQuery (options, formatted_sliderValue):
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
                "rows": 500,
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
   
   
    options = st.multiselect(
                "Select EPD(s) to optimize Bull Selection with:",
                ["CED", "BW", "WW", "YW","TM", "Milk", "Growth"],
                ["TM"],
            )
    custom_values = list(range(1, 6)) + list(range(10, 96, 5))
    # Create the slider using this list of custom values
    slider_value = st.select_slider(
        "Select the Percentile Rank you would like to use for your search:",
        options=custom_values,
        value=5,
    )
    formatted_sliderValue = f"{slider_value}%"

    sireSearchButton = st.button("Search Sire Database")
    if sireSearchButton:
        soup = buildSearchQuery(options, formatted_sliderValue)
        df = searchSoup(soup)
        df = epd_composite_score_app(df)
        st.dataframe(df)
        
        
        
        melted_df = df.melt(id_vars=["Name", "Composite Score"], 
                    value_vars=['CED_EPD', "BW_EPD", "WW_EPD", "YW_EPD", "Milk_EPD", "TM_EPD", "Growth_EPD", "Composite Score"],
                    var_name="EPD Type", value_name="EPD Value")

        # Create the line plot
        fig = px.line(melted_df, x="EPD Type", y="EPD Value", color="Name", markers=True)
        fig.update_layout(width=1500)
        # Plot in Streamlit
        st.plotly_chart(fig)
        
        fig = px.scatter(df, x="Name", y="Composite Score",hover_data="Registration", color="Name")

        # Adjust the figure size (optional)
        fig.update_layout(width=1500)
        # Plot in Streamlit
        st.plotly_chart(fig)