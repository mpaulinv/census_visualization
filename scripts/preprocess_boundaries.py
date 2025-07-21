import geopandas as gpd
import pandas as pd
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')

def load_optimized_boundaries(file_path=None):
    '''Load optimized PUMA boundaries with smart path detection - prioritizing standard optimization for better quality'''
    print('Loading PUMA boundaries...')
    
    # Try standard optimized file first (better quality, acceptable size)
    if file_path is None:
        if os.path.exists('../data/puma_boundaries_combined.gpkg'):
            file_path = '../data/puma_boundaries_combined.gpkg'
        elif os.path.exists('data/puma_boundaries_combined.gpkg'):
            file_path = 'data/puma_boundaries_combined.gpkg'
        else:
            file_path = '../data/puma_boundaries_combined.gpkg'
    
    # Try to load the standard optimized file first
    if os.path.exists(file_path):
        print('Loading standard optimized boundaries...')
        try:
            boundaries = gpd.read_file(file_path)
            file_size = os.path.getsize(file_path) / 1024**2
            print(f'Loaded {len(boundaries)} PUMA boundaries ({file_size:.1f}MB)')
            return boundaries
        except Exception as e:
            print(f'Error loading standard optimized file: {e}')
    
    # Fallback to ultra-optimized file if standard not available
    ultra_optimized_path = '../data/puma_boundaries_optimized.gpkg'
    if os.path.exists(ultra_optimized_path):
        print('Falling back to ULTRA-optimized boundaries...')
        try:
            boundaries = gpd.read_file(ultra_optimized_path)
            file_size = os.path.getsize(ultra_optimized_path) / 1024**2
            print(f'Loaded {len(boundaries)} PUMA boundaries ({file_size:.1f}MB)')
            return boundaries
        except Exception as e:
            print(f'Error loading ultra-optimized file: {e}')
    
    # Final fallback - return None if no files found
    print(f'No boundary files found')
    return None
