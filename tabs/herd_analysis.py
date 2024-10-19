import streamlit as st
from lib.helper_functions import *

def show():
    topCol1, topCol2, topCol3 = st.columns(3, gap="large")
    with topCol1:
        st.title("Herd Pipeline Analysis")
    with topCol3:
        cowCatagory = st.radio(
                "Cattle Type for Analysis",
                ["Active_Sires", "Active_Dams", "Non_Parents"],
            )
        if cowCatagory == "Active_Sires":
            st.write("You selected Sires.")
            scenarioDf = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'B') & (st.session_state.filteredDf['Age'] >= 2)]
        elif cowCatagory == "Active_Dams":
            st.write("You selected Dams.")
            scenarioDf = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'C') & (st.session_state.filteredDf['Age'] >= 2)]
        elif cowCatagory == "Non_Parents":
            st.write("You selected Non-Parents.")
            scenarioDf = st.session_state.filteredDf[st.session_state.filteredDf['Age'] < 2]
        else:
            st.write("You didn't select type.")
            
            
            
    if st.session_state.filteredDf is not None:
        df = st.session_state.filteredDf
        with topCol1:
            st.write("Perform analysis of the herd EPDs and compare to industry benchmarks.")
        
    def compare_sires_epds_with_industry(yourHerdDf, industryDf, catagory):
        if catagory == "Dams":
            yourHerdDf = yourHerdDf[(yourHerdDf['Type or Sex'] == 'C') & (yourHerdDf['Age'] >= 2)]
        elif catagory == "Sires":
            yourHerdDf = yourHerdDf[(yourHerdDf['Type or Sex'] == 'B') & (yourHerdDf['Age'] >= 2)]
        elif catagory == "Non-Parents":
            yourHerdDf = yourHerdDf[yourHerdDf['Age'] < 2]
        else:
            raise ValueError("Invalid catagory. Must be 'Dams', 'Sires', or 'Non-Parents'.")
        column_mapping = {
            'CED': 'CED',
            'BW': 'BW',
            'WW': 'WW',
            'YW': 'YW',
            'MK': 'MK',             # MK in activeSiresPercentileDf is Milk in filtered_df
            'TM': 'TM',    # TM in activeSiresPercentileDf is Total Maternal in filtered_df
            'Growth': 'Growth'     # Growth in activeSiresPercentileDf is Growth Idx in filtered_df
        }

        # Filter the columns based on the mapping
        filtered_sires_avg_epds = yourHerdDf[list(column_mapping.values())].mean().round(2)
        industry_avg_epds_adjusted = industryDf[industryDf['Categories'] == 'Average'][list(column_mapping.keys())].iloc[0]
        # Ensure 'Growth' is properly added to the comparison
        filtered_sires_avg_epds_with_growth = filtered_sires_avg_epds.copy()
        filtered_sires_avg_epds_with_growth['Growth'] = round(yourHerdDf['Growth'].mean(),2)
        # Recreate the comparison dataframe including 'Growth'
        comparison_df = pd.DataFrame({
            'Herd Avgs': filtered_sires_avg_epds_with_growth,
            'Industry Avg': industry_avg_epds_adjusted
        }).reindex(index=['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth'])
        comparison_df["Herd Avgs"].map(lambda x: round(x, 2))

        # Apply the formatting cell-wise
        def highlight_cells(data):
            styled_data = pd.DataFrame('', index=data.index, columns=data.columns)
            for row in data.index:
                if pd.to_numeric(data.at[row, 'Herd Avgs']) > pd.to_numeric(data.at[row, 'Industry Avg']):
                    styled_data.at[row, 'Herd Avgs'] = 'font-weight: bold; color: green'
                else:
                    styled_data.at[row, 'Herd Avgs'] = 'font-weight: bold; color: red'
            return styled_data

        styled_comparison_df = comparison_df.style.apply(highlight_cells, axis=None).format(precision=2)
        
        return styled_comparison_df

    #FIX adding test section here: 
    
    st.markdown("---")
    col1, col2, col3 = st.columns([0.2, 0.2, 0.6], gap="large")
    # List of EPD columns to create sliders for
    epd_columns = ['CED', 'BW', 'WW', 'YW', 'TM', 'MK', "Composite Score"]
    # Create a dictionary to store the selected registration numbers
    selected_registration_numbers = {}
    # Loop through each EPD column to create a slider
    with col1:
        for epd in epd_columns:
            # Slider to select the number of rows with the lowest values for the current EPD
            slider_value = st.slider(f"Select number of lowest {epd} values", 0, scenarioDf.shape[0], 0)
            
            # If the slider value is greater than 0, select the rows with the lowest values for the EPD
            if slider_value > 0:
                lowest_values_df = scenarioDf.nsmallest(slider_value, epd)
                selected_registration_numbers[epd] = lowest_values_df['Registration Number'].tolist()

    # Display the selected registration numbers for each EPD
    cullList = []
    for epd, reg_numbers in selected_registration_numbers.items():

        st.write(f"Registration Numbers for the lowest {epd} values:", reg_numbers)
        for reg_number in reg_numbers:
            cullList.append(reg_number)
    with col1: 
        st.write(f"Cull List: {cullList}")
    #DEBUG Now remove all cullList cows from the scenarioDF
    # st.session_state.filteredDf = st.session_state.filteredDf[~st.session_state.filteredDf['Registration Number'].isin(cullList)]
    scenarioDf = st.session_state.filteredDf[~st.session_state.filteredDf['Registration Number'].isin(cullList)]
   
    #Sires
    sires_styled_comparison_df = compare_sires_epds_with_industry(scenarioDf, st.session_state.activeSiresPercentileRankDf, "Sires")
    #Dams
    dams_styled_comparison_df = compare_sires_epds_with_industry(scenarioDf, st.session_state.activeDamsPercentileRankDf, "Dams")
    #Non-Parents
    non_parents_styled_comparison_df = compare_sires_epds_with_industry(scenarioDf, st.session_state.nonParentsPercentileRankDf, "Non-Parents")
    
    
    
    # Display the styled dataframe
    
    with col3:
        activeSiresDf = scenarioDf[(scenarioDf['Type or Sex'] == 'B') & (df['Age'] >= 2)]
        st.write(f"Sires (Total : {activeSiresDf.shape[0]})")
        st.dataframe(sires_styled_comparison_df)
        activeDamsDf = scenarioDf[(scenarioDf['Type or Sex'] == 'C') & (df['Age'] >= 2)]
        st.write(f"Dams (Total : {activeDamsDf.shape[0]})")
        st.dataframe(dams_styled_comparison_df)
        nonParentDf = scenarioDf[scenarioDf['Age'] < 2]
        st.write(f"Non-Parents (Total : {nonParentDf.shape[0]})")
        st.dataframe(non_parents_styled_comparison_df)
    

     