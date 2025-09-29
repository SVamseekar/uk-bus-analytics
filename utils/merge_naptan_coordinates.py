"""
Merge extracted TransXchange stops with NaPTAN coordinate data
NaPTAN is the UK's authoritative national stop database
"""
import sys
import pandas as pd
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_RAW, DATA_PROCESSED


def load_naptan_data():
    """Load NaPTAN stops database"""
    naptan_path = DATA_RAW / 'naptan' / 'Stops.csv'
    
    if not naptan_path.exists():
        logger.error(f"NaPTAN file not found: {naptan_path}")
        logger.info("\nTo download NaPTAN data:")
        logger.info("1. Visit: https://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx")
        logger.info("2. Select 'CSV' format")
        logger.info("3. Download 'Stops' data")
        logger.info(f"4. Save to: {naptan_path}")
        return None
    
    logger.info(f"Loading NaPTAN data from {naptan_path}")
    
    try:
        # NaPTAN files can be large, load with specific columns
        usecols = ['ATCOCode', 'CommonName', 'Latitude', 'Longitude', 
                   'LocalityName', 'Status']
        
        df = pd.read_csv(naptan_path, usecols=usecols, low_memory=False)
        
        # Only keep active stops
        if 'Status' in df.columns:
            df = df[df['Status'] == 'active']
        
        logger.success(f"Loaded {len(df)} active NaPTAN stops")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load NaPTAN data: {e}")
        return None


def merge_with_transxchange_stops(naptan_df):
    """Merge NaPTAN coordinates with TransXchange stop IDs"""
    
    # Load extracted stops
    tx_stops_path = DATA_PROCESSED / 'stops_extracted.csv'
    
    if not tx_stops_path.exists():
        logger.error(f"TransXchange stops not found: {tx_stops_path}")
        logger.info("Run: python utils/transxchange_stop_extractor.py first")
        return None
    
    logger.info(f"Loading TransXchange stops from {tx_stops_path}")
    tx_stops = pd.read_csv(tx_stops_path)
    
    logger.info(f"TransXchange stops: {len(tx_stops)}")
    logger.info(f"  With coordinates: {tx_stops['has_coordinates'].sum()}")
    logger.info(f"  Without coordinates: {(~tx_stops['has_coordinates']).sum()}")
    
    # Prepare NaPTAN data for merging
    naptan_df = naptan_df.rename(columns={
        'ATCOCode': 'stop_id',
        'CommonName': 'naptan_name',
        'Latitude': 'naptan_lat',
        'Longitude': 'naptan_lon',
        'LocalityName': 'locality'
    })
    
    # Merge with NaPTAN
    logger.info("Merging with NaPTAN coordinates...")
    merged = tx_stops.merge(
        naptan_df[['stop_id', 'naptan_name', 'naptan_lat', 'naptan_lon', 'locality']],
        on='stop_id',
        how='left'
    )
    
    # Use NaPTAN coordinates where TransXchange doesn't have them
    merged['latitude'] = merged.apply(
        lambda row: row['latitude'] if pd.notna(row['latitude']) else row['naptan_lat'],
        axis=1
    )
    merged['longitude'] = merged.apply(
        lambda row: row['longitude'] if pd.notna(row['longitude']) else row['naptan_lon'],
        axis=1
    )
    
    # Use NaPTAN name if TransXchange name is missing
    merged['stop_name'] = merged.apply(
        lambda row: row['stop_name'] if pd.notna(row['stop_name']) else row['naptan_name'],
        axis=1
    )
    
    # Update has_coordinates flag
    merged['has_coordinates'] = merged['latitude'].notna() & merged['longitude'].notna()
    
    # Drop temporary NaPTAN columns
    merged = merged.drop(columns=['naptan_name', 'naptan_lat', 'naptan_lon'], errors='ignore')
    
    # Statistics
    total_stops = len(merged)
    with_coords = merged['has_coordinates'].sum()
    matched_from_naptan = (merged['latitude'].notna() & tx_stops['has_coordinates'] == False).sum()
    
    logger.success(f"Merge complete!")
    logger.info(f"Total stops: {total_stops}")
    logger.info(f"With coordinates: {with_coords} ({with_coords/total_stops*100:.1f}%)")
    logger.info(f"Matched from NaPTAN: {matched_from_naptan}")
    
    # Save enriched stops
    output_path = DATA_PROCESSED / 'stops_processed.csv'
    merged.to_csv(output_path, index=False)
    logger.success(f"Saved enriched stops to: {output_path}")
    
    return merged


def main():
    """Run NaPTAN merge"""
    print("="*60)
    print("NAPTAN COORDINATE MERGER")
    print("="*60)
    print("\nMerging TransXchange stops with NaPTAN coordinates...\n")
    
    # Load NaPTAN
    naptan_df = load_naptan_data()
    
    if naptan_df is None:
        print("\n❌ Cannot proceed without NaPTAN data")
        print("\nPlease download NaPTAN first:")
        print("  https://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx")
        return
    
    # Merge with TransXchange stops
    merged_df = merge_with_transxchange_stops(naptan_df)
    
    if merged_df is not None:
        print("\n" + "="*60)
        print("MERGE RESULTS")
        print("="*60)
        print(f"\nTotal stops: {len(merged_df)}")
        print(f"With coordinates: {merged_df['has_coordinates'].sum()}")
        print(f"Coverage: {merged_df['has_coordinates'].sum()/len(merged_df)*100:.1f}%")
        
        print("\nSample enriched stops:")
        print(merged_df[merged_df['has_coordinates']].head(10)[
            ['stop_id', 'stop_name', 'latitude', 'longitude', 'locality']
        ])
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Stops enriched with NaPTAN coordinates")
        print("\nNext steps:")
        print("1. Re-run: python data_pipeline/02_data_processing.py")
        print("2. Then run: python data_pipeline/03_data_validation.py")
        print("="*60)
    else:
        print("\n❌ Merge failed")


if __name__ == "__main__":
    main()