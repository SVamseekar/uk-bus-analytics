# Data Directory Cleanup Plan

## Current Directory Structure Analysis

Based on the active pipeline scripts analysis, here's what is actually being used:

### ✅ CURRENTLY USED BY PIPELINE

#### Raw Data (data/raw/)
1. **data/raw/regions/** - ✅ Used by processing pipeline (299 MB, 95 files)
   - Referenced in: `02_data_processing.py`
   - Contains regional BODS TransXchange data

2. **data/raw/naptan/** - ✅ Used by processing pipeline (96 MB)
   - Referenced in: `02_data_processing.py`
   - Contains Stops.csv (NaPTAN data)

3. **data/raw/boundaries/** - ✅ Used by processing pipeline (896 MB)
   - Referenced in: `02_data_processing.py`
   - Contains LSOA boundaries, postcode lookups

4. **data/raw/demographics/** - ✅ Likely used for demographic data (558 MB)
   - Contains census and socioeconomic data

#### Processed Data (data/processed/)
1. **data/processed/regions/** - ✅ Used by validation (8 MB, 18 files)
   - Contains processed routes and stops for 9 regions
   - Referenced in: `03_data_validation.py`

2. **data/processed/outputs/** - ✅ Used for reports
   - Contains validation reports, processing summaries

### ❌ DUPLICATES & UNUSED DIRECTORIES

#### Raw Data (data/raw/)
1. **data/raw/transport/** - ❌ DUPLICATE OF regions/ (431 MB, 114 files)
   - Same TransXchange data as regions/
   - NOT referenced in any pipeline script
   - **RECOMMENDATION: DELETE - Saves 431 MB**

2. **data/raw/bods/** - ❌ EMPTY (0 B)
   - Not used by pipeline
   - **RECOMMENDATION: DELETE**

3. **data/raw/gtfs/** - ❌ EMPTY (0 B)
   - Pipeline uses TransXchange, not GTFS
   - **RECOMMENDATION: DELETE**

4. **data/raw/transxchange/** - ❌ OLD DATA (6.3 MB)
   - Contains only 2 old datasets
   - Superseded by data/raw/regions/
   - **RECOMMENDATION: DELETE - Saves 6.3 MB**

5. **data/raw/reports/** - ❌ EMPTY (4 KB)
   - Not used by pipeline
   - **RECOMMENDATION: DELETE**

#### Processed Data (data/processed/)
1. **data/processed/transport/** - ❌ EMPTY (0 B)
   - Not used by pipeline
   - **RECOMMENDATION: DELETE**

2. **data/processed/demographics/** - ❌ EMPTY (0 B)
   - Demographics integrated into regions/
   - **RECOMMENDATION: DELETE**

3. **data/processed/integrated/** - ❌ EMPTY (0 B)
   - Not used by current pipeline
   - **RECOMMENDATION: DELETE**

4. **data/processed/reports/** - ❌ EMPTY (0 B)
   - Reports go to outputs/ instead
   - **RECOMMENDATION: DELETE**

#### Root Level Files
1. **data/Stops.csv** - ⚠️ DUPLICATE (96 MB)
   - Duplicate of data/raw/naptan/Stops.csv
   - **RECOMMENDATION: DELETE - Saves 96 MB**

#### Staging Directories
1. **data/staging/temp/** - ⚠️ CHECK IF EMPTY
   - Temporary processing files
   - Should be cleaned periodically

2. **data/staging/validation/** - ⚠️ CHECK IF EMPTY
   - Temporary validation files
   - Should be cleaned periodically

---

## Summary of Savings

| Item | Type | Size | Status |
|------|------|------|--------|
| data/raw/transport/ | Duplicate | 431 MB | DELETE |
| data/raw/transxchange/ | Old data | 6.3 MB | DELETE |
| data/raw/bods/ | Empty | 0 B | DELETE |
| data/raw/gtfs/ | Empty | 0 B | DELETE |
| data/raw/reports/ | Empty | 4 KB | DELETE |
| data/processed/transport/ | Empty | 0 B | DELETE |
| data/processed/demographics/ | Empty | 0 B | DELETE |
| data/processed/integrated/ | Empty | 0 B | DELETE |
| data/processed/reports/ | Empty | 0 B | DELETE |
| data/Stops.csv | Duplicate | 96 MB | DELETE |
| **TOTAL SAVINGS** | | **~533 MB** | |

---

## Pipeline Data Flow (What's Actually Used)

```
INGESTION (01_data_ingestion.py):
  Downloads to → data/raw/transport/{region}/ (NOT USED BY NEXT STEPS!)

PROCESSING (02_data_processing.py):
  Reads from → data/raw/regions/{region}/
  Reads from → data/raw/naptan/
  Reads from → data/raw/boundaries/
  Reads from → data/raw/demographics/
  Writes to → data/processed/regions/{region}/

VALIDATION (03_data_validation.py):
  Reads from → data/processed/regions/{region}/
  Writes to → data_pipeline/processed/ (validation reports)

ANALYTICS (04_descriptive_analytics.py):
  Reads from → data/processed/regions/{region}/
```

---

## ⚠️ CRITICAL ISSUE IDENTIFIED

**The ingestion script downloads to `data/raw/transport/` but processing reads from `data/raw/regions/`!**

This explains why:
1. You have 431 MB in data/raw/transport/ (114 files)
2. You have 299 MB in data/raw/regions/ (95 files)
3. They contain the same type of data (BODS TransXchange files)

**Two possibilities:**
- **Option A**: Manually moving files from transport/ to regions/ after download
- **Option B**: Pipeline scripts are misaligned

---

## Recommended Actions

### Step 1: Verify Current Pipeline Works
```bash
# Confirm these are the files being used
ls -lh data/processed/regions/*/
```

### Step 2: Safe Cleanup (Delete unused/duplicate folders)
```bash
# Delete duplicate transport data
rm -rf data/raw/transport/

# Delete empty/unused directories
rm -rf data/raw/bods/
rm -rf data/raw/gtfs/
rm -rf data/raw/transxchange/
rm -rf data/raw/reports/

rm -rf data/processed/transport/
rm -rf data/processed/demographics/
rm -rf data/processed/integrated/
rm -rf data/processed/reports/

# Delete duplicate Stops.csv
rm data/Stops.csv

# Clean staging if empty
find data/staging -type d -empty -delete
```

### Step 3: Fix Pipeline Alignment
Update `01_data_ingestion.py` to download directly to `data/raw/regions/` instead of `data/raw/transport/`

### Step 4: Update Documentation
Update DIRECTORY_GUIDE.md to reflect the cleaned structure

---

## Final Recommended Directory Structure

```
data/
├── raw/
│   ├── regions/          # TransXchange data by region (USED)
│   ├── naptan/           # NaPTAN stops data (USED)
│   ├── boundaries/       # LSOA boundaries (USED)
│   └── demographics/     # Census/socioeconomic data (USED)
│
├── processed/
│   ├── regions/          # Processed regional data (USED)
│   └── outputs/          # Validation reports (USED)
│
└── staging/              # Temporary processing files (clean periodically)
```

**Much cleaner and aligned with actual usage!**
