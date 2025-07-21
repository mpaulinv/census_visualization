import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')

def create_final_puma_map():
    """
    Create the final PUMA map using census_puma_data.csv and downloaded boundaries
    with proper integer matching that we discovered works
    """
    print("🗺️ Creating Final PUMA Map with Real Boundaries")
    print("="*50)
    
    # Load our properly formatted census data
    print("📊 Loading census data...")
    try:
        census_df = pd.read_csv("census_puma_data.csv")
        print(f"✓ Loaded {len(census_df)} census records")
        print(f"Columns: {list(census_df.columns)}")
        print(f"Sample data: {census_df.head(3)[['state_fips', 'puma_code', 'median_household_income', 'median_earnings']].values}")
    except FileNotFoundError:
        print("❌ Census data file 'census_puma_data.csv' not found.")
        print("Please run download_census_data.py first.")
        return None
    
    # Load PUMA boundaries from our downloaded data
    print("🗺️ Loading PUMA boundaries from local files...")
    boundaries_folder = r"C:\Users\mario\OneDrive\Documents\map_census\map_boundaries"
    
    # Find all shapefile folders
    shapefile_folders = glob.glob(os.path.join(boundaries_folder, "tl_2020_*_puma10"))
    
    if not shapefile_folders:
        print("❌ No PUMA boundary folders found.")
        print("Please run download_boundaries.py first.")
        return None
    
    print(f"📁 Found {len(shapefile_folders)} state boundary folders")
    
    # Load and combine all PUMA shapefiles
    all_pumas = []
    loaded_states = 0
    
    for folder in shapefile_folders:
        try:
            shapefile_path = glob.glob(os.path.join(folder, "*.shp"))[0]
            state_pumas = gpd.read_file(shapefile_path)
            
            all_pumas.append(state_pumas)
            loaded_states += 1
            
            if loaded_states <= 5:
                print(f"✓ Loaded {len(state_pumas)} PUMAs from state {os.path.basename(folder).split('_')[2]}")
            elif loaded_states == 6:
                print("  ... loading remaining states ...")
            
        except Exception as e:
            print(f"❌ Error loading {folder}: {e}")
    
    if not all_pumas:
        print("❌ No PUMA boundaries could be loaded")
        return None
    
    # Combine all PUMA boundaries
    print(f"🔗 Combining {loaded_states} states...")
    puma_boundaries = gpd.GeoDataFrame(pd.concat(all_pumas, ignore_index=True))
    print(f"✓ Combined {len(puma_boundaries)} PUMA boundaries")
    
    # CRITICAL: Apply the integer conversion solution we discovered
    print("🔧 Converting boundary data to integers for proper matching...")
    
    # Convert boundary fields to integers to match census data format
    puma_boundaries['STATEFP10_INT'] = puma_boundaries['STATEFP10'].astype(int)
    puma_boundaries['PUMACE10_INT'] = puma_boundaries['PUMACE10'].astype(int)
    puma_boundaries['PUMA_FULL_INT'] = (puma_boundaries['STATEFP10'] + puma_boundaries['PUMACE10']).astype(int)
    
    print(f"Sample boundary integers: {puma_boundaries[['STATEFP10_INT', 'PUMACE10_INT', 'PUMA_FULL_INT']].head(3).values}")
    print(f"Sample census integers: {census_df[['state_fips', 'puma_code', 'puma_full_id']].head(3).values}")
    
    # Join census data with boundaries using the integer matching that works
    print("🔗 Joining census data with PUMA boundaries...")
    puma_map = puma_boundaries.merge(census_df, 
                                   left_on='PUMA_FULL_INT', 
                                   right_on='puma_full_id', 
                                   how='left')
    
    # Fill missing values and create derived metrics
    puma_map['median_household_income'] = puma_map['median_household_income'].fillna(0)
    puma_map['median_earnings'] = puma_map['median_earnings'].fillna(0)
    puma_map['income_earnings_ratio'] = puma_map['median_household_income'] / (puma_map['median_earnings'] + 1)
    
    matched_pumas = len(puma_map[puma_map['median_household_income'] > 0])
    print(f"✅ SUCCESS! Matched {matched_pumas} PUMAs with census data")
    print(f"  Coverage: {(matched_pumas/len(puma_map)*100):.1f}% of all PUMAs")
    
    # Create the final visualization
    create_final_visualization(puma_map, matched_pumas, loaded_states)
    
    return puma_map

