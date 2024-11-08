from bs4 import BeautifulSoup
import streamlit as st
import re
import pandas as pd
import requests
import os
# import camelot
from config import *
from datetime import datetime



def log_error(message):
    # Check if the 'error_log' exists in session_state, if not, create it
    if 'error_log' not in st.session_state:
        st.session_state['error_log'] = []

    # Append the error message to the error log
    st.session_state['error_log'].append(message)

def get_percentile_rank_url_by_pattern():
    aaUrl = AA_URL
    pdf_path = INDUSTRY_PERCENTILE_FILE
    response = requests.get(aaUrl)
    html_content = response.text
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    if response.status_code == 200:
        # Save the PDF to a local file
        pattern = re.compile(r'Sire_Summary/\d{8} Akaushi Percentile Ranks\.pdf')
        # Find all 'a' tags with href attributes
        for a_tag in soup.find_all('a', href=True):
            # If the href matches the pattern, return the full URL
            if pattern.search(a_tag['href']):
                aaPercentileRankUrl =  a_tag['href']
                #Now i have the url for  the pdf i need to download it and save it to the pdf_path
                pdfResponse = requests.get(aaPercentileRankUrl)
                if pdfResponse.status_code == 200:
                    # Open a file in write-binary mode to save the PDF
                    with open(pdf_path, 'wb') as pdf_file:
                        pdf_file.write(pdfResponse.content)
                    print(f"PDF downloaded successfully: {pdf_path}")
                    return(pdf_path)
                else:
                    print(f"Failed to download the PDF. Status code: {pdfResponse.status_code}")
                    return None
    else:
        print(f"Failed to get to url. Status code: {response.status_code}")
    return None

def extract_IndustryPercentileRankTables_from_pdf():
    # URL of the PDF file
    #test if file exists 
    if os.path.isfile("datafiles/activeSiresPercentileRankDf.pkl"):
        #read in pickle file to dataframe
        activeSiresPercentileRankDf = pd.read_pickle("datafiles/activeSiresPercentileRankDf.pkl")
        activeDamsPercentileRankDf = pd.read_pickle("datafiles/activeDamsPercentileRankDf.pkl")
        nonParentsPercentileRankDf = pd.read_pickle("datafiles/nonParentsPercentileRankDf.pkl")
        # st.info("Data loaded from local files.")
        return (activeSiresPercentileRankDf, activeDamsPercentileRankDf, nonParentsPercentileRankDf)
    else:
        st.warning("Data not found locally. Downloading from website.")


def epd_composite_score_app(df):
            # st.write("In epd_composite_score_app")
            # st.dataframe(df)
            # Load your dataframe
            # Define a function to calculate composite score
            
            def calculate_composite_score(row, weights):
                try: 
                    if row['Designation'] == "Bull":
                        industryRowHigh = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "High"]
                        industryRowLow = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "Low"]
                    elif row['Designation'] == "Dam":
                        industryRowHigh = st.session_state.activeDamsPercentileRankDf.loc[st.session_state.activeDamsPercentileRankDf['Categories'] == "High"]
                        industryRowLow = st.session_state.activeDamsPercentileRankDf.loc[st.session_state.activeDamsPercentileRankDf['Categories'] == "Low"]
                    elif row['Designation'] == "Non-Parent":
                        industryRowHigh = st.session_state.nonParentsPercentileRankDf.loc[st.session_state.nonParentsPercentileRankDf['Categories'] == "High"]
                        industryRowLow = st.session_state.nonParentsPercentileRankDf.loc[st.session_state.nonParentsPercentileRankDf['Categories'] == "Low"]
                    elif row['Designation'] == "Steer":
                        industryRowHigh = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "High"]
                        industryRowLow = st.session_state.activeSiresPercentileRankDf.loc[st.session_state.activeSiresPercentileRankDf['Categories'] == "Low"]
                    else:
                        st.error(f"Designation not recognized: {row['Designation']}")
                    composite_score = (
                        row['CED'] / float(industryRowHigh["CED"][1]) * weights['CED'] +
                        (float(industryRowHigh.loc[1, "BW"]) - row['BW']) / (float(industryRowHigh.loc[1, "BW"]) - float(industryRowLow.loc[3, "BW"])) * weights['BW'] +
                        row['WW'] / float(industryRowHigh["WW"][1])* weights['WW'] +
                        row['YW'] / float(industryRowHigh["YW"][1])* weights['YW'] +
                        row['MK'] / float(industryRowHigh["MK"][1])* weights['MK'] +
                        row['TM'] / float(industryRowHigh["TM"][1])* weights['TM'] +
                        row['Growth'] / float(industryRowHigh["Growth"][1])* weights['Growth']
                    )
                except:
                    st.error(f"Error calculating composite score for row: {row}")
                    composite_score = 0.0
                return composite_score

            # Sidebar sliders to adjust weights
            st.sidebar.write("### Adjust Weights for Compsite Score")

            weights = {
                'CED': st.sidebar.slider('CED Weight', 0.0, 2.0, 1.0, .5),
                'BW': st.sidebar.slider('BW Weight', 0.0, 2.0, 1.0, .5),
                'WW': st.sidebar.slider('WW Weight', 0.0, 2.0, 1.0, .5),
                'YW': st.sidebar.slider('YW Weight', 0.0, 2.0, 1.0, .5),
                'MK': st.sidebar.slider('Milk Weight', 0.0, 2.0, 1.0, .5),
                'TM': st.sidebar.slider('Total Maternal Weight', 0.0, 2.0, 1.0, .5),
                'Growth': st.sidebar.slider('Growth Idx Weight', 0.0, 2.0, 1.0, .5),
            }
             #DEBUG                      
            df['Composite Score'] = df.apply(calculate_composite_score, axis=1, weights=weights)
            return(df)

