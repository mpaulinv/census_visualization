import os
import requests
import zipfile
from urllib.parse import urljoin
import time

def create_boundaries_folder():
    """Create the map_boundaries folder if it doesn't exist"""
    folder_path = r"C:\Users\mario\OneDrive\Documents\map_census\map_boundaries"
    os.makedirs(folder_path, exist_ok=True)
    print(f"✓ Created/verified folder: {folder_path}")
    return folder_path

def get_state_fips_codes():
    """Get the FIPS codes for states that have PUMA data"""
    # State FIPS codes (we'll focus on the main states first)
    state_fips = {
        '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', 
        '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
        '11': 'District_of_Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
        '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa', 
        '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
        '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
        '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
        '32': 'Nevada', '33': 'New_Hampshire', '34': 'New_Jersey', '35': 'New_Mexico',
        '36': 'New_York', '37': 'North_Carolina', '38': 'North_Dakota', '39': 'Ohio',
        '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode_Island',
        '45': 'South_Carolina', '46': 'South_Dakota', '47': 'Tennessee', '48': 'Texas',
        '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
        '54': 'West_Virginia', '55': 'Wisconsin', '56': 'Wyoming'
    }
    return state_fips

def download_puma_shapefile(state_fips, state_name, output_folder):
    """Download PUMA shapefile for a specific state"""
    
    # Census TIGER URL pattern
    base_url = "https://www2.census.gov/geo/tiger/TIGER2020/PUMA/"
    filename = f"tl_2020_{state_fips}_puma10.zip"
    url = urljoin(base_url, filename)
    
    output_path = os.path.join(output_folder, filename)
    
    # Skip if already downloaded
    if os.path.exists(output_path):
        print(f"⏭️  Skipping {state_name} ({state_fips}) - already exists")
        return True
    
    try:
        print(f"📥 Downloading {state_name} ({state_fips})...")
        print(f"   URL: {url}")
        
        # Download with timeout and user agent - disable SSL verification
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Disable SSL verification to work around certificate issues
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.get(url, headers=headers, timeout=30, stream=True, verify=False)
        response.raise_for_status()
        
        # Write file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"✓ Downloaded {filename} ({file_size:.1f} MB)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {state_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {state_name}: {e}")
        return False

def extract_shapefiles(output_folder):
    """Extract all downloaded zip files"""
    print("\n📂 Extracting shapefiles...")
    
    zip_files = [f for f in os.listdir(output_folder) if f.endswith('.zip')]
    
    for zip_file in zip_files:
        zip_path = os.path.join(output_folder, zip_file)
        extract_folder = os.path.join(output_folder, zip_file.replace('.zip', ''))
        
        if os.path.exists(extract_folder):
            print(f"⏭️  Skipping extraction of {zip_file} - already extracted")
            continue
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            print(f"✓ Extracted {zip_file}")
        except Exception as e:
            print(f"❌ Failed to extract {zip_file}: {e}")

def main():
    """Main download function"""
    print("🗺️  PUMA Boundaries Downloader")
    print("="*40)
    
    # Create output folder
    output_folder = create_boundaries_folder()
    
    # Get state codes
    state_fips_codes = get_state_fips_codes()
    
    print(f"\n📥 Starting download of {len(state_fips_codes)} states...")
    print("This may take several minutes...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    # Download each state - download all states now that SSL is working
    all_states = list(state_fips_codes.items())  # Download all states
    
    for state_fips, state_name in all_states:
        success = download_puma_shapefile(state_fips, state_name, output_folder)
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Small delay to be respectful to the server
        time.sleep(1)
    
    print(f"\n📊 Download Summary:")
    print(f"✓ Successful: {successful_downloads}")
    print(f"❌ Failed: {failed_downloads}")
    
    if successful_downloads > 0:
        extract_shapefiles(output_folder)
        print(f"\n🎉 Complete! Files saved to: {output_folder}")
        
        # List what we have
        files = os.listdir(output_folder)
        print(f"\nDownloaded files ({len(files)} items):")
        for f in sorted(files):
            print(f"  📁 {f}")
    
    return output_folder

if __name__ == "__main__":
    main()