def create_final_visualization(puma_map, matched_pumas, loaded_states):
    """Create the final comprehensive map visualization"""
    print("🎨 Creating final geographic visualization...")
    
    # Filter to continental US for main map (remove Alaska and Hawaii)
    continental_pumas = puma_map[~puma_map['STATEFP10'].isin(['02', '15'])]
    
    # Create comprehensive visualization
    fig, axes = plt.subplots(2, 2, figsize=(24, 18))
    fig.suptitle(f"US Census Economic Data - Complete PUMA Analysis ({loaded_states} states)", fontsize=20, fontweight='bold')
    
    # Map 1: Household Income
    ax1 = axes[0, 0]
    continental_pumas.plot(column='median_household_income', 
                          cmap='Greens', 
                          ax=ax1, 
                          legend=True, 
                          legend_kwds={'shrink': 0.6, 'aspect': 20, 'label': 'Income ($)'},
                          missing_kwds={'color': 'lightgray', 'alpha': 0.3})
    ax1.set_title('Median Household Income by PUMA', fontsize=16, fontweight='bold')
    ax1.axis('off')
    
    # Map 2: Earnings
    ax2 = axes[0, 1]
    continental_pumas.plot(column='median_earnings', 
                          cmap='Blues', 
                          ax=ax2, 
                          legend=True,
                          legend_kwds={'shrink': 0.6, 'aspect': 20, 'label': 'Earnings ($)'},
                          missing_kwds={'color': 'lightgray', 'alpha': 0.3})
    ax2.set_title('Median Earnings by PUMA', fontsize=16, fontweight='bold')
    ax2.axis('off')
    
    # Map 3: Income/Earnings Ratio
    ax3 = axes[1, 0]
    continental_pumas.plot(column='income_earnings_ratio', 
                          cmap='RdYlBu_r', 
                          ax=ax3, 
                          legend=True,
                          legend_kwds={'shrink': 0.6, 'aspect': 20, 'label': 'Ratio'},
                          missing_kwds={'color': 'lightgray', 'alpha': 0.3})
    ax3.set_title('Household Income to Earnings Ratio by PUMA', fontsize=16, fontweight='bold')
    ax3.axis('off')
    
    # Statistics panel
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Generate comprehensive statistics
    data_pumas = puma_map[puma_map['median_household_income'] > 0]
    
    if len(data_pumas) > 0:
        top_income = data_pumas.nlargest(10, 'median_household_income')
        top_earnings = data_pumas.nlargest(10, 'median_earnings')
        
        # State-level aggregation
        state_stats = data_pumas.groupby('STATEFP10').agg({
            'median_household_income': 'mean',
            'median_earnings': 'mean',
            'puma_full_id': 'count'
        }).round(0).astype(int)
        state_stats.columns = ['Avg_Income', 'Avg_Earnings', 'PUMA_Count']
        top_states = state_stats.nlargest(5, 'Avg_Income')
        
        stats_text = f"""COMPREHENSIVE PUMA ECONOMIC ANALYSIS
{'='*45}

COVERAGE STATISTICS:
• States Analyzed: {loaded_states}
• Total PUMAs: {len(puma_map):,}
• PUMAs with Data: {matched_pumas:,}
• Coverage Rate: {(matched_pumas/len(puma_map)*100):.1f}%

NATIONAL STATISTICS:
• Avg Household Income: ${data_pumas['median_household_income'].mean():,.0f}
• Avg Earnings: ${data_pumas['median_earnings'].mean():,.0f}
• Avg Income/Earnings Ratio: {data_pumas['income_earnings_ratio'].mean():.2f}

TOP 5 STATES BY AVERAGE INCOME:"""

        for state_fips, row in top_states.head(5).iterrows():
            state_name = get_state_name(state_fips)
            stats_text += f"\n• {state_name}: ${row['Avg_Income']:,} ({row['PUMA_Count']} PUMAs)"

        stats_text += f"""

TOP 5 PUMAS BY HOUSEHOLD INCOME:"""
        
        for _, row in top_income.head(5).iterrows():
            puma_name = str(row.get('NAMELSAD10', 'Unknown'))[:25]
            state_name = get_state_name(row.get('STATEFP10', 'Unknown'))
            stats_text += f"\n• {state_name}, {puma_name}: ${row['median_household_income']:,.0f}"

        stats_text += f"""

TOP 5 PUMAS BY EARNINGS:"""
        
        for _, row in top_earnings.head(5).iterrows():
            puma_name = str(row.get('NAMELSAD10', 'Unknown'))[:25]
            state_name = get_state_name(row.get('STATEFP10', 'Unknown'))
            stats_text += f"\n• {state_name}, {puma_name}: ${row['median_earnings']:,.0f}"
        
        stats_text += f"""

DATA SOURCES:
• Census Bureau ACS 2020 (via API)
• TIGER/Line Shapefiles 2020
• Geographic Resolution: PUMA Level
• Method: Direct Boundary Integration"""

    else:
        stats_text = """❌ NO DATA MATCHES FOUND
        
Check data integration process:
1. Census data format
2. Boundary file integrity  
3. PUMA code matching logic"""
    
    ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=1', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    # Save the final map
    output_file = "final_puma_economic_map.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved comprehensive map: {output_file}")
    
    # Create Alaska and Hawaii inset if we have data
    create_alaska_hawaii_inset(puma_map)
    
    plt.show()

