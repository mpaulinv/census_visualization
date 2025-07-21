#!/usr/bin/env python3
"""
Moderate Optimization of PUMA Boundaries
Creates a balanced file that's much smaller than 107MB but with better quality than ultra-optimized
Target: 5-15MB with good visual quality
"""

import geopandas as gpd
import pandas as pd
import os
import glob
from pathlib import Path

def moderate_optimize_boundaries():
    """Create moderately optimized boundary files - balanced quality and size"""
    
    print("🔧 Starting MODERATE optimization of PUMA boundaries...")
    print("📊 Target: 5-15MB with good visual quality")
    
    # Check for combined boundaries first
    input_file = "../data/puma_boundaries_combined.gpkg"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("💡 Please run preprocess_boundaries.py first to create combined file")
        return
    
    # Load the combined boundaries
    print(f"📥 Loading boundaries from {input_file}...")
    try:
        boundaries = gpd.read_file(input_file)
        original_size = os.path.getsize(input_file) / 1024**2
        print(f"✅ Loaded {len(boundaries)} PUMA boundaries ({original_size:.1f}MB)")
    except Exception as e:
        print(f"❌ Error loading boundaries: {e}")
        return
    
    print(f"📊 Original data info:")
    print(f"   - Number of PUMAs: {len(boundaries):,}")
    print(f"   - File size: {original_size:.1f}MB")
    print(f"   - CRS: {boundaries.crs}")
    
    # Step 1: Moderate simplification (0.005° ≈ 555m tolerance)
    print("🔄 Step 1: Applying moderate simplification...")
    tolerance = 0.005  # Moderate simplification - good balance
    boundaries['geometry'] = boundaries['geometry'].simplify(
        tolerance=tolerance, preserve_topology=True
    )
    print(f"   ✅ Applied {tolerance}° simplification")
    
    # Step 2: Remove small holes (more conservative than ultra-optimization)
    print("🔄 Step 2: Removing small holes...")
    hole_threshold = 0.001  # Remove smaller holes than ultra-optimization
    
    def remove_small_holes(geom):
        if hasattr(geom, 'interiors') and geom.interiors:
            # Keep larger holes, remove only very small ones
            large_holes = [hole for hole in geom.interiors 
                          if hole.is_ring and abs(gpd.GeoSeries([hole]).area.iloc[0]) > hole_threshold]
            if large_holes != list(geom.interiors):
                from shapely.geometry import Polygon
                return Polygon(geom.exterior.coords, holes=[hole.coords for hole in large_holes])
        return geom
    
    boundaries['geometry'] = boundaries['geometry'].apply(remove_small_holes)
    print(f"   ✅ Removed holes smaller than {hole_threshold}°²")
    
    # Step 3: Moderate coordinate precision (keep more precision than ultra)
    print("🔄 Step 3: Optimizing coordinate precision...")
    precision = 5  # 5 decimal places ≈ 1.1m precision (vs 4 for ultra-optimization)
    
    def round_coordinates(geom):
        from shapely.ops import transform
        def round_coords(x, y, z=None):
            return (round(x, precision), round(y, precision))
        return transform(round_coords, geom)
    
    boundaries['geometry'] = boundaries['geometry'].apply(round_coordinates)
    print(f"   ✅ Rounded coordinates to {precision} decimal places")
    
    # Step 4: Optimize data types but keep important columns
    print("🔄 Step 4: Optimizing data types...")
    
    # Keep essential columns for mapping
    essential_columns = [
        'STATEFP10', 'PUMA_FULL_INT', 'NAMELSAD10', 'geometry'
    ]
    
    # Add any other columns that exist and might be useful
    available_columns = boundaries.columns.tolist()
    for col in ['GEOID10', 'INTPTLAT10', 'INTPTLON10']:
        if col in available_columns:
            essential_columns.append(col)
    
    # Filter to essential columns
    boundaries = boundaries[essential_columns]
    
    # Optimize string columns
    for col in boundaries.select_dtypes(include=['object']).columns:
        if col != 'geometry':
            boundaries[col] = boundaries[col].astype('category')
    
    print(f"   ✅ Optimized to {len(boundaries.columns)} essential columns")
    
    # Save the moderately optimized file
    output_file = "../data/puma_boundaries_moderate.gpkg"
    print(f"💾 Saving moderate optimization to {output_file}...")
    
    try:
        boundaries.to_file(output_file, driver='GPKG')
        new_size = os.path.getsize(output_file) / 1024**2
        reduction = ((original_size - new_size) / original_size) * 100
        
        print(f"✅ MODERATE optimization complete!")
        print(f"📊 Results:")
        print(f"   - Original size: {original_size:.1f}MB")
        print(f"   - Moderate size: {new_size:.1f}MB")
        print(f"   - Reduction: {reduction:.1f}%")
        print(f"   - Quality: High (balanced)")
        print(f"   - Precision: {precision} decimal places")
        print(f"   - Simplification: {tolerance}° tolerance")
        
        if new_size < 20:
            print(f"🎯 Perfect! File size under 20MB with good quality")
        else:
            print(f"⚠️  File size is {new_size:.1f}MB - consider if acceptable")
            
    except Exception as e:
        print(f"❌ Error saving optimized boundaries: {e}")

if __name__ == "__main__":
    moderate_optimize_boundaries()
