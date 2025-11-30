"""
US Census Economic Data Explorer - UNIFIED EDITION
Dark/Light theme toggle with full-bleed map
"""
import streamlit as st

# Set page config FIRST before any other st calls
st.set_page_config(
    page_title="Economic Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Now import the rest
import geopandas as gpd
import polars as pl
import pydeck as pdk
import os
import pickle
from pathlib import Path

# Lazy load plotly only when needed
@st.cache_resource
def get_plotly():
    import plotly.express as px
    import plotly.graph_objects as go
    return px, go

# Get the base directory (parent of scripts folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

@st.cache_data
def get_theme_css(is_dark):
    if is_dark:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --font-display: 'Space Grotesk', -apple-system, sans-serif;
            --font-body: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
            --bg-main: #0f172a;
            --bg-panel: rgba(15, 23, 42, 0.92);
            --bg-card: rgba(30, 41, 59, 0.7);
            --bg-hover: rgba(51, 65, 85, 0.5);
            --border-subtle: rgba(148, 163, 184, 0.15);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent: #38bdf8;
            --accent-rgb: 56, 189, 248;
            --accent-glow: rgba(56, 189, 248, 0.3);
        }
        
        html, body, .main, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--bg-main) !important;
            color: var(--text-primary) !important;
        }
        
        #MainMenu, footer, header, 
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stDeployButton,
        .viewerBadge_container__r5tak,
        section[data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
        }
        
        .block-container { padding: 0 !important; max-width: 100% !important; }
        .stApp > header { display: none !important; }
        div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
        
        .top-nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 56px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.85) 100%);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            z-index: 1000;
        }
        
        .nav-brand { display: flex; align-items: center; gap: 12px; }
        .nav-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--text-primary); }
        .nav-subtitle { font-family: var(--font-body); font-size: 12px; color: var(--text-muted); margin-left: 16px; padding-left: 16px; border-left: 1px solid var(--border-subtle); }
        .nav-links { display: flex; align-items: center; gap: 8px; }
        .nav-link { font-family: var(--font-body); font-size: 13px; font-weight: 500; color: var(--text-secondary); padding: 8px 14px; border-radius: 6px; cursor: pointer; }
        .nav-link:hover { color: var(--text-primary); background: var(--bg-hover); }
        .nav-link.active { color: var(--accent); background: rgba(var(--accent-rgb), 0.1); }
        
        .theme-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .theme-toggle:hover { border-color: var(--accent); }
        .theme-icon { font-size: 16px; }
        .theme-label { font-family: var(--font-body); font-size: 12px; color: var(--text-secondary); }
        
        .panel-label { font-family: var(--font-body); font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
        
        .stat-card {
            background: var(--bg-panel);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .stat-card:hover { border-color: var(--accent); box-shadow: 0 0 40px rgba(var(--accent-rgb), 0.15); }
        .stat-label { font-family: var(--font-body); font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
        .stat-value { font-family: var(--font-mono); font-size: 22px; font-weight: 600; color: var(--text-primary); }
        .stat-value.accent { color: var(--accent); text-shadow: 0 0 20px var(--accent-glow); }
        
        .stSelectbox label { font-family: var(--font-body) !important; font-size: 10px !important; font-weight: 600 !important; color: var(--text-muted) !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
        .stSelectbox > div > div { background: var(--bg-card) !important; border: 1px solid var(--border-subtle) !important; border-radius: 8px !important; color: var(--text-primary) !important; }
        .stSelectbox > div > div:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important; }
        
        [data-baseweb="popover"] { background: var(--bg-panel) !important; border: 1px solid var(--border-subtle) !important; border-radius: 10px !important; backdrop-filter: blur(20px) !important; }
        [role="option"] { background: transparent !important; color: var(--text-secondary) !important; }
        [role="option"]:hover { background: var(--bg-hover) !important; color: var(--text-primary) !important; }
        [aria-selected="true"] { background: rgba(var(--accent-rgb), 0.15) !important; color: var(--accent) !important; }
        
        .stRadio > label { font-family: var(--font-body) !important; font-size: 10px !important; font-weight: 600 !important; color: var(--text-muted) !important; text-transform: uppercase !important; }
        .stRadio [data-baseweb="radio"] label { color: var(--text-secondary) !important; font-size: 13px !important; }
        .stRadio [data-baseweb="radio"]:has(input:checked) label { color: var(--text-primary) !important; }
        
        .stTabs [data-baseweb="tab-list"] { background: var(--bg-card) !important; border-radius: 8px !important; padding: 4px !important; border: 1px solid var(--border-subtle) !important; }
        .stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--text-secondary) !important; font-family: var(--font-body) !important; font-size: 12px !important; border-radius: 6px !important; }
        .stTabs [data-baseweb="tab"]:hover { background: var(--bg-hover) !important; }
        .stTabs [aria-selected="true"] { background: var(--bg-panel) !important; color: var(--accent) !important; }
        .stTabs [data-baseweb="tab-panel"] { padding: 16px 0 0 0 !important; }
        [data-testid="column"] { padding: 0 8px !important; }
        
        .stButton > button {
            background: transparent !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 20px !important;
            color: var(--text-secondary) !important;
            padding: 4px 16px !important;
            font-size: 12px !important;
        }
        .stButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
        }
        
        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
            .top-nav { flex-direction: column !important; padding: 12px 16px !important; gap: 8px !important; }
            .nav-brand { text-align: center !important; }
            .nav-title { font-size: 16px !important; }
            .nav-subtitle { font-size: 10px !important; display: none !important; }
            .nav-links { display: none !important; }
            [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; padding: 0 4px !important; }
            .stat-card { padding: 12px !important; margin-bottom: 8px !important; }
            .stat-value { font-size: 18px !important; }
            .stat-label { font-size: 9px !important; }
            .panel-label { font-size: 9px !important; margin-bottom: 6px !important; }
            [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
            iframe { min-height: 400px !important; }
            .stButton > button { padding: 8px 12px !important; font-size: 11px !important; width: 100% !important; }
            .js-plotly-plot { width: 100% !important; }
        }
        @media (max-width: 480px) {
            .nav-title { font-size: 14px !important; }
            .stat-value { font-size: 16px !important; }
            iframe { min-height: 350px !important; }
        }
        </style>
        """
    else:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --font-display: 'Space Grotesk', -apple-system, sans-serif;
            --font-body: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
            --bg-main: #f8fafc;
            --bg-panel: rgba(255, 255, 255, 0.92);
            --bg-card: rgba(241, 245, 249, 0.8);
            --bg-hover: rgba(226, 232, 240, 0.6);
            --border-subtle: rgba(148, 163, 184, 0.25);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --accent: #ea580c;
            --accent-rgb: 234, 88, 12;
            --accent-glow: rgba(234, 88, 12, 0.2);
        }
        
        html, body, .main, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--bg-main) !important;
            color: var(--text-primary) !important;
        }
        
        #MainMenu, footer, header, 
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stDeployButton,
        .viewerBadge_container__r5tak,
        section[data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
        }
        
        .block-container { padding: 0 !important; max-width: 100% !important; }
        .stApp > header { display: none !important; }
        div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
        
        .top-nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 56px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.92) 100%);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            z-index: 1000;
        }
        
        .nav-brand { display: flex; align-items: center; gap: 12px; }
        .nav-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--text-primary); }
        .nav-subtitle { font-family: var(--font-body); font-size: 12px; color: var(--text-muted); margin-left: 16px; padding-left: 16px; border-left: 1px solid var(--border-subtle); }
        .nav-links { display: flex; align-items: center; gap: 8px; }
        .nav-link { font-family: var(--font-body); font-size: 13px; font-weight: 500; color: var(--text-secondary); padding: 8px 14px; border-radius: 6px; cursor: pointer; }
        .nav-link:hover { color: var(--text-primary); background: var(--bg-hover); }
        .nav-link.active { color: var(--accent); background: rgba(var(--accent-rgb), 0.1); }
        
        .theme-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .theme-toggle:hover { border-color: var(--accent); }
        .theme-icon { font-size: 16px; }
        .theme-label { font-family: var(--font-body); font-size: 12px; color: var(--text-secondary); }
        
        .panel-label { font-family: var(--font-body); font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
        
        .stat-card {
            background: var(--bg-panel);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .stat-card:hover { border-color: var(--accent); }
        .stat-label { font-family: var(--font-body); font-size: 10px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
        .stat-value { font-family: var(--font-mono); font-size: 22px; font-weight: 600; color: var(--text-primary); }
        .stat-value.accent { color: var(--accent); }
        
        .stSelectbox label { font-family: var(--font-body) !important; font-size: 10px !important; font-weight: 600 !important; color: var(--text-muted) !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
        .stSelectbox > div > div { background: white !important; border: 1px solid var(--border-subtle) !important; border-radius: 8px !important; color: var(--text-primary) !important; }
        .stSelectbox > div > div:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important; }
        
        [data-baseweb="popover"] { background: white !important; border: 1px solid var(--border-subtle) !important; border-radius: 10px !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15) !important; }
        [role="option"] { background: transparent !important; color: var(--text-secondary) !important; }
        [role="option"]:hover { background: var(--bg-hover) !important; color: var(--text-primary) !important; }
        [aria-selected="true"] { background: rgba(var(--accent-rgb), 0.1) !important; color: var(--accent) !important; }
        
        .stRadio > label { font-family: var(--font-body) !important; font-size: 10px !important; font-weight: 600 !important; color: var(--text-muted) !important; text-transform: uppercase !important; }
        .stRadio [data-baseweb="radio"] label { color: var(--text-secondary) !important; font-size: 13px !important; }
        .stRadio [data-baseweb="radio"]:has(input:checked) label { color: var(--text-primary) !important; }
        
        .stTabs [data-baseweb="tab-list"] { background: var(--bg-card) !important; border-radius: 8px !important; padding: 4px !important; border: 1px solid var(--border-subtle) !important; }
        .stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--text-secondary) !important; font-family: var(--font-body) !important; font-size: 12px !important; border-radius: 6px !important; }
        .stTabs [data-baseweb="tab"]:hover { background: var(--bg-hover) !important; }
        .stTabs [aria-selected="true"] { background: white !important; color: var(--accent) !important; box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important; }
        .stTabs [data-baseweb="tab-panel"] { padding: 16px 0 0 0 !important; }
        [data-testid="column"] { padding: 0 8px !important; }
        
        .stButton > button {
            background: transparent !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 20px !important;
            color: var(--text-secondary) !important;
            padding: 4px 16px !important;
            font-size: 12px !important;
        }
        .stButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
        }
        
        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
            .top-nav { flex-direction: column !important; padding: 12px 16px !important; gap: 8px !important; }
            .nav-brand { text-align: center !important; }
            .nav-title { font-size: 16px !important; }
            .nav-subtitle { font-size: 10px !important; display: none !important; }
            .nav-links { display: none !important; }
            [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; padding: 0 4px !important; }
            .stat-card { padding: 12px !important; margin-bottom: 8px !important; }
            .stat-value { font-size: 18px !important; }
            .stat-label { font-size: 9px !important; }
            .panel-label { font-size: 9px !important; margin-bottom: 6px !important; }
            [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
            iframe { min-height: 400px !important; }
            .stButton > button { padding: 8px 12px !important; font-size: 11px !important; width: 100% !important; }
            .js-plotly-plot { width: 100% !important; }
        }
        @media (max-width: 480px) {
            .nav-title { font-size: 14px !important; }
            .stat-value { font-size: 16px !important; }
            iframe { min-height: 350px !important; }
        }
        </style>
        """

