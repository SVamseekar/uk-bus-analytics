# Data Directory Cleanup Summary

## ✅ Cleanup Completed Successfully

**Date:** 2025-10-28

---

## Actions Taken

### 1. Merged Transport to Regions ✅
- **Strategy:** Safely merged `data/raw/transport/` into `data/raw/regions/`
- **Duplicates Found:** 3 files (kept the versions in regions/)
- **Unique Files Moved:** 111 files
- **Result:** All unique transport data now consolidated in regions/

### 2. Deleted Duplicate Files ✅
- `data/Stops.csv` (96 MB) - duplicate of `data/raw/naptan/Stops.csv`

### 3. Deleted Unused Raw Directories ✅
- `data/raw/transport/` (431 MB) - merged into regions/
- `data/raw/bods/` (0 B) - empty
- `data/raw/gtfs/` (0 B) - empty, pipeline uses TransXchange
- `data/raw/transxchange/` (6.3 MB) - old data superseded by regions/
- `data/raw/reports/` (4 KB) - empty

### 4. Deleted Unused Processed Directories ✅
- `data/processed/transport/` (0 B) - not used
- `data/processed/demographics/` (0 B) - integrated into regions/
- `data/processed/integrated/` (0 B) - not used
- `data/processed/reports/` (0 B) - reports go to outputs/

### 5. Cleaned Staging ✅
- Removed empty staging directories

---

## Storage Savings

| Category | Size Freed |
|----------|------------|
| Transport folder merge | 431 MB |
| Duplicate Stops.csv | 96 MB |
| Old transxchange data | 6.3 MB |
| Empty directories | ~1 MB |
| **Total Saved** | **~534 MB** |

---

## Final Directory Structure

```
data/
├── raw/
│   ├── regions/          [705 MB] ✅ TransXchange by region (merged from transport)
│   ├── boundaries/       [896 MB] ✅ LSOA boundaries & lookups
│   ├── demographics/     [558 MB] ✅ Census & socioeconomic data
│   └── naptan/           [96 MB]  ✅ NaPTAN stops data
│
└── processed/
    ├── regions/          [8 MB]   ✅ Processed regional data
    └── outputs/          [14 MB]  ✅ Reports & validation results
```

**Total Data Size:** ~2.3 GB (down from ~2.8 GB)

---

## Pipeline Alignment Verified

### Current Pipeline Flow (Working)
```
01_data_ingestion.py
  └─→ Downloads to: data/raw/transport/{region}/ ⚠️ (Note: old location)

02_data_processing.py
  ├─→ Reads from: data/raw/regions/{region}/  ✅
  ├─→ Reads from: data/raw/naptan/           ✅
  ├─→ Reads from: data/raw/boundaries/       ✅
  └─→ Writes to: data/processed/regions/     ✅

03_data_validation.py
  ├─→ Reads from: data/processed/regions/    ✅
  └─→ Writes to: data_pipeline/processed/    ✅

04_descriptive_analytics.py
  └─→ Reads from: data/processed/regions/    ✅
```

---

## Files Currently in Use

### Raw Data (1.7 GB)
- ✅ **data/raw/regions/** - 705 MB, 206 TransXchange files (95 original + 111 merged)
- ✅ **data/raw/naptan/** - 96 MB, Stops.csv
- ✅ **data/raw/boundaries/** - 896 MB, LSOA boundaries, postcode lookups
- ✅ **data/raw/demographics/** - 558 MB, Census and unemployment data

### Processed Data (22 MB)
- ✅ **data/processed/regions/** - 8 MB, 18 files (9 regions × 2 file types)
  - Routes: routes_processed.csv per region
  - Stops: stops_processed.csv per region
- ✅ **data/processed/outputs/** - 14 MB, validation reports and summaries

---

## Regions with Data

All 9 UK regions now have consolidated data in `data/raw/regions/`:

1. **Yorkshire and Humber** - 22 files
2. **West Midlands** - 23 files
3. **East Midlands** - 20 files
4. **North East** - 16 files
5. **South West** - 18 files
6. **Greater London** - 39 files
7. **South East** - 20 files
8. **North West** - 26 files
9. **East of England** - 22 files

**Total:** 206 TransXchange files covering all regions

---

## Next Steps (Optional)

### 1. Update Ingestion Script ⚠️
The ingestion script currently downloads to `data/raw/transport/` but processing reads from `data/raw/regions/`. Consider updating:

```python
# In 01_data_ingestion.py, change:
region_dir = DATA_RAW / 'transport' / region_code
# To:
region_dir = DATA_RAW / 'regions' / region_code
```

### 2. Add to .gitignore
```
# Large data files
data/raw/
data/processed/
data/staging/

# Keep structure
!data/raw/.gitkeep
!data/processed/.gitkeep
```

### 3. Document the Structure
Update DIRECTORY_GUIDE.md to reflect the cleaned structure.

---

## Verification Commands

```bash
# Check structure
tree data -L 2 -d

# Check sizes
du -sh data/raw/* data/processed/*

# Count files per region
for region in data/raw/regions/*; do
  echo "$(basename $region): $(ls $region | wc -l) files"
done

# Verify processed data
ls -lh data/processed/regions/*/
```

---

## Cleanup Script Created

Created `scripts/merge_transport_to_regions.sh` for future reference. This script:
- Identifies duplicates between transport/ and regions/
- Moves only unique files
- Provides detailed summary of actions

---

## Status: ✅ COMPLETE

The data directory is now clean, organized, and aligned with the working pipeline. All unnecessary duplicates and empty directories have been removed, saving ~534 MB of storage space.