def clean_and_modify_CattlemaxDfs(df):
    # st.write("In clean_and_modify_CattlemaxDfs")
    # st.dataframe(df)
    today = datetime.today()
    df = df.rename(columns={
        'Calving Ease Direct EPD': 'CED',
        'Calving Ease Direct Acc': 'CED Acc',
        'Birth Weight EPD': 'BW',
        'Birth Weight Acc': 'BW Acc',
        'Weaning Weight EPD': 'WW',
        'Weaning Weight Acc': 'WW Acc',
        'Yearling Weight EPD': 'YW',
        'Yearling Weight Acc': 'YW Acc',
        'Milk EPD': 'MK',
        'Milk Acc': 'MK Acc',
        'Total Maternal EPD': 'TM'
    })
    df['Growth'] = (- 0.301 * df['BW'] ) + \
                   ( 0.039 * df['WW']) + \
                   (1.098 * df['YW'] ) - 6.815
    df['Date of Birth'] = pd.to_datetime(df['Date of Birth'], errors='coerce')
    df['Year_Born'] = df['Date of Birth'].dt.year
    df['Age'] = (pd.to_datetime('today').year) - df['Date of Birth'].dt.year
    def assign_designation(row):
        if pd.isnull(row['Year_Born']):
            return 'Unknown'  # Handle cases where Year_Born is missing
        
        age_in_years = today.year - int(row['Year_Born'])
        
        if row['Type or Sex'] == 'B' and age_in_years >= 2:
            return 'Bull'
        elif row['Type or Sex'] == 'C' and age_in_years >= 2:
            return 'Dam'
        elif row['Type or Sex'] in ['B', 'C'] and age_in_years < 2:
            return 'Non-Parent'
        elif row['Type or Sex'] == 'S':
            return 'Steer'
        
        return 'Unknown'  # Default for rows that don't match any condition
    df['Designation'] = df.apply(assign_designation, axis=1)
    
    return(df)


def find_percentile_for_epd(value, epd_column, df):
    """
    Given a number and an EPD column name, return the industry percentile rank based on the input DataFrame.
    
    Args:
        value (float): The value of the EPD.
        epd_column (str): The EPD column to search (e.g., 'CED', 'BW', 'WW').
        df (pd.DataFrame): The DataFrame containing percentile ranks.

    Returns:
        str: The corresponding percentile rank or a message if value is out of bounds.
    """
    # Percentile rows typically start from the row with 1% and go downwards
    percentiles = df.iloc[4:]  # Exclude the first rows like 'Num Animals', 'High', 'Average', etc.

    # Convert the EPD column to numeric (handling any non-numeric values gracefully)
    percentiles[epd_column] = pd.to_numeric(percentiles[epd_column], errors='coerce')

    # If the value is higher than the highest recorded, return the 1% rank
    if epd_column == 'BW':
        if value  >= percentiles[epd_column].max():
            st.write(f"Looking at BW , the max is {percentiles[epd_column].max()}")
            return '95%'
        # If the value is lower than the lowest recorded, return the 95% rank
        elif value < percentiles[epd_column].min():
            return '1%'
        
        for index, row in percentiles.iterrows():
            if value <= row[epd_column]:
                return row['Categories']
    else: 
        if value >= percentiles[epd_column].max():
            return '1%'
        # If the value is lower than the lowest recorded, return the 95% rank
        elif value <= percentiles[epd_column].min():
            return '95%'
        
        for index, row in percentiles.iterrows():
            if value >= row[epd_column]:
                return row['Categories']  # Return the percentile rank (like 1%, 2%, etc.)

    return "Percentile rank not found."