# Apply theme CSS
is_dark = st.session_state.theme == 'dark'
st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)

# Constants
STATE_NAMES = {
    '01': 'Alabama', '04': 'Arizona', '05': 'Arkansas', '06': 'California',
    '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'DC',
    '12': 'Florida', '13': 'Georgia', '16': 'Idaho', '17': 'Illinois',
    '18': 'Indiana', '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana',
    '23': 'Maine', '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
    '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada',
    '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico', '36': 'New York',
    '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio', '40': 'Oklahoma',
    '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island', '45': 'South Carolina',
    '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah', '50': 'Vermont',
    '51': 'Virginia', '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
}
CONTINENTAL_STATES = [str(i).zfill(2) for i in range(1, 57) if i not in [2, 15]]
CACHE_DIR = BASE_DIR / "data" / ".cache"

# Color palettes
PALETTE_DARK = [
    (30, 58, 138),
    (59, 130, 246),
    (34, 211, 238),
    (74, 222, 128),
    (250, 204, 21),
]

PALETTE_LIGHT = [
    (255, 243, 224),
    (255, 204, 128),
    (255, 152, 0),
    (245, 124, 0),
    (230, 81, 0),
]


def get_cache_path(name):
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    return CACHE_DIR / f"{name}.pkl"


