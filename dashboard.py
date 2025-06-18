import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Flood Impact Analysis Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Power BI-like appearance with visible metrics
st.markdown("""
    <style>
    .main {
        padding: 0rem;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #000000;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #0066cc;
        font-weight: 500;
    }
    [data-testid="stMetricDelta"] {
        font-size: 14px;
        color: #595959;
    }
    div[data-testid="stHorizontalBlock"] > div {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        color: rgb(49, 51, 63);
        overflow-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('DATA BANJIR.xlsx')
    return df

try:
    df = load_data()
    
    # Sidebar filters
    with st.sidebar:
        st.header("📊 Filters")
        
        # NEGERI filter
        selected_negeri = st.multiselect(
            "Select NEGERI",
            options=df['NEGERI'].unique(),
            default=df['NEGERI'].unique()
        )
        
        # DAERAH filter
        selected_daerah = st.multiselect(
            "Select DAERAH",
            options=df[df['NEGERI'].isin(selected_negeri)]['DAERAH'].unique(),
            default=df[df['NEGERI'].isin(selected_negeri)]['DAERAH'].unique()
        )
        
        # KATEGORI filter
        selected_kategori = st.multiselect(
            "Select KATEGORI",
            options=df['KATEGORI'].unique(),
            default=df['KATEGORI'].unique()
        )

    # Filter the dataframe
    df_filtered = df[
        df['NEGERI'].isin(selected_negeri) &
        df['DAERAH'].isin(selected_daerah) &
        df['KATEGORI'].isin(selected_kategori)
    ]

    # Top metrics row with improved visibility
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_people = df_filtered['JUMLAH'].sum()
        st.metric("Total People Affected", f"{total_people:,}")
    
    with col2:
        total_locations = len(df_filtered['MUKIM'].unique())
        st.metric("Total Locations", total_locations)
    
    with col3:
        avg_people_per_location = total_people / total_locations if total_locations > 0 else 0
        st.metric("Avg. People per Location", f"{avg_people_per_location:.1f}")
    
    with col4:
        total_categories = len(df_filtered['KATEGORI'].unique())
        st.metric("Total Categories", total_categories)

    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution by Category and Gender
        category_gender_data = df_filtered.groupby(['KATEGORI', 'JANTINA'])['JUMLAH'].sum().reset_index()
        fig_category = px.bar(
            category_gender_data,
            x='KATEGORI',
            y='JUMLAH',
            color='JANTINA',
            title='Distribution by Category and Gender',
            barmode='group'
        )
        fig_category.update_layout(
            xaxis_title="Category",
            yaxis_title="Number of People",
            legend_title="Gender",
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_category, use_container_width=True)

    with col2:
        # Distribution by Location
        location_data = df_filtered.groupby('MUKIM')['JUMLAH'].sum().reset_index()
        fig_location = px.pie(
            location_data,
            values='JUMLAH',
            names='MUKIM',
            title='Distribution by Location'
        )
        fig_location.update_layout(plot_bgcolor='white')
        st.plotly_chart(fig_location, use_container_width=True)

    # Full width chart
    location_category_data = df_filtered.groupby(['MUKIM', 'KATEGORI'])['JUMLAH'].sum().reset_index()
    fig_heatmap = px.density_heatmap(
        location_category_data,
        x='MUKIM',
        y='KATEGORI',
        z='JUMLAH',
        title='Heat Map: Location vs Category',
        color_continuous_scale='Viridis'
    )
    fig_heatmap.update_layout(
        xaxis_title="Location",
        yaxis_title="Category",
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Add a treemap visualization
    fig_treemap = px.treemap(
        df_filtered,
        path=['NEGERI', 'DAERAH', 'MUKIM', 'KATEGORI'],
        values='JUMLAH',
        title='Hierarchical View of Affected Population'
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

    # Optional: Show filtered data table
    if st.checkbox("Show Detailed Data"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please make sure the Excel file 'DATA BANJIR.xlsx' is in the same directory as this script and contains the required columns.")