import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.stats import chi2_contingency
import numpy as np
import io
from fpdf import FPDF
from datetime import datetime

# Set page config with wide layout and a custom title
st.set_page_config(
    page_title="Sire Quality Analysis",
    page_icon="🐮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Update the CSS with larger dataframe fonts
st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:18px !important;
    }
    .stMetric {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 10px;
        border-radius: 5px;
    }
    /* Increase font size in Streamlit dataframe */
    [data-testid="stDataFrame"] {
        font-size: 1.5rem !important;  /* Increased from 1.2rem to 1.5rem */
    }
    /* Make column headers larger */
    [data-testid="stDataFrame"] div[data-testid="stDataFrameColumn"] {
        font-size: 1.6rem !important;  /* Increased from 1.3rem to 1.6rem */
        font-weight: bold;
    }
    /* Add padding to cells for better readability */
    [data-testid="stDataFrame"] td {
        padding: 12px !important;  /* Added more padding */
    }
    /* Style for sire metrics */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    /* Style for metric labels (sire names) */
    [data-testid="metric-container"] label {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #1f2937 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Title with custom styling
st.markdown("<h1 style='text-align: center;'>🐮 Cattle Carcass Quality Analysis 🥩</h1>", unsafe_allow_html=True)

# Read and process data
df = pd.read_csv('datafiles/artesianCaracassDf.csv')
df['Quality'] = df['Quality'].replace(['CH', 'CHG'], 'Choice')
df['Quality'] = df['Quality'].replace('P', 'Prime')

# Create sidebar for filters and settings
with st.sidebar:
    st.header("Analysis Settings")
    min_offspring = st.slider("Minimum Offspring per Sire", 
                            min_value=3, 
                            max_value=20, 
                            value=5,
                            help="Filter sires based on minimum number of offspring")
    
    st.markdown("---")
    st.markdown("### About This Dashboard")
    st.markdown("""
    This dashboard analyzes the relationship between sires and 
    carcass quality grades in cattle. It helps identify top-performing 
    sires and quality distribution patterns.
    """)

# Calculate basic statistics for overview
total_cattle = len(df)
total_sires = df['Sire'].nunique()
prime_percent = (df['Quality'] == 'Prime').mean() * 100
choice_percent = (df['Quality'] == 'Choice').mean() * 100

# Overview metrics in a nice grid
st.markdown("### 📊 Overview Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Cattle",
        f"{total_cattle:,}",
        delta=f"{total_sires} Sires"
    )
with col2:
    st.metric(
        "Prime Grade",
        f"{prime_percent:.1f}%",
        delta="of total cattle"
    )
with col3:
    st.metric(
        "Choice Grade",
        f"{choice_percent:.1f}%",
        delta="of total cattle"
    )
with col4:
    avg_weight = df['Carcass_Weight'].mean()
    st.metric(
        "Avg Carcass Weight",
        f"{avg_weight:.0f} lbs",
        delta=f"±{df['Carcass_Weight'].std():.0f} lbs"
    )

# Statistical Analysis Section
st.markdown("---")
st.markdown("### 📈 Statistical Analysis")

# Calculate sire performance statistics
sire_quality = pd.crosstab(df['Sire'], df['Quality'])
sire_percentages = sire_quality.div(sire_quality.sum(axis=1), axis=0) * 100

# Filter for sires with minimum offspring
significant_sires = sire_quality[sire_quality.sum(axis=1) >= min_offspring].index
filtered_percentages = sire_percentages.loc[significant_sires]

# Perform chi-square test
contingency_table = sire_quality.loc[significant_sires]
chi2, p_value, dof, expected = chi2_contingency(contingency_table)
confidence_level = ((1 - p_value) * 100).round(1)

# Display statistical results in columns
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### Statistical Measures")
    st.metric("Chi-square Value", f"{chi2:.2f}")
    st.metric("Confidence Level", f"{confidence_level}%")
    st.metric("P-value", f"{p_value:.6f}")

with col2:
    st.markdown("#### Interpretation")
    st.info(f"""
    📊 The analysis shows with {confidence_level}% confidence that there is a 
    significant relationship between sires and quality grades. This means the 
    choice of sire has a measurable impact on carcass quality outcomes.
    """)

# Quality Distribution Table
st.markdown("---")
st.markdown("### 📋 Sire Quality Distribution")

# Create and style the table
quality_table = filtered_percentages.round(1)
quality_table['Total_Head'] = sire_quality.sum(axis=1)[significant_sires]
quality_table = quality_table.sort_values('Prime', ascending=False)
quality_table = quality_table.reindex(columns=['Prime', 'SE', 'Choice', 'No Roll', 'Total_Head'])

def style_prime(val):
    color = 'green' if val >= 50 else 'black'
    return f'color: {color}'

def style_choice(val):
    color = 'red' if val >= 50 else 'black'
    return f'color: {color}'

# Create tabs for different views
tab1, tab2 = st.tabs(["📊 Distribution Table", "📈 Visualization"])

with tab1:
    st.markdown("#### Quality Grade Distribution by Sire")
    st.markdown("*Green: Prime ≥ 50% | Red: Choice ≥ 50%*")
    st.dataframe(
        quality_table.style
        .format({
            'Prime': '{:.1f}%',
            'SE': '{:.1f}%',
            'Choice': '{:.1f}%',
            'No Roll': '{:.1f}%',
            'Total_Head': '{:,.0f}'
        })
        .applymap(style_prime, subset=['Prime'])
        .applymap(style_choice, subset=['Choice'])
    )



with tab2:
    plot_data = quality_table.reset_index()
    plot_data = plot_data.melt(
        id_vars=['Sire', 'Total_Head'],
        value_vars=['Prime', 'SE', 'Choice', 'No Roll'],
        var_name='Quality',
        value_name='Percentage'
    )

    fig = px.bar(
        plot_data,
        x='Sire',
        y='Percentage',
        color='Quality',
        title='Quality Grade Distribution by Sire',
        labels={'Percentage': 'Percentage of Offspring', 'Sire': 'Sire ID'},
        barmode='group',
        color_discrete_map={
            'Prime': '#2ecc71',    # Green
            'Choice': '#e74c3c',   # Red
            'SE': '#f1c40f',       # Yellow
            'No Roll': '#95a5a6'   # Gray
        }
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=True,
        plot_bgcolor='white',
        font=dict(
            size=20,  # Increased base font size
            family="Arial"
        ),
        title=dict(
            text='<b>Quality Grade Distribution by Sire</b>',
            font=dict(size=28)  # Larger title
        ),
        xaxis=dict(
            tickfont=dict(
                size=24,  # Even larger sire names
                family="Arial Black"  # Bold font for sire names
            ),
            title=dict(
                text='<b>Sire ID</b>',
                font=dict(size=24)  # Larger axis title
            )
        ),
        yaxis=dict(
            tickfont=dict(size=20),
            title=dict(
                text='<b>Percentage of Offspring</b>',
                font=dict(size=24)  # Larger axis title
            )
        ),
        legend=dict(
            font=dict(size=20)  # Larger legend text
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# Top Performers Section
st.markdown("---")
st.markdown("### 🏆 Top Performers Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Top 5 Prime Grade Sires")
    top_prime = quality_table.nlargest(5, 'Prime')
    for idx, row in top_prime.iterrows():
        st.metric(
            f"Sire: {idx}",  # Added "Sire:" prefix
            f"{row['Prime']:.1f}% Prime",
            f"{row['Total_Head']:.0f} head",
            help=f"Total offspring: {row['Total_Head']:.0f}"
        )

with col2:
    st.markdown("#### Top 5 Choice Grade Sires")
    top_choice = quality_table.nlargest(5, 'Choice')
    for idx, row in top_choice.iterrows():
        st.metric(
            f"Sire: {idx}",  # Added "Sire:" prefix
            f"{row['Choice']:.1f}% Choice",
            f"{row['Total_Head']:.0f} head",
            help=f"Total offspring: {row['Total_Head']:.0f}"
        )

# Footer with additional information
st.markdown("---")
st.markdown("### 📝 Analysis Notes")
st.info(f"""
- Analysis includes only sires with {min_offspring}+ offspring
- Total animals analyzed: {contingency_table.sum().sum():,}
- Number of qualifying sires: {len(significant_sires)}
""")

# Download section with both CSV and PDF options
st.markdown("### 💾 Download Options")
col1, col2 = st.columns(2)

with col1:
    # CSV download
    csv = quality_table.to_csv(index=True)
    st.download_button(
        label="📊 Download Full Analysis (CSV)",
        data=csv,
        file_name="sire_quality_analysis.csv",
        mime="text/csv",
        help="Download the raw data as a CSV file"
    )

with col2:
    # Generate PDF data
    def create_pdf_data():
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Sire Quality Analysis Report', ln=True, align='C')
        
        # Add date
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True)
        
        # Summary statistics
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Summary Statistics', ln=True)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Total Animals: {total_cattle}', ln=True)
        pdf.cell(0, 10, f'Total Sires: {total_sires}', ln=True)
        pdf.cell(0, 10, f'Average Prime %: {prime_percent:.1f}%', ln=True)
        
        # Top performers table
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Top Performing Sires', ln=True)
        
        # Convert quality table to PDF
        pdf.set_font('Arial', '', 10)
        cols = ['Prime', 'Choice', 'SE', 'Total_Head']
        pdf.cell(30, 10, 'Sire', 1)
        for col in cols:
            pdf.cell(30, 10, col, 1)
        pdf.ln()
        
        for idx, row in quality_table.head().iterrows():
            pdf.cell(30, 10, str(idx), 1)
            for col in cols:
                pdf.cell(30, 10, f"{row[col]:.1f}", 1)
            pdf.ln()
        
        return pdf.output(dest='S').encode('latin-1')

    # PDF download button
    st.download_button(
        label="📑 Download Report (PDF)",
        data=create_pdf_data(),
        file_name="sire_quality_analysis.pdf",
        mime="application/pdf",
        help="Download a formatted PDF report"
    )