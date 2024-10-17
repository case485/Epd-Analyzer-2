import streamlit as st
import pandas as pd

def show():
    st.title("Individual Cattle Analysis")
    st.write("Analyze EPDs of individual cattle.")
    # Add logic to display individual cattle analysis
    if st.session_state.filteredDf is not None:


        def compare_epds_to_industry(filtered_df, industry_df):
            comparison_columns = {
                "CED": "CED",
                "BW": "BW",
                "WW": "WW",
                "YW": "YW",
                "Milk": "MK",
                "Total Maternal": "TM",
                "Growth Idx": "Growth"
            }

            for cow_idx, cow in filtered_df.iterrows():
                for epd, industry_epd in comparison_columns.items():
                    try:
                        cow_value = float(cow[epd]) if pd.notnull(cow[epd]) else None
                        industry_value = float(industry_df.loc[industry_df['Categories'] == 'Average', industry_epd].values[0])

                        if cow_value is not None:
                            if cow_value > industry_value:
                                filtered_df.at[cow_idx, epd] = f"<span style='color:green'>{cow_value}</span>"
                            else:
                                filtered_df.at[cow_idx, epd] = f"<span style='color:red'>{cow_value}</span>"
                    except (ValueError, TypeError):
                        # Skip if conversion to float fails or comparison is not possible
                        continue

            return filtered_df

        # Get user selection (simulated here as Streamlit options)
        selection2 = st.selectbox("Select Cattle Type", ["Active Sires", "Active Dams", "Non-Parents"] ,key="cattle_type_selection")

        # Load corresponding industry dataframe
        if selection2 == "Active Dams":
            industry_metrics_df = st.session_state.activeDamsPercentileRankDf
            #FIX ME : need to add the filtered cattle df here as well
        elif selection2 == "Active Sires":
            industry_metrics_df = st.session_state.activeSiresPercentileRankDf
        else:
            industry_metrics_df = st.session_state.nonParentsPercentileRankDf

        # Apply EPD comparison
        highlighted_df = compare_epds_to_industry(st.session_state.filteredDf, industry_metrics_df)

        # Sort for top and bottom performing cattle based on composite score
        top_performers_df = highlighted_df.nlargest(5, 'Composite Score')
        bottom_performers_df = highlighted_df.nsmallest(5, 'Composite Score')
        st.dataframe(top_performers_df)
        st.dataframe(bottom_performers_df)
