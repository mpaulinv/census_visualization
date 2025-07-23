from census import Census
import pandas as pd
import os

def download_census_puma_data(year=2020, output_dir=None):
    """
    Download census data for all PUMAs for a specific year
    
    Args:
        year (int): Census year to download (e.g., 2020, 2019, 2018)
        output_dir (str): Directory to save the output file
    
    Returns:
        pd.DataFrame: Census data for the specified year
    """
    print(f"Downloading Census Data for All PUMAs - Year {year}")
    print("="*50)
    
    # Determine output directory - work from script location
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(os.path.dirname(script_dir), "data")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    API_KEY = "910f75dea9028e117b2d3c64a50078aa5161f965"
    c = Census(API_KEY)
    
    # Variables: Median Household Income & Median Earnings
    variables = {
        'B19013_001E': 'median_household_income',
        'B20017_001E': 'median_earnings'
    }
    
    print(f"🔍 Querying Census API for PUMA data (Year: {year})...")
    
    try:
        # Query nationwide for all PUMAs for specified year
        results = c.acs5.get(
            ['NAME'] + list(variables.keys()),
            {'for': 'public use microdata area:*'},
            year=year
        )
        
        print(f"✓ Retrieved {len(results)} PUMA records for {year}")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Add year column for tracking
        df['year'] = year
        
        # Rename columns
        df.rename(columns=variables, inplace=True)
        
        # Convert to numeric
        df['median_household_income'] = pd.to_numeric(df['median_household_income'], errors='coerce')
        df['median_earnings'] = pd.to_numeric(df['median_earnings'], errors='coerce')
        
        # Create proper PUMA identifiers for matching with boundaries
        df['state_fips'] = df['state'].astype(str).str.zfill(2)  # Ensure 2-digit state code
        df['puma_code'] = df['public use microdata area'].astype(str).str.zfill(5)  # Ensure 5-digit PUMA code
        
        # Create composite PUMA ID (state + puma) for reference
        df['puma_full_id'] = df['state_fips'] + df['puma_code']
        
        print(f"\n📋 Data Structure for {year}:")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        
        print(f"\nSample Data for {year}:")
        print(df[['NAME', 'year', 'state_fips', 'puma_code', 'median_household_income', 'median_earnings']].head(10))
        
        print(f"\n🔍 Data Quality Check for {year}:")
        print(f"Records with household income data: {df['median_household_income'].notna().sum()}")
        print(f"Records with earnings data: {df['median_earnings'].notna().sum()}")
        print(f"Unique states: {df['state_fips'].nunique()}")
        print(f"Total PUMAs: {len(df)}")
        
        # Save to CSV with year in filename
        output_file = os.path.join(output_dir, f"census_puma_data_{year}.csv")
        df.to_csv(output_file, index=False)
        print(f"\n✓ Saved data to: {output_file}")
        
        # Show some examples of the matching fields
        print(f"\n🔗 Matching Fields for Boundary Files ({year}):")
        print("State FIPS codes (first 10):", df['state_fips'].head(10).tolist())
        print("PUMA codes (first 10):", df['puma_code'].head(10).tolist())
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading data for {year}: {e}")
        print("This might be due to:")
        print("  - Internet connection issues")
        print("  - Census API rate limits")
        print("  - Invalid API key")
        print(f"  - Year {year} not available in ACS 5-year estimates")
        return None

def download_multiple_years(years=[2020, 2019, 2018], output_dir=None):
    """
    Download census data for multiple years
    
    Args:
        years (list): List of years to download
        output_dir (str): Directory to save output files
    
    Returns:
        dict: Dictionary with year as key and DataFrame as value
    """
    print(f"Downloading Census Data for Multiple Years: {years}")
    print("="*60)
    
    # Determine output directory if not provided
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(os.path.dirname(script_dir), "data")
    
    all_data = {}
    successful_downloads = []
    failed_downloads = []
    
    for year in years:
        print(f"\n🎯 Processing year {year}...")
        data = download_census_puma_data(year=year, output_dir=output_dir)
        
        if data is not None:
            all_data[year] = data
            successful_downloads.append(year)
            print(f"✅ Successfully downloaded {year}")
        else:
            failed_downloads.append(year)
            print(f"❌ Failed to download {year}")
    
    print(f"\n📈 Download Summary:")
    print(f"✅ Successful: {successful_downloads}")
    if failed_downloads:
        print(f"❌ Failed: {failed_downloads}")
    
    return all_data

if __name__ == "__main__":
    # Download data for multiple years (2017-2022)
    years_to_download = [2022, 2021, 2020, 2019, 2018, 2017]
    
    print("🚀 Starting comprehensive multi-year census data download...")
    print(f"📅 Target years: {years_to_download}")
    
    all_data = download_multiple_years(years=years_to_download)
    
    if all_data:
        print(f"\n🎉 Successfully downloaded census data for {len(all_data)} years!")
        for year, data in all_data.items():
            print(f"  📁 Year {year}: {len(data)} PUMAs saved to data/census_puma_data_{year}.csv")
        print("\n� Data Summary:")
        print(f"   - Years available: {sorted(all_data.keys())}")
        print(f"   - Total datasets: {len(all_data)}")
        print(f"   - PUMA coverage: ~{len(next(iter(all_data.values())))} areas per year")
        print("\n�🗺️ Ready to build multi-year interactive map!")
    else:
        print("\n❌ No census data was successfully downloaded.")
        print("💡 Try checking your internet connection and Census API status.")