def create_alaska_hawaii_inset(puma_map):
    """Create separate visualization for Alaska and Hawaii"""
    ak_hi_data = puma_map[puma_map['STATEFP10'].isin(['02', '15'])]
    ak_hi_data = ak_hi_data[ak_hi_data['median_household_income'] > 0]
    
    if len(ak_hi_data) > 0:
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Alaska and Hawaii - PUMA Economic Data", fontsize=16)
        
        alaska_data = ak_hi_data[ak_hi_data['STATEFP10'] == '02']
        hawaii_data = ak_hi_data[ak_hi_data['STATEFP10'] == '15']
        
        if len(alaska_data) > 0:
            alaska_data.plot(column='median_household_income', cmap='Greens', ax=axes[0], legend=True)
            axes[0].set_title(f'Alaska - {len(alaska_data)} PUMAs', fontsize=14)
            axes[0].axis('off')
        else:
            axes[0].text(0.5, 0.5, 'No Alaska Data', ha='center', va='center', transform=axes[0].transAxes)
            axes[0].set_title('Alaska - No Data', fontsize=14)
            axes[0].axis('off')
        
        if len(hawaii_data) > 0:
            hawaii_data.plot(column='median_household_income', cmap='Greens', ax=axes[1], legend=True)
            axes[1].set_title(f'Hawaii - {len(hawaii_data)} PUMAs', fontsize=14)
            axes[1].axis('off')
        else:
            axes[1].text(0.5, 0.5, 'No Hawaii Data', ha='center', va='center', transform=axes[1].transAxes)
            axes[1].set_title('Hawaii - No Data', fontsize=14)
            axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig("alaska_hawaii_puma_map.png", dpi=200, bbox_inches='tight', facecolor='white')
        print("✅ Saved Alaska/Hawaii map: alaska_hawaii_puma_map.png")
        plt.show()

def get_state_name(state_fips):
    """Convert state FIPS to state name"""
    state_names = {
        '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', '06': 'California',
        '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'DC', '12': 'Florida',
        '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho', '17': 'Illinois', '18': 'Indiana',
        '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
        '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota', '28': 'Mississippi',
        '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada', '33': 'New Hampshire',
        '34': 'New Jersey', '35': 'New Mexico', '36': 'New York', '37': 'North Carolina', '38': 'North Dakota',
        '39': 'Ohio', '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
        '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah',
        '50': 'Vermont', '51': 'Virginia', '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
    }
    return state_names.get(str(state_fips), f'State {state_fips}')

if __name__ == "__main__":
    result = create_final_puma_map()
    if result is not None:
        print(f"\n🎉 SUCCESS! Created comprehensive PUMA map with {len(result)} boundaries!")
        print("📍 This map shows real Census Bureau PUMA boundaries with economic data!")
        print("📊 Check the generated PNG files for your visualizations!")
    else:
        print("\n❌ Failed to create PUMA map. Check data files and try again.")
