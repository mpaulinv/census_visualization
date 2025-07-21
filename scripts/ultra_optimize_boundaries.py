import geopandas as gpd
import pandas as pd
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')

def create_ultra_optimized_boundaries(output_file="../data/puma_boundaries_optimized.gpkg"):
    """
    Create an ultra-optimized boundary file for web use
    """
    print("🚀 Creating ULTRA-OPTIMIZED PUMA boundaries for web")
    print("="*55)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load PUMA boundaries from downloaded data
    print("🗺️ Loading PUMA boundaries from local files...")
    boundaries_folder = r"C:\Users\mario\OneDrive\Documents\map_census\map_boundaries"
    
    # Find all shapefile folders
    shapefile_folders = glob.glob(os.path.join(boundaries_folder, "tl_2020_*_puma10"))
    
    if not shapefile_folders:
        print("❌ No PUMA boundary folders found.")
        return None
    
    print(f"📁 Found {len(shapefile_folders)} state boundary folders")
    
    # Load and combine all PUMA shapefiles
    print("🔄 Loading shapefiles...")
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
    original_size = puma_boundaries.memory_usage(deep=True).sum() / 1024**2
    print(f"✓ Combined {len(puma_boundaries)} PUMA boundaries ({original_size:.1f}MB)")
    
    # AGGRESSIVE optimization for web use
    print("⚡ Applying AGGRESSIVE optimization for web...")
    
    # 1. Very aggressive simplification (0.02 degrees ≈ 2km)
    print("   🔧 Aggressive geometry simplification...")
    puma_boundaries['geometry'] = puma_boundaries['geometry'].simplify(tolerance=0.02, preserve_topology=True)
    step1_size = puma_boundaries.memory_usage(deep=True).sum() / 1024**2
    print(f"   📉 Step 1: {original_size:.1f}MB → {step1_size:.1f}MB ({(1-step1_size/original_size)*100:.1f}% reduction)")
    
    # 2. Remove all holes (interior rings)
    print("   🕳️ Removing all interior holes...")
    def remove_holes(geom):
        if geom is None or geom.is_empty:
            return geom
        
        from shapely.geometry import Polygon, MultiPolygon
        
        if hasattr(geom, 'exterior'):  # Single Polygon
            return Polygon(geom.exterior.coords)
        elif hasattr(geom, 'geoms'):  # MultiPolygon
            cleaned = []
            for poly in geom.geoms:
                if poly.area > 1e-5:  # Remove tiny polygons
                    cleaned.append(Polygon(poly.exterior.coords))
            if len(cleaned) == 0:
                return geom  # Return original if all parts removed
            elif len(cleaned) == 1:
                return cleaned[0]
            else:
                return MultiPolygon(cleaned)
        return geom
    
    puma_boundaries['geometry'] = puma_boundaries['geometry'].apply(remove_holes)
    step2_size = puma_boundaries.memory_usage(deep=True).sum() / 1024**2
    print(f"   📉 Step 2: {step1_size:.1f}MB → {step2_size:.1f}MB ({(1-step2_size/step1_size)*100:.1f}% reduction)")
    
    # 3. Keep only essential columns  
    print("   📋 Keeping only essential columns...")
    essential_columns = [
        'STATEFP10',      # State FIPS (string)
        'PUMACE10',       # PUMA code (string)  
        'NAMELSAD10',     # PUMA name
        'geometry'        # Geometry
    ]
    
    puma_boundaries = puma_boundaries[essential_columns]
    
    # 4. Add integer matching fields
    print("   🔢 Adding integer matching fields...")
    puma_boundaries['STATEFP10_INT'] = puma_boundaries['STATEFP10'].astype(int)
    puma_boundaries['PUMACE10_INT'] = puma_boundaries['PUMACE10'].astype(int)
    puma_boundaries['PUMA_FULL_INT'] = (puma_boundaries['STATEFP10'] + puma_boundaries['PUMACE10']).astype(int)
    
    # 5. Ensure WGS84
    print("   🌍 Converting to WGS84...")
    if puma_boundaries.crs != 'EPSG:4326':
        puma_boundaries = puma_boundaries.to_crs('EPSG:4326')
    
    # 6. Round coordinates to 3 decimal places (≈100m precision)
    print("   📏 Reducing coordinate precision to 3 decimal places...")
    def round_coords(geom):
        if geom is None or geom.is_empty:
            return geom
            
        from shapely.ops import transform
        def round_coordinate(x, y, z=None):
            return (round(x, 3), round(y, 3))
        
        return transform(round_coordinate, geom)
    
    puma_boundaries['geometry'] = puma_boundaries['geometry'].apply(round_coords)
    
    final_size = puma_boundaries.memory_usage(deep=True).sum() / 1024**2
    total_reduction = (1 - final_size/original_size) * 100
    
    print(f"🎯 TOTAL OPTIMIZATION: {original_size:.1f}MB → {final_size:.1f}MB ({total_reduction:.1f}% reduction)")
    
    # Save optimized file
    print(f"💾 Saving ultra-optimized boundaries...")
    puma_boundaries.to_file(output_file, driver="GPKG")
    
    # Check actual file size on disk
    file_size_mb = os.path.getsize(output_file) / 1024**2
    print(f"✅ File saved: {file_size_mb:.1f}MB on disk")
    
    # Verify loading
    print("🔍 Verifying file can be loaded...")
    try:
        test_load = gpd.read_file(output_file)
        print(f"✅ Verification successful - {len(test_load)} boundaries loaded")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return None
    
    print(f"\n🎉 ULTRA-OPTIMIZATION COMPLETE!")
    print(f"📱 Web-ready file: {file_size_mb:.1f}MB")
    print(f"⚡ {total_reduction:.1f}% size reduction achieved")
    
    return puma_boundaries

if __name__ == "__main__":
    result = create_ultra_optimized_boundaries()
    if result is not None:
        print(f"\n🚀 SUCCESS! Ultra-optimized boundaries ready for web use!")
    else:
        print(f"\n❌ Optimization failed.")
