import streamlit as st
import pandas as pd
import numpy as np
from functools import partial

def show():
    st.title("Individual Cattle Analysis")
    st.write("Analyze EPDs of individual cattle.")
    
    if st.session_state.filteredDf is not None:
        comparison_columns = {
            "CED": "CED",
            "BW": "BW",
            "WW": "WW",
            "YW": "YW",
            "MK": "MK",
            "TM": "TM",
            "Growth": "Growth"
        }

        def compare_epds_to_industry(filtered_df, industry_df):
            for epd, industry_epd in comparison_columns.items():
                industry_value = float(industry_df.loc[industry_df['Categories'] == 'Average', industry_epd].values[0])
                filtered_df[f'{epd}_industry_avg'] = round(industry_value, 2)
            return filtered_df

        def style_dataframe(data, columns_to_display):
            def highlight_cells(val, col):
                try:
                    cow_value = float(val)
                    industry_value = data[f'{col}_industry_avg'].iloc[0]
                    if pd.notnull(cow_value) and pd.notnull(industry_value):
                        color = 'green' if cow_value > industry_value else 'red'
                        return f'font-weight: bold; color: {color}'
                except (ValueError, TypeError):
                    pass
                return ''
            
            styled = data[columns_to_display].style
            for col in comparison_columns:
                if col in columns_to_display:
                    highlight_func = partial(highlight_cells, col=col)
                    styled = styled.applymap(highlight_func, subset=[col]).format(precision=2)

            return styled
        selection2 = st.selectbox("Select Cattle Type", ["Active Sires", "Active Dams", "Non-Parents"], key="cattle_type_selection")

        if selection2 == "Active Dams":
            industry_metrics_df = st.session_state.activeDamsPercentileRankDf
            comparisonDF = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'C') & (st.session_state.filteredDf['Age'] >= 2)]
        elif selection2 == "Active Sires":
            industry_metrics_df = st.session_state.activeSiresPercentileRankDf
            comparisonDF = st.session_state.filteredDf[(st.session_state.filteredDf['Type or Sex'] == 'B') & (st.session_state.filteredDf['Age'] >= 2)]
        else:
            industry_metrics_df = st.session_state.nonParentsPercentileRankDf
            comparisonDF = st.session_state.filteredDf[(st.session_state.filteredDf['Age'] < 2)]

        highlighted_df = compare_epds_to_industry(comparisonDF, industry_metrics_df)
        

        selected_value = st.slider(
            "Select Number of Cattle to Display",
            min_value=1,
            max_value=highlighted_df.shape[0],
            value=5  # Default value
        )

        display_columns = ['Name', 'Registration Number', 'Age', 'Composite Score', 'CED', 'BW', 'WW', 'YW', 'MK', 'TM', 'Growth']

        top_performers_df = highlighted_df.nlargest(selected_value, 'Composite Score')
        bottom_performers_df = highlighted_df.nsmallest(selected_value, 'Composite Score')

        st.subheader("Top Performing Cattle")
        st.dataframe(style_dataframe(top_performers_df, display_columns))

        st.subheader("Bottom Performing Cattle")
        st.dataframe(style_dataframe(bottom_performers_df, display_columns))