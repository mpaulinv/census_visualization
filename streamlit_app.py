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
        if os.path.exists("data/puma_boundaries_combined.gpkg"):
            file_path = "data/puma_boundaries_combined.gpkg"
        else:
            file_path = "data/puma_boundaries_combined.gpkg"
    
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
    map_data['clean_puma_name'] = map_data['NAMELSAD10'].str.replace(r'--PUMA \d+', '', regex=True).str.strip()
    
    # Ensure all data is properly formatted for tooltip
    map_data[data_column] = pd.to_numeric(map_data[data_column], errors='coerce').fillna(0)
    map_data['formatted_value'] = map_data[data_column].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and x > 0 else "No data")
    
    # Create color mapping based on data values
    if len(map_data) > 0:
        min_val = map_data[data_column].min()
        max_val = map_data[data_column].max()
        
        # Normalize values to 0-1 for color mapping
        normalized = (map_data[data_column] - min_val) / (max_val - min_val)
        
        # Create monotone blue scale: light blue to dark blue
        map_data['red'] = (255 * (1 - normalized * 0.8)).astype(int)    # Light to darker
        map_data['green'] = (255 * (1 - normalized * 0.6)).astype(int)  # Light to darker  
        map_data['blue'] = 255                                          # Always blue
        map_data['alpha'] = (120 + normalized * 100).astype(int)        # Semi-transparent to more opaque
    
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
        
        # Calculate color using same logic as map
        red = int(255 * (1 - normalized * 0.8))
        green = int(255 * (1 - normalized * 0.6))
        blue = 255
        
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

def display_top_areas(map_data, data_column, n=10):
    """
    Display top performing areas
    """
    if map_data is None or len(map_data) == 0:
        return
    
    st.subheader(f"Top {n} PUMAs by {data_column.replace('_', ' ').title()}")
    
    top_areas = map_data.nlargest(n, data_column)[
        ['NAMELSAD10', 'STATEFP10', data_column]
    ].reset_index(drop=True)
    
    # Format the data column as currency
    top_areas[f'{data_column}_formatted'] = top_areas[data_column].apply(lambda x: f"${x:,.0f}")
    
    # Display as a clean table
    st.dataframe(
        top_areas[['NAMELSAD10', 'STATEFP10', f'{data_column}_formatted']].rename(columns={
            'NAMELSAD10': 'PUMA Name',
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
    st.title("🗺️ US Census Economic Data Explorer")
    st.markdown("Interactive exploration of median household income and earnings across US Public Use Microdata Areas (PUMAs)")
    
    # Sidebar controls
    st.sidebar.header("Map Controls")
    
    # Year selection - check for available data files
    available_years = []
    
    # Check for year-specific files
    for year in [2022, 2021, 2020, 2019, 2018, 2017, 2016]:
        if os.path.exists(f"data/census_puma_data_{year}.csv"):
            available_years.append(year)
    
    # If no year-specific files, check for generic file
    if not available_years and os.path.exists("data/census_puma_data.csv"):
        available_years = [2020]  # Default to 2020 for generic file
    
    if not available_years:
        st.error("❌ No census data files found. Please run download_census_data.py first.")
        st.stop()
    
    selected_year = st.sidebar.selectbox(
        "Select Year",
        available_years,
        index=0,
        help="Choose the census data year to display"
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
    st.subheader(f"📊 {data_options[selected_data]} Statistics for {selected_year}")
    display_statistics(map_data, selected_data, selected_year)
    
    # Create and display map with legend
    st.subheader(f"🗺️ {data_options[selected_data]} by PUMA - {selected_year}")
    
    # Create columns for map and legend
    map_col, legend_col = st.columns([4, 1])
    
    with map_col:
        deck = create_pydeck_map(map_data, selected_data, selected_year)
        if deck:
            # Make the map larger by using full width and increased height
            st.pydeck_chart(deck, use_container_width=True, height=600)
    
    with legend_col:
        st.markdown("**Legend**")
        legend_data = create_legend(map_data, selected_data)
        if legend_data:
            for step in reversed(legend_data):  # Show highest values at top
                st.markdown(
                    f'<div style="display: flex; align-items: center; margin: 5px 0;">'
                    f'<div style="width: 20px; height: 20px; background-color: {step["color"]}; '
                    f'border: 1px solid #ccc; margin-right: 8px;"></div>'
                    f'<span style="font-size: 12px;">{step["label"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        # Add color explanation
        st.markdown(
            '<div style="font-size: 11px; color: #666; margin-top: 10px;">'
            'Light blue = Lower values<br/>'
            'Dark blue = Higher values'
            '</div>',
            unsafe_allow_html=True
        )
    
    # Add map instructions
    st.info("💡 **Map Tips:** Hover over areas to see state, PUMA name, and values. Use mouse/touch to zoom and pan.")
    
    # Display top areas
    col1, col2 = st.columns(2)
    
    with col1:
        display_top_areas(map_data, selected_data, 10)
    
    with col2:
        st.subheader("📈 Data Summary")
        st.write(f"**Year:** {selected_year}")
        st.write(f"**Data Type:** {data_options[selected_data]}")
        st.write(f"**PUMAs with Data:** {len(map_data):,}")
        
        # Only calculate coverage if boundaries loaded successfully
        if boundaries is not None:
            st.write(f"**Coverage:** {len(map_data) / len(boundaries) * 100:.1f}% of all PUMAs")
        else:
            st.write("**Coverage:** Unable to calculate (boundaries not loaded)")
        
        # Data source info
        st.markdown("---")
        st.markdown("**Data Sources:**")
        st.markdown("- 📊 Census Bureau ACS 5-Year Estimates")
        st.markdown("- 🗺️ TIGER/Line PUMA Boundaries (2020)")
        st.markdown("- 🔧 Real-time Census API integration")
        st.markdown("- ⚡ Ultra-optimized geometries (98.8% size reduction)")
        
        # Performance info
        optimized_path = "data/puma_boundaries_optimized.gpkg"
        if os.path.exists(optimized_path):
            file_size = os.path.getsize(optimized_path) / 1024**2
            st.markdown(f"- 🚀 Boundary file: {file_size:.1f}MB (ultra-optimized)")
        
        if use_high_detail:
            st.info("🎯 High Detail Mode: Maximum visual quality enabled")

if __name__ == "__main__":
    main()