def interpolate_color(value, palette):
    n = len(palette) - 1
    idx = value * n
    lower_idx = int(idx)
    upper_idx = min(lower_idx + 1, n)
    t = idx - lower_idx
    return tuple(int(palette[lower_idx][i] * (1-t) + palette[upper_idx][i] * t) for i in range(3))


@st.cache_resource
def load_boundaries():
    cache_path = get_cache_path("boundaries_unified_v1")
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    for fp in [BASE_DIR / "data/puma_boundaries_fast.json", BASE_DIR / "data/puma_boundaries_moderate.gpkg", BASE_DIR / "data/puma_boundaries_optimized.gpkg"]:
        if os.path.exists(fp):
            try:
                gdf = gpd.read_file(fp)
                if gdf.crs != 'EPSG:4326':
                    gdf = gdf.to_crs('EPSG:4326')
                if 'STATEFP10' in gdf.columns:
                    gdf = gdf[gdf['STATEFP10'].isin(CONTINENTAL_STATES)]
                if 'NAMELSAD10' not in gdf.columns and 'clean_puma_name' in gdf.columns:
                    gdf['NAMELSAD10'] = gdf['clean_puma_name']
                gdf['geometry'] = gdf['geometry'].simplify(0.001, preserve_topology=True)
                with open(cache_path, 'wb') as f:
                    pickle.dump(gdf, f, protocol=pickle.HIGHEST_PROTOCOL)
                return gdf
            except:
                continue
    return None


