import streamlit as st
from lib.helper_functions import *

def show():
    st.title("Herd Analysis")
    if st.session_state.filteredDf is not None:
        df = st.session_state.filteredDf
        st.write("Perform analysis of the herd EPDs and compare to industry benchmarks.")
        df['CM_Age'] = (pd.to_datetime('today').year) - df['CM_Date of Birth'].dt.year
        damsDf = df[(df['CM_Type or Sex'] == 'C') & (df['CM_Age'] >= 2)]
        siresDf = df[(df['CM_Type or Sex'] == 'B') & (df['CM_Age'] >= 2)]
        nonParentDf = df[df['CM_Age'] < 2]
    def compare_sires_epds_with_industry(yourHerdDf, industryDf, catagory):
        if catagory == "Dams":
            yourHerdDf = yourHerdDf[(yourHerdDf['CM_Type or Sex'] == 'C') & (yourHerdDf['CM_Age'] >= 2)]
        elif catagory == "Sires":
            yourHerdDf = yourHerdDf[(yourHerdDf['CM_Type or Sex'] == 'B') & (yourHerdDf['CM_Age'] >= 2)]
        elif catagory == "Non-Parents":
            yourHerdDf = yourHerdDf[yourHerdDf['CM_Age'] < 2]
        else:
            raise ValueError("Invalid catagory. Must be 'Dams', 'Sires', or 'Non-Parents'.")
        column_mapping = {
            'CED': 'CED',
            'BW': 'BW',
            'WW': 'WW',
            'YW': 'YW',
            'MK': 'Milk',             # MK in activeSiresPercentileDf is Milk in filtered_df
            'TM': 'Total Maternal',    # TM in activeSiresPercentileDf is Total Maternal in filtered_df
            'Growth': 'Growth Idx'     # Growth in activeSiresPercentileDf is Growth Idx in filtered_df
        }

        # Filter the columns based on the mapping
        filtered_sires_avg_epds = yourHerdDf[list(column_mapping.values())].mean().round(2)
        industry_avg_epds_adjusted = industryDf[industryDf['Categories'] == 'Average'][list(column_mapping.keys())].iloc[0]
        # filtered_sires_avg_epds["Herd Avgs"] = filtered_sires_avg_epds["Herd Avgs"].round(2)
        
        # Rename the columns in the filtered_sires_avg_epds to match the activeSiresPercentileRankDf
        filtered_sires_avg_epds = filtered_sires_avg_epds.rename({
            'Milk': 'MK',
            'Total Maternal': 'TM',
            'Growth Idx': 'Growth'
        })

        # Ensure 'Growth' is properly added to the comparison
        filtered_sires_avg_epds_with_growth = filtered_sires_avg_epds.copy()
        filtered_sires_avg_epds_with_growth['Growth'] = round(yourHerdDf['Growth Idx'].mean(),2)
        # Recreate the comparison dataframe including 'Growth'
        comparison_df = pd.DataFrame({
            'Herd Avgs': filtered_sires_avg_epds_with_growth,
            'Industry Avg': industry_avg_epds_adjusted
        }).reindex(index=['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth'])

        comparison_df["Herd Avgs"].map(lambda x: round(x, 2))
        
        
        # Apply conditional formatting: bold green for better performance, bold red for worse
        def highlight_comparison(val, industry_val):
            if val > industry_val:
                return 'font-weight: bold; color: green'
            else:
                return 'font-weight: bold; color: red'

        # Apply the formatting cell-wise
        def highlight_cells(data):
            styled_data = pd.DataFrame('', index=data.index, columns=data.columns)
            for row in data.index:
                if pd.to_numeric(data.at[row, 'Herd Avgs']) > pd.to_numeric(data.at[row, 'Industry Avg']):
                    styled_data.at[row, 'Herd Avgs'] = 'font-weight: bold; color: green'
                else:
                    styled_data.at[row, 'Herd Avgs'] = 'font-weight: bold; color: red'
            return styled_data

        # Apply the styling
        styled_comparison_df = comparison_df.style.apply(highlight_cells, axis=None)
        

        # Return the styled comparison dataframe
        return styled_comparison_df

    # Test the function with styling
    #Sires
    sires_styled_comparison_df = compare_sires_epds_with_industry(st.session_state.filteredDf, st.session_state.activeSiresPercentileRankDf, "Sires")
    #Dams
    dams_styled_comparison_df = compare_sires_epds_with_industry(st.session_state.filteredDf, st.session_state.activeDamsPercentileRankDf, "Dams")
    #Non-Parents
    non_parents_styled_comparison_df = compare_sires_epds_with_industry(st.session_state.filteredDf, st.session_state.nonParentsPercentileRankDf, "Non-Parents")

    # Display the styled dataframe
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Sires (Total : {siresDf.shape[0]})")
        st.dataframe(sires_styled_comparison_df)
    with col2:
        st.write(f"Dams (Total : {damsDf.shape[0]})")
        st.dataframe(dams_styled_comparison_df)
    with col3:
        st.write(f"Non-Parents (Total : {nonParentDf.shape[0]})")
        st.dataframe(non_parents_styled_comparison_df)
    

        
        #        