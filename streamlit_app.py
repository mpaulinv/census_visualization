import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import os
import numpy as np
# from scripts.preprocess_boundaries import load_optimized_boundaries

def load_optimized_boundaries(file_path=None):
    """Load optimized PUMA boundaries with smart path detection - prioritizing standard optimization"""
    print("🗺️ Loading PUMA boundaries...")
    
    # Try standard optimized file first (better quality, moderate size)
    if file_path is None:
        if os.path.exists("data/puma_boundaries_moderate.gpkg"):
            file_path = "data/puma_boundaries_moderate.gpkg"
        else:
            file_path = "data/puma_boundaries_moderate.gpkg"
    
    # Try to load standard optimized file first
    if os.path.exists(file_path):
        print("📊 Loading standard optimized boundaries...")
        try:
            boundaries = gpd.read_file(file_path)
            file_size = os.path.getsize(file_path) / 1024**2
            print(f"✅ Loaded {len(boundaries)} PUMA boundaries ({file_size:.1f}MB)")
            return boundaries
        except Exception as e:
            print(f"❌ Error loading standard optimized file: {e}")
    
    # Fallback to ultra-optimized file only if standard not available
    ultra_optimized_path = "data/puma_boundaries_optimized.gpkg"
    if os.path.exists(ultra_optimized_path):
        print("⚡ Falling back to ULTRA-optimized boundaries...")
        try:
            boundaries = gpd.read_file(ultra_optimized_path)
            file_size = os.path.getsize(ultra_optimized_path) / 1024**2
            print(f"✅ Loaded {len(boundaries)} PUMA boundaries ({file_size:.1f}MB)")
            return boundaries
        except Exception as e:
            print(f"❌ Error loading ultra-optimized file: {e}")
    
    print(f"❌ No boundary files found")
    return None