@st.cache_data
def load_census_data(year):
    for path in [BASE_DIR / f"data/census_puma_data_{year}.parquet", BASE_DIR / f"data/census_puma_data_{year}.csv"]:
        if path.exists():
            return pl.read_parquet(path) if str(path).endswith('.parquet') else pl.read_csv(path)
    main_csv = BASE_DIR / "data/census_puma_data.csv"
    if main_csv.exists():
        df = pl.read_csv(main_csv)
        return df.with_columns(pl.lit(year).alias('year')) if 'year' not in df.columns else df
    return None


@st.cache_data
def prepare_map_data(_boundaries, census_df, data_column, palette, _cache_key):
    if _boundaries is None or census_df is None:
        return None
    census_pd = census_df.to_pandas()
    map_data = _boundaries.merge(census_pd, left_on='PUMA_FULL_INT', right_on='puma_full_id', how='left')
    map_data[data_column] = map_data[data_column].fillna(0)
    map_data = map_data[map_data[data_column] > 0].copy()
    if len(map_data) == 0:
        return None
    if 'state_name' not in map_data.columns:
        map_data['state_name'] = map_data['STATEFP10'].map(STATE_NAMES).fillna('Unknown')
    if 'clean_puma_name' not in map_data.columns:
        if 'NAMELSAD10' in map_data.columns:
            map_data['clean_puma_name'] = map_data['NAMELSAD10'].str.replace(r'--PUMA \d+', '', regex=True).str.strip()
        else:
            map_data['clean_puma_name'] = 'PUMA ' + map_data['PUMA_FULL_INT'].astype(str)
    map_data['formatted_value'] = map_data[data_column].apply(lambda x: f"${x:,.0f}")
    min_val, max_val = map_data[data_column].min(), map_data[data_column].max()
    norm = (map_data[data_column] - min_val) / (max_val - min_val)
    colors = [interpolate_color(v, palette) for v in norm]
    map_data['red'] = [c[0] for c in colors]
    map_data['green'] = [c[1] for c in colors]
    map_data['blue'] = [c[2] for c in colors]
    map_data['alpha'] = 200
    return map_data


