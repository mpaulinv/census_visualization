import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')

def create_actual_puma_map():
    """
    Create a real geographic map using the downloaded PUMA boundaries
    """
    print("🗺️ Creating Real PUMA Map with Actual Boundaries")
    print("="*50)
    
    # Load census data
    print("📊 Loading census data...")
    try:
        hincp_df = pd.read_csv("HINCP.csv", skiprows=4)
        wagp_df = pd.read_csv("WAGP.csv", skiprows=4)
    except FileNotFoundError:
        print("❌ Census data files not found. Run main.py first.")
        return
    
    # Extract PUMA codes and data
    hincp_df['PUMA'] = hincp_df.iloc[:, 0].astype(str).str.extract(r'(\d{5})')
    wagp_df['PUMA'] = wagp_df.iloc[:, 0].astype(str).str.extract(r'(\d{5})')
    
    hincp_df['HINCP'] = pd.to_numeric(hincp_df.iloc[:, 1].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)
    wagp_df['WAGP'] = pd.to_numeric(wagp_df.iloc[:, 1].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)
    
    # Merge data
    data = pd.merge(hincp_df[['PUMA', 'HINCP']], wagp_df[['PUMA', 'WAGP']], on='PUMA')
    data['income_wage_ratio'] = data['HINCP'] / (data['WAGP'] + 1)
    data['PUMA_FULL'] = data['PUMA']  # Keep full PUMA code for joining
    
    print(f"✓ Loaded {len(data)} PUMA records")
    
    # Load PUMA boundaries
    print("🗺️ Loading PUMA boundary shapefiles...")
    boundaries_folder = r"C:\\Users\\mario\\OneDrive\\Documents\\map_census\\map_boundaries"
    
    # Find all shapefile folders
    shapefile_folders = glob.glob(os.path.join(boundaries_folder, "tl_2020_*_puma10"))
    
    if not shapefile_folders:
        print("❌ No PUMA boundary folders found. Run download_boundaries.py first.")
        return
    
    print(f"📁 Found {len(shapefile_folders)} state boundary folders")
    
    # Load and combine all PUMA shapefiles
    all_pumas = []
    loaded_states = 0
    
    for folder in shapefile_folders[:10]:  # Start with first 10 states for testing
        try:
            shapefile_path = glob.glob(os.path.join(folder, "*.shp"))[0]
            state_pumas = gpd.read_file(shapefile_path)
            
            # Extract state FIPS from folder name
            state_fips = os.path.basename(folder).split('_')[2]
            state_pumas['STATE_FIPS'] = state_fips
            
            all_pumas.append(state_pumas)
            loaded_states += 1
            
            print(f"✓ Loaded {len(state_pumas)} PUMAs from state {state_fips}")
            
        except Exception as e:
            print(f"❌ Error loading {folder}: {e}")
    
    if not all_pumas:
        print("❌ No PUMA boundaries could be loaded")
        return
    
    # Combine all PUMA boundaries
    print(f"🔗 Combining {loaded_states} states...")
    puma_boundaries = gpd.GeoDataFrame(pd.concat(all_pumas, ignore_index=True))
    
    # Create PUMA ID for joining (state FIPS + PUMA code)
    puma_boundaries['PUMA_FULL'] = puma_boundaries['STATEFP10'] + puma_boundaries['PUMACE10']
    
    print(f"✓ Combined {len(puma_boundaries)} PUMA boundaries")
    
    # Join census data with boundaries
    print("🔗 Joining census data with boundaries...")
    puma_map = puma_boundaries.merge(data, on='PUMA_FULL', how='left')\n    \n    # Fill missing values\n    puma_map['HINCP'] = puma_map['HINCP'].fillna(0)\n    puma_map['WAGP'] = puma_map['WAGP'].fillna(0)\n    puma_map['income_wage_ratio'] = puma_map['income_wage_ratio'].fillna(0)\n    \n    matched_pumas = len(puma_map[puma_map['HINCP'] > 0])\n    print(f\"✓ Matched {matched_pumas} PUMAs with census data\")\n    \n    # Create the actual geographic map\n    print(\"🎨 Creating geographic visualization...\")\n    \n    fig, axes = plt.subplots(2, 2, figsize=(24, 16))\n    fig.suptitle(\"US Census Economic Data - Real PUMA Boundaries\", fontsize=20)\n    \n    # Map 1: Income\n    ax1 = axes[0, 0]\n    puma_map.plot(column='HINCP', cmap='Greens', ax=ax1, legend=True, \n                  legend_kwds={'shrink': 0.6, 'aspect': 20})\n    ax1.set_title('Average Household Income by PUMA', fontsize=14)\n    ax1.axis('off')\n    \n    # Map 2: Wages\n    ax2 = axes[0, 1]\n    puma_map.plot(column='WAGP', cmap='Blues', ax=ax2, legend=True,\n                  legend_kwds={'shrink': 0.6, 'aspect': 20})\n    ax2.set_title('Average Wages by PUMA', fontsize=14)\n    ax2.axis('off')\n    \n    # Map 3: Ratio\n    ax3 = axes[1, 0]\n    puma_map.plot(column='income_wage_ratio', cmap='RdYlBu_r', ax=ax3, legend=True,\n                  legend_kwds={'shrink': 0.6, 'aspect': 20})\n    ax3.set_title('Income/Wage Ratio by PUMA', fontsize=14)\n    ax3.axis('off')\n    \n    # Statistics\n    ax4 = axes[1, 1]\n    ax4.axis('off')\n    \n    stats_text = f\"\"\"\nReal Geographic PUMA Map\n========================\n\nStates Loaded: {loaded_states}\nTotal PUMA Boundaries: {len(puma_boundaries):,}\nMatched with Data: {matched_pumas:,}\nData Coverage: {(matched_pumas/len(puma_boundaries)*100):.1f}%\n\nTop PUMAs by Income:\n{get_top_pumas_text(puma_map, 'HINCP')}\n\nTop PUMAs by Wages:\n{get_top_pumas_text(puma_map, 'WAGP')}\n\nData Source: U.S. Census Bureau, 2020\nBoundaries: TIGER/Line Shapefiles\nGeography: Actual PUMA boundaries\n    \"\"\"\n    \n    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=12,\n             verticalalignment='top', fontfamily='monospace',\n             bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.8))\n    \n    plt.tight_layout()\n    \n    # Save the map\n    output_file = \"real_puma_map.png\"\n    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')\n    print(f\"✓ Saved: {output_file}\")\n    \n    # Create focused state maps\n    create_focused_state_maps(puma_map)\n    \n    plt.show()\n\ndef get_top_pumas_text(data, column):\n    \"\"\"Get text for top 5 PUMAs\"\"\"\n    top_5 = data[data[column] > 0].nlargest(5, column)\n    text = \"\"\n    for _, row in top_5.iterrows():\n        puma_id = row.get('PUMACE10', 'Unknown')\n        state = row.get('STATE_FIPS', 'Unknown')\n        if 'ratio' in column.lower():\n            text += f\"  {state}-{puma_id}: {row[column]:.2f}\\n\"\n        else:\n            text += f\"  {state}-{puma_id}: ${row[column]:,.0f}\\n\"\n    return text.strip()\n\ndef create_focused_state_maps(puma_map):\n    \"\"\"Create focused maps for individual states\"\"\"\n    print(\"📍 Creating focused state maps...\")\n    \n    # Get states with the most data\n    state_counts = puma_map[puma_map['HINCP'] > 0]['STATE_FIPS'].value_counts().head(4)\n    \n    if len(state_counts) == 0:\n        print(\"❌ No states with sufficient data for focused maps\")\n        return\n    \n    fig, axes = plt.subplots(2, 2, figsize=(20, 16))\n    fig.suptitle(\"Focused State Maps - PUMA Economic Data\", fontsize=16)\n    \n    for idx, (state_fips, count) in enumerate(state_counts.items()):\n        if idx >= 4:\n            break\n            \n        ax = axes[idx // 2, idx % 2]\n        \n        # Filter to this state\n        state_data = puma_map[puma_map['STATE_FIPS'] == state_fips]\n        \n        if len(state_data) > 0:\n            # Plot income data for this state\n            state_data.plot(column='HINCP', cmap='Greens', ax=ax, legend=True,\n                          legend_kwds={'shrink': 0.8})\n            ax.set_title(f\"State {state_fips} - Household Income ({len(state_data)} PUMAs)\", fontsize=12)\n            ax.axis('off')\n        else:\n            ax.text(0.5, 0.5, f\"No data for State {state_fips}\", transform=ax.transAxes, \n                   ha='center', va='center')\n            ax.axis('off')\n    \n    plt.tight_layout()\n    \n    output_file = \"focused_state_maps.png\"\n    plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')\n    print(f\"✓ Saved: {output_file}\")\n\nif __name__ == \"__main__\":\n    create_actual_puma_map()