# Configure Streamlit page
st.set_page_config(
    page_title="US Census Economic Data Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_census_data(year):
    """
    Load census data for a specific year with caching
    """
    # First try year-specific file
    file_path = f"data/census_puma_data_{year}.csv"
    
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            st.error(f"Error loading census data for {year}: {e}")
            return None
    
    # Fallback to generic file (add year column if missing)
    generic_path = "data/census_puma_data.csv"
    if os.path.exists(generic_path):
        try:
            df = pd.read_csv(generic_path)
            # Add year column if it doesn't exist
            if 'year' not in df.columns:
                df['year'] = year
            return df
        except Exception as e:
            st.error(f"Error loading census data: {e}")
            return None
    
    return None

@st.cache_data
def load_boundaries(simplification_tolerance=0.005):
    """
    Load preprocessed PUMA boundaries with caching - prioritizing moderate optimization for balanced quality
    """
    try:
        # Priority order: moderate > standard > ultra-optimized
        moderate_path = "data/puma_boundaries_moderate.gpkg"
        standard_path = "data/puma_boundaries_combined.gpkg"
        ultra_optimized_path = "data/puma_boundaries_optimized.gpkg"
        
        if os.path.exists(moderate_path):
            boundaries = gpd.read_file(moderate_path)
            file_size = os.path.getsize(moderate_path) / 1024**2
            print(f"✅ Loaded moderate optimized boundaries: {len(boundaries)} PUMAs ({file_size:.1f}MB)")
        elif os.path.exists(standard_path):
            boundaries = gpd.read_file(standard_path)
            file_size = os.path.getsize(standard_path) / 1024**2
            print(f"✅ Loaded standard optimized boundaries: {len(boundaries)} PUMAs ({file_size:.1f}MB)")
        elif os.path.exists(ultra_optimized_path):
            boundaries = gpd.read_file(ultra_optimized_path)
            file_size = os.path.getsize(ultra_optimized_path) / 1024**2
            print(f"✅ Loaded ultra-optimized boundaries: {len(boundaries)} PUMAs ({file_size:.1f}MB)")
            # Apply simplification if using fallback
            if simplification_tolerance > 0.001:
                boundaries['geometry'] = boundaries['geometry'].simplify(
                    tolerance=simplification_tolerance, preserve_topology=True
                )
        else:
            st.error("❌ No boundary files found. Please run ultra_optimize_boundaries.py first.")
            return None
        
        # Ensure CRS is WGS84 for web mapping
        if boundaries.crs != 'EPSG:4326':
            boundaries = boundaries.to_crs('EPSG:4326')
        
        # Filter to continental US only (exclude Alaska, Hawaii, Puerto Rico, etc.)
        # Continental US state FIPS codes: 01-56 excluding AK(02), HI(15), PR(72), etc.
        continental_states = [str(i).zfill(2) for i in range(1, 57) if i not in [2, 15]]
        boundaries = boundaries[boundaries['STATEFP10'].isin(continental_states)]
        print(f"✅ Filtered to continental US: {len(boundaries)} PUMAs")
            
        return boundaries
    except Exception as e:
        st.error(f"Error loading boundaries: {e}")
        return None

def prepare_map_data(boundaries, census_data, data_column):
    """
    Merge boundaries with census data and prepare for mapping
    """
    if boundaries is None or census_data is None:
        return None
    
    # Merge boundaries with census data
    map_data = boundaries.merge(
        census_data, 
        left_on='PUMA_FULL_INT', 
        right_on='puma_full_id', 
        how='left'
    )
    
    # Fill missing values
    map_data[data_column] = map_data[data_column].fillna(0)
    
    # Filter out areas with no data for cleaner visualization
    map_data = map_data[map_data[data_column] > 0]
    
    # Add state names for better tooltip
    state_names = {
        '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', '06': 'California',
        '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'District of Columbia',
        '12': 'Florida', '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho', '17': 'Illinois',
        '18': 'Indiana', '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana',
        '23': 'Maine', '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
        '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada',
        '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico', '36': 'New York',
        '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio', '40': 'Oklahoma',
        '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island', '45': 'South Carolina',
        '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah', '50': 'Vermont',
        '51': 'Virginia', '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
    }
    
    map_data['state_name'] = map_data['STATEFP10'].map(state_names).fillna('Unknown State')
    
    # Clean up PUMA names for better display
    # Remove '--PUMA <digits>' and trailing 'PUMA' (with or without space before)
    map_data['clean_puma_name'] = map_data['NAMELSAD10']
    map_data['clean_puma_name'] = map_data['clean_puma_name'].str.replace(r'--PUMA \d+', '', regex=True)
    map_data['clean_puma_name'] = map_data['clean_puma_name'].str.replace(r'\s*PUMA$', '', regex=True)
    map_data['clean_puma_name'] = map_data['clean_puma_name'].str.strip()
    
    # Ensure all data is properly formatted for tooltip
    map_data[data_column] = pd.to_numeric(map_data[data_column], errors='coerce').fillna(0)
    map_data['formatted_value'] = map_data[data_column].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and x > 0 else "No data")
    
    # Create color mapping based on data values
    if len(map_data) > 0:
        min_val = map_data[data_column].min()
        max_val = map_data[data_column].max()
        # Normalize values to 0-1 for color mapping
        normalized = (map_data[data_column] - min_val) / (max_val - min_val)
        # White to orange gradient for professional appearance
        # Low values: Almost white (#FEFEFE)
        # High values: Deep orange (#D97706)
        map_data['red'] = (254 - normalized * 37).astype(int)     # 254 to 217
        map_data['green'] = (254 - normalized * 135).astype(int)  # 254 to 119  
        map_data['blue'] = (254 - normalized * 248).astype(int)   # 254 to 6
        map_data['alpha'] = (180 + normalized * 75).astype(int)   # 180 to 255 for subtle transparency
    
    return map_data