def create_map(map_data, data_column, is_dark):
    if map_data is None:
        return None
    
    metric_label = "Median Household Income" if 'income' in data_column else "Median Earnings"
    
    if is_dark:
        line_color = [255, 255, 255, 60]
        highlight_color = [255, 255, 255, 80]
        tooltip_bg = "rgba(15, 23, 42, 0.95)"
        tooltip_border = "1px solid rgba(148, 163, 184, 0.15)"
        state_color = "#94a3b8"
        name_color = "#f8fafc"
        value_color = "#38bdf8"
        map_style = "mapbox://styles/mapbox/dark-v11"
    else:
        line_color = [100, 116, 139, 120]
        highlight_color = [255, 255, 255, 150]
        tooltip_bg = "rgba(255, 255, 255, 0.97)"
        tooltip_border = "1px solid rgba(148, 163, 184, 0.2)"
        state_color = "#64748b"
        name_color = "#0f172a"
        value_color = "#ea580c"
        map_style = "mapbox://styles/mapbox/light-v11"
    
    layer = pdk.Layer(
        "GeoJsonLayer",
        map_data,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color="[red, green, blue, alpha]",
        get_line_color=line_color,
        line_width_min_pixels=0.3,
        auto_highlight=True,
        highlight_color=highlight_color,
    )
    
    view = pdk.ViewState(latitude=39.5, longitude=-98.5, zoom=4.2, pitch=0, bearing=0, min_zoom=3, max_zoom=10)
    
    tooltip_html = """<div style="font-family: Inter, sans-serif;">
        <div style="font-size: 10px; color: STATE_COLOR; text-transform: uppercase; margin-bottom: 4px;">{state_name}</div>
        <div style="font-size: 14px; font-weight: 600; color: NAME_COLOR; margin-bottom: 10px;">{clean_puma_name}</div>
        <div style="font-family: JetBrains Mono, monospace; font-size: 24px; font-weight: 600; color: VALUE_COLOR;">{formatted_value}</div>
        <div style="font-size: 10px; color: STATE_COLOR; margin-top: 4px;">METRIC_LABEL</div>
    </div>""".replace("STATE_COLOR", state_color).replace("NAME_COLOR", name_color).replace("VALUE_COLOR", value_color).replace("METRIC_LABEL", metric_label)
    
    tooltip = {
        "html": tooltip_html,
        "style": {
            "backgroundColor": tooltip_bg,
            "backdropFilter": "blur(20px)",
            "borderRadius": "12px",
            "padding": "16px 20px",
            "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.3)",
            "border": tooltip_border
        }
    }
    
    return pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip, map_style=map_style)


def create_histogram(map_data, data_column, is_dark):
    if map_data is None or len(map_data) == 0:
        return None
    
    px, go = get_plotly()
    color = '#38bdf8' if is_dark else '#ea580c'
    text_color = '#94a3b8' if is_dark else '#475569'
    grid_color = 'rgba(148, 163, 184, 0.1)' if is_dark else 'rgba(148, 163, 184, 0.2)'
    
    fig = px.histogram(map_data, x=data_column, nbins=30, color_discrete_sequence=[color])
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color=text_color, size=10),
        xaxis=dict(gridcolor=grid_color, tickformat='$,.0f', title=None, tickfont=dict(size=9, color='#64748b'), showgrid=False),
        yaxis=dict(gridcolor=grid_color, title=None, tickfont=dict(size=9, color='#64748b'), showgrid=True),
        margin=dict(l=0, r=0, t=5, b=25), height=150, bargap=0.1, showlegend=False
    )
    fig.update_traces(marker=dict(line=dict(width=0), opacity=0.85))
    return fig


