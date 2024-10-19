import streamlit as st
import requests
import json
from datetime import datetime

# Function to handle the search request
def do_search_epd():
    # Prepare the parameters for the request
    params = {
        "user_id": st.session_state.get('uname', ''),
        "t": datetime.now().microsecond
    }

    # Add optional parameters if they are filled out
    optional_params = [
        ("minced", "Min CED"),
        ("maxced", "Max CED"),
        ("mincedacc", "Min CED Accuracy"),
        ("minbwt", "Min BWT"),
        ("maxbwt", "Max BWT"),
        ("minbwtacc", "Min BWT Accuracy"),
        ("minwwt", "Min WWT"),
        ("maxwwt", "Max WWT"),
        ("minwwtacc", "Min WWT Accuracy"),
        ("minywt", "Min YWT"),
        ("maxywt", "Max YWT"),
        ("minywtacc", "Min YWT Accuracy"),
        ("minmilk", "Min Milk"),
        ("maxmilk", "Max Milk"),
        ("minmilkacc", "Min Milk Accuracy"),
        ("mintm", "Min TM"),
        ("maxtm", "Max TM"),
        ("mingrowth", "Min Growth"),
        ("maxgrowth", "Max Growth")
    ]

    for param, label in optional_params:
        value = st.session_state.get(param, "")
        if value:
            params[param] = value

    # Handle radio buttons and select boxes
    rows = st.session_state.get("e_search_rows_page", "")
    if rows:
        params["rows"] = rows

    sort_field = st.session_state.get("e_search_sort_fld", "")
    if sort_field:
        params["sort_field"] = sort_field

    animal_sex = st.session_state.get("e_search_sex", "")
    if animal_sex:
        params["animal_sex"] = animal_sex

    parent = st.session_state.get("e_search_parent", "")
    if parent:
        params["parent"] = parent

    classification = st.session_state.get("e_search_classification", "")
    if classification:
        params["classification"] = classification

    scur_score = st.session_state.get("e_search_scur_score", "")
    if scur_score:
        params["scur_score"] = scur_score

    # Handle date range and percentage base
    if st.session_state.get("e_born_between", False):
        birth_date1 = st.session_state.get("e_birth_date1", "")
        birth_date2 = st.session_state.get("e_birth_date2", "")
        if birth_date1 and birth_date2:
            params["birth_date1"] = birth_date1
            params["birth_date2"] = birth_date2

    if st.session_state.get("e_minimum_percentage", False):
        percentage_base = st.session_state.get("e_percentage_base", "")
        if percentage_base:
            params["percentage_base"] = percentage_base

    # Replace commas with dots in the parameters
    params = {k: str(v).replace(",", ".") for k, v in params.items()}

    # Make the request
    response = requests.get("https://https://akaushi.digitalbeef.com/modules/DigitalBeef-Landing/ajax/search_results_epd.php", params=params)

    # Display the results
    if response.status_code == 200:
        st.write("Search Results:")
        st.write(response.text)
    else:
        st.error("Failed to retrieve data. Please try again.")

# Streamlit app layout
st.title("EPD Search Form")

# Input fields
st.subheader("Optional Parameters")
for param, label in [
    ("minced", "Min CED"),
    ("maxced", "Max CED"),
    ("mincedacc", "Min CED Accuracy"),
    ("minbwt", "Min BWT"),
    ("maxbwt", "Max BWT"),
    ("minbwtacc", "Min BWT Accuracy"),
    ("minwwt", "Min WWT"),
    ("maxwwt", "Max WWT"),
    ("minwwtacc", "Min WWT Accuracy"),
    ("minywt", "Min YWT"),
    ("maxywt", "Max YWT"),
    ("minywtacc", "Min YWT Accuracy"),
    ("minmilk", "Min Milk"),
    ("maxmilk", "Max Milk"),
    ("minmilkacc", "Min Milk Accuracy"),
    ("mintm", "Min TM"),
    ("maxtm", "Max TM"),
    ("mingrowth", "Min Growth"),
    ("maxgrowth", "Max Growth")
]:
    st.text_input(label, key=param)

# Radio buttons and select boxes
st.subheader("Radio Buttons and Select Boxes")
rows_options = ["10", "20", "50", "100"]
st.radio("Rows per page", rows_options, key="e_search_rows_page")

sort_field_options = ["field1", "field2", "field3"]  # Replace with actual field names
st.radio("Sort Field", sort_field_options, key="e_search_sort_fld")

animal_sex_options = ["male", "female", "unknown"]  # Replace with actual options
st.selectbox("Animal Sex", animal_sex_options, key="e_search_sex")

parent_options = ["parent1", "parent2", "parent3"]  # Replace with actual options
st.selectbox("Parent", parent_options, key="e_search_parent")

classification_options = ["class1", "class2", "class3"]  # Replace with actual options
st.selectbox("Classification", classification_options, key="e_search_classification")

scur_score_options = ["score1", "score2", "score3"]  # Replace with actual options
st.selectbox("SCUR Score", scur_score_options, key="e_search_scur_score")

# Date range and percentage base
st.subheader("Date Range and Percentage Base")
st.checkbox("Born Between", key="e_born_between")
if st.session_state.get("e_born_between", False):
    st.date_input("Birth Date 1", key="e_birth_date1")
    st.date_input("Birth Date 2", key="e_birth_date2")

st.checkbox("Minimum Percentage", key="e_minimum_percentage")
if st.session_state.get("e_minimum_percentage", False):
    st.text_input("Percentage Base", key="e_percentage_base")

# Submit button
st.button("Search", on_click=do_search_epd)