def create_pydeck_map(map_data, data_column, year):
    """
    Create PyDeck map visualization
    """
    if map_data is None or len(map_data) == 0:
        st.warning("No data available for mapping")
        return None
    
    # Set fixed center for continental US for consistent viewing
    center_lat = 39.8283  # Geographic center of continental US
    center_lon = -98.5795
    
    # Create PyDeck layer with improved quality and clear divisions
    layer = pdk.Layer(
        "GeoJsonLayer",
        map_data,
        pickable=True,
        stroked=True,
        filled=True,
        extruded=False,
        get_fill_color="[red, green, blue, alpha]",
        get_line_color=[80, 80, 80, 120],  # Clear dark gray borders for better division visibility
        line_width_min_pixels=0.5,  # Slightly thicker borders for clarity
        line_width_scale=1,
        wireframe=False,
    )
    
    # Create view state centered on continental US
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=4.2,  # Slightly zoomed in for continental US
        pitch=0,
        bearing=0
    )
    
    # Create tooltip with proper data formatting
    if 'HINCP' in data_column.upper():
        metric_name = "Median Household Income"
    elif 'WAGP' in data_column.upper():
        metric_name = "Median Earnings"
    else:
        metric_name = data_column.replace('_', ' ').title()
    
    # Create tooltip with pre-formatted values
    tooltip = {
        "html": """
        <b>{state_name}</b><br/>
        <b>{clean_puma_name}</b><br/>
        <b>""" + metric_name + """:</b> {formatted_value}
        """,
        "style": {
            "backgroundColor": "rgba(0, 0, 0, 0.8)",
            "color": "white",
            "border": "1px solid white",
            "borderRadius": "8px",
            "padding": "12px",
            "fontSize": "14px"
        }
    }
    
    # Create deck with improved styling
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10"  # Cleaner, more modern map style
    )
    
    return deck

def create_legend(map_data, data_column):
    """
    Create a color legend for the map
    """
    if map_data is None or len(map_data) == 0 or data_column not in map_data.columns:
        return None
    
    min_val = map_data[data_column].min()
    max_val = map_data[data_column].max()
    
    # Create 5 legend steps
    legend_steps = []
    for i in range(5):
        value = min_val + (max_val - min_val) * i / 4
        normalized = i / 4
        # White to orange gradient
        red = int(254 - normalized * 37)
        green = int(254 - normalized * 135)
        blue = int(254 - normalized * 248)
        legend_steps.append({
            'value': value,
            'color': f'rgb({red}, {green}, {blue})',
            'label': f'${value:,.0f}'
        })
    
    return legend_steps

def display_statistics(map_data, data_column, year):
    """
    Display statistics about the data
    """
    if map_data is None or len(map_data) == 0:
        st.warning("No data available for statistics")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total PUMAs", 
            f"{len(map_data):,}"
        )
    
    with col2:
        avg_value = map_data[data_column].mean()
        st.metric(
            f"Average {data_column.replace('_', ' ').title()}", 
            f"${avg_value:,.0f}"
        )
    
    with col3:
        max_value = map_data[data_column].max()
        st.metric(
            f"Maximum {data_column.replace('_', ' ').title()}", 
            f"${max_value:,.0f}"
        )
    
    with col4:
        min_value = map_data[data_column].min()
        st.metric(
            f"Minimum {data_column.replace('_', ' ').title()}", 
            f"${min_value:,.0f}"
        )

def display_top_and_bottom_areas(map_data, data_column, n=5):
    """
    Display top 5 and bottom 5 performing areas
    """
    if map_data is None or len(map_data) == 0:
        return
    
    # Get top 5 areas
    top_areas = map_data.nlargest(n, data_column)[['clean_puma_name', 'STATEFP10', data_column]].reset_index(drop=True)
    # Get bottom 5 areas
    bottom_areas = map_data.nsmallest(n, data_column)[['clean_puma_name', 'STATEFP10', data_column]].reset_index(drop=True)
    # Format the data columns as currency
    top_areas[f'{data_column}_formatted'] = top_areas[data_column].apply(lambda x: f"${x:,.0f}")
    bottom_areas[f'{data_column}_formatted'] = bottom_areas[data_column].apply(lambda x: f"${x:,.0f}")
    # Display top areas
    st.markdown("#### Highest Values")
    st.dataframe(
        top_areas[['clean_puma_name', 'STATEFP10', f'{data_column}_formatted']].rename(columns={
            'clean_puma_name': 'Area',
            'STATEFP10': 'State',
            f'{data_column}_formatted': data_column.replace('_', ' ').title()
        }),
        use_container_width=True,
        hide_index=True
    )
    # Add minimal spacing
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    # Display bottom areas
    st.markdown("#### Lowest Values")
    st.dataframe(
        bottom_areas[['clean_puma_name', 'STATEFP10', f'{data_column}_formatted']].rename(columns={
            'clean_puma_name': 'Area',
            'STATEFP10': 'State',
            f'{data_column}_formatted': data_column.replace('_', ' ').title()
        }),
        use_container_width=True,
        hide_index=True
    )

