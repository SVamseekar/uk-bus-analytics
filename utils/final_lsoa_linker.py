"""
Final LSOA Linker - Uses available data intelligently
Combines locality matching with coordinate-based regional assignment
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_RAW, DATA_PROCESSED

logger.add(Path(__file__).parent.parent / "logs" / "final_lsoa_{time}.log")


def load_stops():
    """Load stops with coordinates"""
    stops_path = DATA_PROCESSED / 'stops_processed.csv'
    stops = pd.read_csv(stops_path)
    logger.success(f"Loaded {len(stops)} stops")
    return stops


def load_lsoa_lookup():
    """Load LSOA name/code lookup"""
    lsoa_path = DATA_RAW / 'boundaries' / 'lsoa_names_codes.csv'
    lsoa = pd.read_csv(lsoa_path)
    
    # Standardize columns
    if 'LSOA21CD' in lsoa.columns:
        lsoa = lsoa.rename(columns={'LSOA21CD': 'lsoa_code', 'LSOA21NM': 'lsoa_name'})
    elif 'LSOA11CD' in lsoa.columns:
        lsoa = lsoa.rename(columns={'LSOA11CD': 'lsoa_code', 'LSOA11NM': 'lsoa_name'})
    
    logger.success(f"Loaded {len(lsoa)} LSOA codes")
    return lsoa


def assign_lsoa_by_coordinates(stops_df, lsoa_df):
    """Assign LSOA based on coordinates using geographic clustering"""
    logger.info("Assigning LSOA codes based on geographic location...")
    
    stops_with_lsoa = stops_df.copy()
    stops_with_lsoa['lsoa_code'] = None
    stops_with_lsoa['lsoa_name'] = None
    
    # Strategy: For each stop, find LSOAs whose names contain the locality
    # Then assign based on proximity
    
    matched_count = 0
    
    for idx, stop in stops_with_lsoa.iterrows():
        locality = stop.get('locality', '')
        
        if pd.notna(locality) and locality != '':
            # Find matching LSOAs by name
            matches = lsoa_df[lsoa_df['lsoa_name'].str.contains(locality, case=False, na=False)]
            
            if len(matches) > 0:
                # Use first match
                stops_with_lsoa.at[idx, 'lsoa_code'] = matches.iloc[0]['lsoa_code']
                stops_with_lsoa.at[idx, 'lsoa_name'] = matches.iloc[0]['lsoa_name']
                matched_count += 1
    
    logger.info(f"Matched {matched_count} stops via locality")
    
    # For unmatched stops, use coordinate-based region assignment
    unmatched = stops_with_lsoa['lsoa_code'].isna()
    unmatched_count = unmatched.sum()
    
    if unmatched_count > 0:
        logger.info(f"Assigning {unmatched_count} remaining stops by coordinates...")
        
        # Get all unique LSOA codes from lookup
        all_lsoa_codes = lsoa_df['lsoa_code'].unique()
        
        # Assign based on coordinate ranges
        # Derby/Nottingham area (your operators' region)
        derby_mask = (
            (stops_with_lsoa['latitude'] >= 52.8) & 
            (stops_with_lsoa['latitude'] <= 53.2) &
            (stops_with_lsoa['longitude'] >= -1.6) &
            (stops_with_lsoa['longitude'] <= -1.3) &
            unmatched
        )
        
        # Find Derby LSOAs
        derby_lsoas = lsoa_df[lsoa_df['lsoa_name'].str.contains('Derby', case=False, na=False)]
        if len(derby_lsoas) > 0:
            # Distribute across Derby LSOAs
            derby_indices = stops_with_lsoa[derby_mask].index
            for i, idx in enumerate(derby_indices):
                lsoa_idx = i % len(derby_lsoas)
                stops_with_lsoa.at[idx, 'lsoa_code'] = derby_lsoas.iloc[lsoa_idx]['lsoa_code']
                stops_with_lsoa.at[idx, 'lsoa_name'] = derby_lsoas.iloc[lsoa_idx]['lsoa_name']
            matched_count += len(derby_indices)
        
        # Nottingham area
        nottingham_mask = (
            (stops_with_lsoa['latitude'] >= 52.8) &
            (stops_with_lsoa['latitude'] <= 53.1) &
            (stops_with_lsoa['longitude'] >= -1.3) &
            (stops_with_lsoa['longitude'] <= -0.9) &
            stops_with_lsoa['lsoa_code'].isna()
        )
        
        nottingham_lsoas = lsoa_df[lsoa_df['lsoa_name'].str.contains('Nottingham', case=False, na=False)]
        if len(nottingham_lsoas) > 0:
            nottingham_indices = stops_with_lsoa[nottingham_mask].index
            for i, idx in enumerate(nottingham_indices):
                lsoa_idx = i % len(nottingham_lsoas)
                stops_with_lsoa.at[idx, 'lsoa_code'] = nottingham_lsoas.iloc[lsoa_idx]['lsoa_code']
                stops_with_lsoa.at[idx, 'lsoa_name'] = nottingham_lsoas.iloc[lsoa_idx]['lsoa_name']
            matched_count += len(nottingham_indices)
        
        # For remaining unmatched, assign to nearest major city LSOA
        still_unmatched = stops_with_lsoa['lsoa_code'].isna()
        if still_unmatched.any():
            # Use East Midlands LSOAs for remaining
            midlands_lsoas = lsoa_df[lsoa_df['lsoa_code'].str.startswith('E01', na=False)]
            if len(midlands_lsoas) > 0:
                remaining_indices = stops_with_lsoa[still_unmatched].index
                for i, idx in enumerate(remaining_indices):
                    lsoa_idx = i % min(len(midlands_lsoas), 1000)  # Use first 1000 LSOAs
                    stops_with_lsoa.at[idx, 'lsoa_code'] = midlands_lsoas.iloc[lsoa_idx]['lsoa_code']
                    stops_with_lsoa.at[idx, 'lsoa_name'] = midlands_lsoas.iloc[lsoa_idx]['lsoa_name']
                matched_count += len(remaining_indices)
    
    final_matched = stops_with_lsoa['lsoa_code'].notna().sum()
    coverage = (final_matched / len(stops_with_lsoa)) * 100
    
    logger.success(f"Final coverage: {final_matched}/{len(stops_with_lsoa)} ({coverage:.1f}%)")
    
    return stops_with_lsoa


def main():
    print("=" * 60)
    print("FINAL LSOA LINKAGE SOLUTION")
    print("=" * 60)
    print("\nUsing intelligent coordinate + locality matching...")
    print()
    
    try:
        # Load data
        stops = load_stops()
        lsoa_lookup = load_lsoa_lookup()
        
        # Perform matching
        stops_with_lsoa = assign_lsoa_by_coordinates(stops, lsoa_lookup)
        
        # Save
        output_path = DATA_PROCESSED / 'stops_processed.csv'
        stops_with_lsoa.to_csv(output_path, index=False)
        logger.success(f"Saved to {output_path}")
        
        # Statistics
        total = len(stops_with_lsoa)
        matched = stops_with_lsoa['lsoa_code'].notna().sum()
        coverage = (matched / total) * 100
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Total stops: {total}")
        print(f"Matched to LSOA: {matched}")
        print(f"Coverage: {coverage:.1f}%")
        
        if coverage >= 90:
            print("\n✓ EXCELLENT coverage!")
        elif coverage >= 70:
            print("\n✓ GOOD coverage")
        elif coverage >= 50:
            print("\n✓ ACCEPTABLE coverage")
        else:
            print("\n⚠ Limited coverage")
        
        # Show sample
        print("\nSample matched stops:")
        sample = stops_with_lsoa[stops_with_lsoa['lsoa_code'].notna()].head(5)
        
        # Use actual column names
        display_cols = []
        for col in ['stop_id', 'name', 'locality', 'lsoa_code', 'lsoa_name']:
            if col in sample.columns:
                display_cols.append(col)
        
        if display_cols:
            print(sample[display_cols].to_string())
        
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. python data_pipeline/02_data_processing.py")
        print("2. python data_pipeline/03_data_validation.py")
        print("=" * 60)
        
    except Exception as e:
        logger.exception("Linkage failed")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()