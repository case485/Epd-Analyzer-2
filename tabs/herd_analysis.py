import streamlit as st
from lib.helper_functions import *

def show():
    st.title("Herd Analysis")
    if st.session_state.filteredDf is not None:
        df = st.session_state.filteredDf
        st.write("Perform analysis of the herd EPDs and compare to industry benchmarks.")
         # Load the EPD data and perform analysis (you can expand this later)
         # Since 'CM_Date of Birth' is in datetime format, we need to calculate age by subtracting the date from the current year
        df['CM_Age'] = (pd.to_datetime('today').year) - df['CM_Date of Birth'].dt.year

        # Apply the filters based on the given criteria
        damsDf = df[(df['CM_Type or Sex'] == 'C') & (df['CM_Age'] >= 2)]
        sireDf = df[(df['CM_Type or Sex'] == 'B') & (df['CM_Age'] >= 2)]
        nonParentDf = df[df['CM_Age'] < 2]
        
        st.write(f"Number of Cows in Analysis: {damsDf.shape[0]}")
        st.write(f"Number of Bulls in Analysis: {sireDf.shape[0]}")
        st.write(f"Number of Non-Parents in Analysis: {nonParentDf.shape[0]}")
        
        
        # Adjust the function to correctly compare numeric values and apply the styling
    def compare_sires_epds_with_industry(filtered_sires_df, active_sires_percentile_rank_df):
        # Adjust the column mapping based on Chad's instructions
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
        filtered_sires_avg_epds = filtered_sires_df[list(column_mapping.values())].mean()
        industry_avg_epds_adjusted = active_sires_percentile_rank_df[active_sires_percentile_rank_df['Categories'] == 'Average'][list(column_mapping.keys())].iloc[0]

        # Rename the columns in the filtered_sires_avg_epds to match the activeSiresPercentileRankDf
        filtered_sires_avg_epds = filtered_sires_avg_epds.rename({
            'Milk': 'MK',
            'Total Maternal': 'TM',
            'Growth Idx': 'Growth'
        })

        # Ensure 'Growth' is properly added to the comparison
        filtered_sires_avg_epds_with_growth = filtered_sires_avg_epds.copy()
        filtered_sires_avg_epds_with_growth['Growth'] = filtered_sires_df['Growth Idx'].mean()

        # Recreate the comparison dataframe including 'Growth'
        comparison_df = pd.DataFrame({
            'Filtered Sires Avg': filtered_sires_avg_epds_with_growth,
            'Industry Avg': industry_avg_epds_adjusted
        }).reindex(index=['CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth'])

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
                if pd.to_numeric(data.at[row, 'Filtered Sires Avg']) > pd.to_numeric(data.at[row, 'Industry Avg']):
                    styled_data.at[row, 'Filtered Sires Avg'] = 'font-weight: bold; color: green'
                else:
                    styled_data.at[row, 'Filtered Sires Avg'] = 'font-weight: bold; color: red'
            return styled_data

        # Apply the styling
        styled_comparison_df = comparison_df.style.apply(highlight_cells, axis=None)

        # Return the styled comparison dataframe
        return styled_comparison_df

    # Test the function with styling
    styled_comparison_df = compare_sires_epds_with_industry(st.session_state.filteredDf, st.session_state.activeSiresPercentileRankDf)

    # Display the styled dataframe
    st.dataframe(styled_comparison_df)

        
        #        