def main():
    """
    Main Streamlit app
    """
    st.markdown("<h1 class='address-title'>US Census Economic Data Explorer</h1>", unsafe_allow_html=True)
    st.markdown("<div class='address-subtitle'>Interactive exploration of median household income and earnings across US Public Use Microdata Areas (PUMAs)</div>", unsafe_allow_html=True)
    
    # Sidebar controls
    st.sidebar.markdown("<h2 class='address-sidebar-header'>Map Controls</h2>", unsafe_allow_html=True)
    
    # Year selection - check for available data files
    available_years = []
    for year in [2022, 2021, 2020, 2019, 2018, 2017, 2016]:
        if os.path.exists(f"data/census_puma_data_{year}.csv"):
            available_years.append(year)
    if not available_years and os.path.exists("data/census_puma_data.csv"):
        available_years = [2020]
    if not available_years:
        st.error("❌ No census data files found. Please run download_census_data.py first.")
        st.stop()
    # Replace selectbox with slider and arrow icon
    st.sidebar.markdown("<div class='address-sidebar-label'>Select Year</div>", unsafe_allow_html=True)
    selected_year = st.sidebar.slider(
        "Year",
        min_value=min(available_years),
        max_value=max(available_years),
        value=max(available_years),
        step=1,
        format="%d"
    )
    
    # Data type selection
    data_options = {
        "median_household_income": "Median Household Income",
        "median_earnings": "Median Earnings"
    }
    
    selected_data = st.sidebar.selectbox(
        "Select Data Type",
        list(data_options.keys()),
        format_func=lambda x: data_options[x],
        help="Choose the economic indicator to visualize"
    )
    
    # Simple performance toggle (since we have ultra-optimized file)
    st.sidebar.subheader("🚀 Performance")
    
    use_high_detail = st.sidebar.checkbox(
        "High Detail Mode",
        value=False,
        help="Enable for highest visual quality (slightly slower loading)"
    )
    
    # Set simplification based on detail mode
    simplification_tolerance = 0.001 if use_high_detail else 0.005
    
    # Load data
    with st.spinner("Loading data..."):
        # Load boundaries (cached) with user-selected quality
        boundaries = load_boundaries(simplification_tolerance)
        
        if boundaries is None:
            st.error("❌ Could not load PUMA boundaries. Please run preprocess_boundaries.py first.")
            st.stop()
        
        # Load census data for selected year
        census_data = load_census_data(selected_year)
        
        if census_data is None:
            st.error(f"❌ Could not load census data for {selected_year}. Please run download_census_data.py first.")
            st.stop()
    
    # Prepare map data
    with st.spinner("Preparing map..."):
        map_data = prepare_map_data(boundaries, census_data, selected_data)
    
    if map_data is None or len(map_data) == 0:
        st.error("No data available for the selected year and data type.")
        st.stop()
    
    # Display statistics
    st.markdown(f"<h2 class='address-section-header'>{data_options[selected_data]} Statistics for {selected_year}</h2>", unsafe_allow_html=True)
    display_statistics(map_data, selected_data, selected_year)
    
    # Create and display map with legend
    st.markdown(f"<h2 class='address-section-header'>{data_options[selected_data]} by PUMA - {selected_year}</h2>", unsafe_allow_html=True)
    
    # Create columns for map and legend
    map_col, legend_col = st.columns([4, 1])
    
    with map_col:
        deck = create_pydeck_map(map_data, selected_data, selected_year)
        if deck:
            # Make the map larger by using full width and increased height
            st.pydeck_chart(deck, use_container_width=True, height=600)
    
    with legend_col:
        st.markdown("<div class='address-legend-label'>Legend</div>", unsafe_allow_html=True)
        legend_data = create_legend(map_data, selected_data)
        if legend_data:
            # Horizontal legend bar
            legend_html = "<div class='address-legend-bar'>"
            for step in legend_data:
                legend_html += f"<div class='address-legend-step' style='background:{step['color']}'></div>"
            legend_html += "</div>"
            # Labels below
            label_html = "<div class='address-legend-labels'>"
            for step in legend_data:
                label_html += f"<span>{step['label']}</span>"
            label_html += "</div>"
            st.markdown(legend_html + label_html, unsafe_allow_html=True)
    
    # Add map instructions
    st.markdown("<div class='address-map-tips'>Map Tips: Hover over areas to see state, PUMA name, and values. Use mouse/touch to zoom and pan.</div>", unsafe_allow_html=True)
    
    # Display top and bottom areas
    col1, col2 = st.columns(2)
    
    with col1:
        display_top_and_bottom_areas(map_data, selected_data, 5)
    
    with col2:
        st.markdown("<h3 class='address-section-header'>Data Summary</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='address-summary'><strong>Year:</strong> {selected_year}<br><strong>Data Type:</strong> {data_options[selected_data]}<br><strong>PUMAs with Data:</strong> {len(map_data):,}</div>", unsafe_allow_html=True)
        if boundaries is not None:
            st.markdown(f"<div class='address-summary'><strong>Coverage:</strong> {len(map_data) / len(boundaries) * 100:.1f}% of all PUMAs</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='address-summary'><strong>Coverage:</strong> Unable to calculate (boundaries not loaded)</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='address-summary'><strong>Data Sources:</strong><ul><li>Census Bureau ACS 5-Year Estimates</li><li>TIGER/Line PUMA Boundaries (2020)</li><li>Real-time Census API integration</li><li>Ultra-optimized geometries (98.8% size reduction)</li></ul></div>", unsafe_allow_html=True)
        optimized_path = "data/puma_boundaries_optimized.gpkg"
        if os.path.exists(optimized_path):
            file_size = os.path.getsize(optimized_path) / 1024**2
            st.markdown(f"<div class='address-summary'>Boundary file: {file_size:.1f}MB (ultra-optimized)</div>", unsafe_allow_html=True)
        if use_high_detail:
            st.markdown("<div class='address-summary'>High Detail Mode: Maximum visual quality enabled</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()


st.markdown("""
<style>
    body, .main, .stApp {
        background: #fff;
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
        color: #222;
    }
    .address-title {
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #222;
        margin-bottom: 0.5rem;
    }
    .address-subtitle {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .address-sidebar-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #222;
        margin-bottom: 1.2rem;
        letter-spacing: 0.5px;
    }
    .address-sidebar-label {
        font-size: 1rem;
        color: #222;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .address-section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #222;
        margin-top: 2rem;
        margin-bottom: 1rem;
        letter-spacing: 0.5px;
    }
    .address-legend-label {
        font-size: 1rem;
        font-weight: 600;
        color: #222;
        margin-bottom: 0.5rem;
    }
    .address-legend-bar {
        display: flex;
        height: 18px;
        border-radius: 9px;
        overflow: hidden;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border: 1px solid #eee;
    }
    .address-legend-step {
        flex: 1;
        height: 100%;
    }
    .address-legend-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.95rem;
        color: #555;
        margin-bottom: 1rem;
    }
    .address-map-tips {
        background: #f7f7f7;
        color: #222;
        font-size: 1rem;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin: 1.5rem 0;
        border: 1px solid #eee;
        font-weight: 500;
    }
    .address-summary {
        font-size: 1rem;
        color: #222;
        margin-bottom: 0.7rem;
        font-weight: 400;
    }
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #fff;
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
        font-size: 1rem;
    }
    .stDataFrame table {
        font-weight: 600;
        border-collapse: separate;
        border-spacing: 0;
    }
    .stDataFrame th {
        background: #fffbe6;
        color: #222;
        font-weight: 700;
        font-size: 1.05rem;
        border-bottom: 2px solid #f7c948;
    }
    .stDataFrame td {
        background: #fff;
        color: #222;
        font-weight: 500;
        border-bottom: 1px solid #f0f0f0;
    }
    .stDataFrame tr:nth-child(even) td {
        background: #f7f7f7;
    }
    .stSidebar {
        background-color: #fff;
        border-right: 1px solid #e2e8f0;
    }
    .stSelectbox > div > div {
        background-color: #fff;
        border: 1px solid #e2e8f0;
    }
    .stSlider > div > div > div {
        color: #f7c948;
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .stAlert > div {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #4a5568;
    }
</style>
""", unsafe_allow_html=True)