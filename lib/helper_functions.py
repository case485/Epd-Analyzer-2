from bs4 import BeautifulSoup
import streamlit as st
import re
import pandas as pd
import requests
import camelot
from config import *

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
                # st.write(f"Found the URL: {a677777777777777777aPercentileRankUrl}")
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
    pdf_path = INDUSTRY_PERCENTILE_FILE
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
    log_error(f"tables: {tables}")
    
    if len(tables) > 2:
        try:
            activeSiresPercentileRankDf = tables[0].df  # Convert the first table to a DataFrame
            activeDamsPercentileRankDf = tables[1].df  # Convert the second table to a DataFrame
            nonParentsPercentileRankDf = tables[2].df  # Convert the third table to a DataFrame
            
            

            # Active Dams
            df = activeDamsPercentileRankDf
            header_index = df[df.isin(['CED']).any(axis=1)].index[0]  # Find where 'CED' is located
            df = df.iloc[header_index:].reset_index(drop=True)
            df.columns = df.iloc[0]  # Set new headers
            df = df[1:].reset_index(drop=True)
            df = df.rename(columns={df.columns[0]: 'Categories'})
            activeDamsPercentileRankDf = df

            # Active Sires
            df = activeSiresPercentileRankDf
            header_index = df[df.isin(['CED']).any(axis=1)].index[0]  # Find where 'CED' is located
            df = df.iloc[header_index:].reset_index(drop=True)
            df.columns = df.iloc[0]  # Set new headers
            df = df[1:].reset_index(drop=True)
            df = df.rename(columns={df.columns[0]: 'Categories'})
            activeSiresPercentileRankDf = df
            # Non-Parents
            df = nonParentsPercentileRankDf
            header_index = df[df.isin(['CED']).any(axis=1)].index[0]  # Find where 'CED' is located
            df = df.iloc[header_index:].reset_index(drop=True)
            df.columns = df.iloc[0]  # Set new headers
            df = df[1:].reset_index(drop=True)
            df = df.rename(columns={df.columns[0]: 'Categories'})
            nonParentsPercentileRankDf = df
            
            # Save the dataframes
            activeSiresPercentileRankDf.to_pickle('datafiles/activeSiresPercentileRankDf.pkl')
            activeDamsPercentileRankDf.to_pickle('datafiles/activeDamsPercentileRankDf.pkl') 
            nonParentsPercentileRankDf.to_pickle('datafiles/nonParentsPercentileRankDf.pkl')
           
            
        except IndexError:
            # Handle the case where 'CED' is not found in the DataFrame
            st.error(f"Warning: 'CED' not found in one of the DataFrames.")
        except KeyError as e:
            st.error(f"KeyError: {e} - Ensure the column 'Categories' exists.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        
    else:
        st.error(f"Less than 3 tables found in the PDF. Found {len(tables)} tables.")
    
    return (activeSiresPercentileRankDf, activeDamsPercentileRankDf, nonParentsPercentileRankDf)

def epd_composite_score_app(df):
            # Load your dataframe
            # Define a function to calculate composite score
            def calculate_composite_score(row, weights):
                composite_score = (
                    row['CED'] * weights['CED'] +
                    row['BW'] * weights['BW'] +
                    row['WW'] * weights['WW'] +
                    row['YW'] * weights['YW'] +
                    row['MK'] * weights['MK'] +
                    row['TM'] * weights['TM'] +
                    row['Growth'] * weights['Growth']
                )
                return composite_score

            # Sidebar sliders to adjust weights
            st.sidebar.header("Adjust Weights for EPD Traits")

            weights = {
                'CED': st.sidebar.slider('CED Weight', 0.0, 0.5, 1.0),
                'BW': st.sidebar.slider('BW Weight', 0.0, 0.5, 1.0),
                'WW': st.sidebar.slider('WW Weight', 0.0, 0.5, 1.0),
                'YW': st.sidebar.slider('YW Weight', 0.0, 0.5, 1.0),
                'MK': st.sidebar.slider('Milk Weight', 0.0, 0.5, 1.0),
                'TM': st.sidebar.slider('Total Maternal Weight', 0.0, 0.5, 1.0),
                'Growth': st.sidebar.slider('Growth Idx Weight', 0.0, 0.5, 1.0),
            }

            df['Composite Score'] = df.apply(calculate_composite_score, axis=1, weights=weights)
            return(df)

def clean_and_modify_CattlemaxDfs(df):
    
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
    
    return(df)