import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static

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
    .section-title-black {
        color: #111;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
        margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('DATA BANJIR.xlsx')
    # Extract latitude and longitude from KOORDINAT column
    df[['LATITUDE', 'LONGITUDE']] = df['KOORDINAT'].str.extract(r'(\d+\.\d+)°\s*[NS],\s*(\d+\.\d+)°\s*[EW]')
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'])
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'])
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

    # Center the map using columns and set the section title to black
    st.markdown('<div class="section-title-black">Flood Location Map</div>', unsafe_allow_html=True)
    map_col1, map_col2, map_col3 = st.columns([1,2,1])
    with map_col2:
        m = folium.Map(
            location=[df_filtered['LATITUDE'].mean(), df_filtered['LONGITUDE'].mean()],
            zoom_start=12,
            tiles='CartoDB dark_matter'
        )
        for idx, row in df_filtered.drop_duplicates(subset=['MUKIM', 'LATITUDE', 'LONGITUDE']).iterrows():
            location_total = df_filtered[
                (df_filtered['LATITUDE'] == row['LATITUDE']) & 
                (df_filtered['LONGITUDE'] == row['LONGITUDE'])
            ]['JUMLAH'].sum()
            popup_content = f"""
                <b>Location:</b> {row['MUKIM']}<br>
                <b>District:</b> {row['DAERAH']}<br>
                <b>Total Affected:</b> {location_total:,} people
            """
            folium.CircleMarker(
                location=[row['LATITUDE'], row['LONGITUDE']],
                radius=10,
                popup=folium.Popup(popup_content, max_width=300),
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.8
            ).add_to(m)
        folium_static(m)

    # Full width charts
    st.subheader("Detailed Analysis")
    # Heat Map
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

    # Treemap visualization
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