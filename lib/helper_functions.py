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
            
            # Save the dataframes
            activeSiresPercentileRankDf.to_pickle('datafiles/activeSiresPercentileRankDf.pkl')
            activeDamsPercentileRankDf.to_pickle('datafiles/activeDamsPercentileRankDf.pkl') 
            nonParentsPercentileRankDf.to_pickle('datafiles/nonParentsPercentileRankDf.pkl')

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

def mergeEpdAndCattlemaxDfs(epdDf, cattlemaxDf):
    # Prepare to merge by adding the "CM_" prefix to all cattlemax columns
    cattlemaxDf = cattlemaxDf.add_prefix("CM_")
    # Rename the "CM_Registration Number" to match "Reg No" in the epdDf for merging
    cattlemaxDf = cattlemaxDf.rename(columns={"CM_Registration Number": "Reg No"})
    # Merge the dataframes on "Reg No", ensuring epdDf is not overwritten
    mergedDf = pd.merge(epdDf, cattlemaxDf, on="Reg No", how="left")
    if 'CM_Date of Birth' in mergedDf.columns:
        mergedDf['CM_Date of Birth'] = pd.to_datetime(mergedDf['CM_Date of Birth'], errors='coerce')

    return(mergedDf)