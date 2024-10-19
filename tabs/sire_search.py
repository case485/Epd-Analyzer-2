import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from lib.helper_functions import *

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

    def buildSearchQuery ():
        # Define the search form
        #Get industry Data: 
        minced = ""
        maxbwt = ""
        minwwt = ""
        minywt = ""
        mintm = ""
        minmilk = ""
        mingrowth = ""
        options = st.multiselect(
            "Select EPD(s) to optimize Bull Selection with:",
            ["CED", "BW", "WW", "YW","TM", "MK", "Growth"],
            ["TM"],
        )

        st.write("You selected:", options)
        for option in options:
            epd = option
            
            value = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == '5%'][epd].values[0]
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
            elif epd == "MK":
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
            }
            st.write(f"Query Parameters: {params}")
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


    soup = buildSearchQuery()
    if soup:
        df = searchSoup(soup)
        st.dataframe(df)