def create_bars(map_data, data_column, is_dark):
    if map_data is None or len(map_data) == 0:
        return None
    
    state_avg = map_data.groupby('state_name')[data_column].mean().sort_values(ascending=True).tail(10)
    
    px, go = get_plotly()
    if is_dark:
        colors = [f'rgba(56, 189, 248, {0.4 + 0.06 * i})' for i in range(len(state_avg))]
        text_color = "#94a3b8"
    else:
        colors = [f'rgba(234, 88, 12, {0.4 + 0.06 * i})' for i in range(len(state_avg))]
        text_color = "#475569"
    
    fig = go.Figure(go.Bar(
        x=state_avg.values, y=state_avg.index, orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"${v:,.0f}" for v in state_avg.values], textposition='outside',
        textfont=dict(size=9, color=text_color, family="JetBrains Mono"),
    ))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color=text_color, size=10),
        xaxis=dict(tickformat='$,.0f', title=None, showticklabels=False, showgrid=False),
        yaxis=dict(title=None, tickfont=dict(size=10, color=text_color)),
        margin=dict(l=0, r=50, t=5, b=5), height=240,
    )
    return fig


def main():
    is_dark = st.session_state.theme == 'dark'
    palette = PALETTE_DARK if is_dark else PALETTE_LIGHT
    
    # Theme colors for inline styles
    accent = '#38bdf8' if is_dark else '#ea580c'
    accent_bg = 'rgba(56, 189, 248, 0.1)' if is_dark else 'rgba(234, 88, 12, 0.1)'
    accent_border = 'rgba(56, 189, 248, 0.3)' if is_dark else 'rgba(234, 88, 12, 0.3)'
    panel_bg = 'rgba(15, 23, 42, 0.85)' if is_dark else 'rgba(255, 255, 255, 0.92)'
    panel_border = 'rgba(148, 163, 184, 0.15)' if is_dark else 'rgba(148, 163, 184, 0.25)'
    text_legend = '#94a3b8' if is_dark else '#475569'
    
    theme_label = "Light" if is_dark else "Dark"
    
    # Navigation with theme toggle
    st.markdown(f'''
        <div class="top-nav">
            <div class="nav-brand">
                <span class="nav-title">Economic Data Explorer</span>
                <span class="nav-subtitle">U.S. Census Bureau - American Community Survey</span>
            </div>
            <div class="nav-links">
                <span class="nav-link active">Map</span>
                <span class="nav-link">Analysis</span>
                <span class="nav-link">Download</span>
                <span class="nav-link">About</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    # Find years - use BASE_DIR for proper path resolution
    years = sorted([y for y in [2022, 2021, 2020, 2019, 2018, 2017] 
                   if (BASE_DIR / f"data/census_puma_data_{y}.parquet").exists() or 
                      (BASE_DIR / f"data/census_puma_data_{y}.csv").exists()], reverse=True)
    if not years:
        years = [2020] if (BASE_DIR / "data/census_puma_data.csv").exists() else []
    if not years:
        st.error("No census data files found")
        st.stop()
    
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = years[0]
    if 'selected_metric' not in st.session_state:
        st.session_state.selected_metric = 'median_household_income'
    
    # Layout
    with st.container():
        col_spacer, col_controls = st.columns([0.02, 0.98])
        with col_controls:
            ctrl_col, map_col, stats_col = st.columns([1, 3, 0.8])
            
            with ctrl_col:
                st.markdown('<div style="height: 56px;"></div>', unsafe_allow_html=True)
                
                # Theme toggle button
                if st.button(f"{theme_label} Mode", key="theme_toggle", use_container_width=True):
                    st.session_state.theme = 'light' if is_dark else 'dark'
                    st.rerun()
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-label">Select Year</div>', unsafe_allow_html=True)
                year = st.selectbox("Year", years, index=years.index(st.session_state.selected_year) if st.session_state.selected_year in years else 0, label_visibility="collapsed", key="year_select")
                st.session_state.selected_year = year
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-label">Map Variable</div>', unsafe_allow_html=True)
                metric_options = {"median_household_income": "Household Income", "median_earnings": "Median Earnings"}
                selected_metric = st.radio("Variable", list(metric_options.keys()), format_func=lambda x: metric_options[x], index=list(metric_options.keys()).index(st.session_state.selected_metric), label_visibility="collapsed", key="metric_select")
                st.session_state.selected_metric = selected_metric
                
                st.markdown(f'''
                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid {panel_border};">
                        <div class="panel-label">Data Source</div>
                        <div style="font-size: 11px; color: #64748b; line-height: 1.6;">U.S. Census Bureau<br>American Community Survey<br>5-Year Estimates</div>
                    </div>
                ''', unsafe_allow_html=True)
            
            with map_col:
                boundaries = load_boundaries()
                census = load_census_data(year)
                if boundaries is None:
                    st.error("Could not load boundary data")
                    st.stop()
                if census is None:
                    st.error(f"Could not load census data for {year}")
                    st.stop()
                
                # Cache key includes year, metric, and theme for proper caching
                cache_key = f"{year}_{selected_metric}_{is_dark}"
                map_data = prepare_map_data(boundaries, census, selected_metric, palette, cache_key)
                if map_data is None or len(map_data) == 0:
                    st.error("No data available")
                    st.stop()
                
                deck = create_map(map_data, selected_metric, is_dark)
                if deck:
                    st.pydeck_chart(deck, use_container_width=True, height=650)
                
                # Legend
                min_val = map_data[selected_metric].min()
                max_val = map_data[selected_metric].max()
                gradient_stops = ", ".join([f"rgb{interpolate_color(i/4, palette)}" for i in range(5)])
                
                st.markdown(f'''
                    <div style="background: {panel_bg}; backdrop-filter: blur(20px); border: 1px solid {panel_border}; border-radius: 10px; padding: 12px 16px; margin-top: 12px;">
                        <div style="font-family: Inter, sans-serif; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Value Range - {metric_options[selected_metric]}</div>
                        <div style="height: 6px; border-radius: 3px; background: linear-gradient(to right, {gradient_stops}); margin-bottom: 6px;"></div>
                        <div style="display: flex; justify-content: space-between; font-family: JetBrains Mono, monospace; font-size: 10px; color: {text_legend};">
                            <span>${min_val:,.0f}</span>
                            <span>${(min_val + max_val) / 2:,.0f}</span>
                            <span>${max_val:,.0f}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                tab1, tab2 = st.tabs(["Distribution", "Top States"])
                with tab1:
                    fig = create_histogram(map_data, selected_metric, is_dark)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                with tab2:
                    fig = create_bars(map_data, selected_metric, is_dark)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            with stats_col:
                st.markdown('<div style="height: 56px;"></div>', unsafe_allow_html=True)
                avg_val = map_data[selected_metric].mean()
                max_val = map_data[selected_metric].max()
                min_val = map_data[selected_metric].min()
                count = len(map_data)
                
                st.markdown(f'''
                    <div style="background: {accent_bg}; border: 1px solid {accent_border}; border-radius: 8px; padding: 12px; margin-bottom: 12px; text-align: center;">
                        <div style="font-family: JetBrains Mono, monospace; font-size: 24px; font-weight: 600; color: {accent};">{year}</div>
                        <div style="font-size: 9px; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px;">Data Year</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                st.markdown(f'<div class="stat-card"><div class="stat-label">Regions</div><div class="stat-value">{count:,}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-card"><div class="stat-label">Average</div><div class="stat-value accent">${avg_val:,.0f}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-card"><div class="stat-label">Highest</div><div class="stat-value">${max_val:,.0f}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-card"><div class="stat-label">Lowest</div><div class="stat-value">${min_val:,.0f}</div></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
