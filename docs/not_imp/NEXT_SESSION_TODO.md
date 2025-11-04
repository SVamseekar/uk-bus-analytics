# Next Session: Fix Missing Demographics

## Current Status
- ✅ **5/9 regions processed successfully** (Yorkshire, West Midlands, East Midlands, North East, South West)
- ✅ **Memory management fix applied** (gc.collect() in demographic merges)
- ⚠️ **Pipeline crashed on London** (stopped after committing memory fix)

## Critical Issues to Fix

### 1. Schools Data Not Linked to LSOAs
**Files affected:**
- `data/raw/demographics/schools_2024.csv` (52,068 schools)
- `data/raw/demographics/edubasealldata20251028.csv` (52,068 schools)

**Problem:** These files have school-level data with columns like:
- `URN` (school ID)
- `Postcode`
- `EstablishmentName`
- BUT NO `lsoa_code` column!

**Solution needed:**
1. Geocode schools using postcode → lat/lon
2. Link lat/lon to LSOA using spatial join with `data/raw/boundaries/lsoa_names_codes.csv`
3. Create aggregated LSOA-level school metrics (schools per LSOA, school types, etc.)

**Implementation:**
- Create `utils/school_lsoa_linker.py` to:
  - Read school files
  - Geocode postcodes (use geopy or UK postcode database)
  - Spatial join to LSOAs
  - Aggregate: `schools_per_lsoa.csv` with columns: `lsoa_code`, `total_schools`, `primary_schools`, `secondary_schools`

### 2. imd_scores.csv is Corrupted
**File:** `data/raw/demographics/imd_scores.csv`

**Problem:** First line is `<!DOCTYPE html>` - it's an HTML error page, not CSV data!

**Solution:**
- Delete corrupted file
- Re-download proper IMD scores from official source
- OR use `imd_2019.csv` which is already working (2.7M records)

**Action:** Check if `imd_2019.csv` already contains all needed IMD data. If yes, just delete `imd_scores.csv`.

### 3. Remove Corrupt business_counts Files
**Files to remove:**
- `data/raw/demographics/business_counts_fixed.csv` (5MB corrupt)
- `data/raw/demographics/business_counts_CORRUPT_BACKUP.csv` (5MB corrupt)

**Good file (keep):**
- `data/raw/demographics/business_counts.csv` (264KB, 7,201 LSOAs) ✅

**Action:**
```bash
rm data/raw/demographics/business_counts_fixed.csv
rm data/raw/demographics/business_counts_CORRUPT_BACKUP.csv
```

## Steps for Next Session

### Step 1: Clean up corrupt files (5 min)
```bash
cd ~/Projects/uk_bus_analytics
rm data/raw/demographics/imd_scores.csv
rm data/raw/demographics/business_counts_fixed.csv
rm data/raw/demographics/business_counts_CORRUPT_BACKUP.csv
```

### Step 2: Create school LSOA linker (1 hour)
```python
# Create: utils/school_lsoa_linker.py
# - Read schools_2024.csv
# - Geocode postcodes to lat/lon
# - Spatial join to LSOAs
# - Output: data/processed/schools_by_lsoa.csv
```

### Step 3: Update data pipeline to use school aggregates (30 min)
- Modify `data_pipeline/02_data_processing.py` to load `schools_by_lsoa.csv`
- This file will already have `lsoa_code` column, so it will merge successfully

### Step 4: Restart full pipeline (20-30 min)
```bash
python run_full_pipeline.py
```

Should complete all 9 regions now with:
- Memory management fix ✅
- Schools data properly linked ✅
- All demographics clean ✅

## Why Schools Matter for 57 Questions

Schools are critical for:
- **Accessibility analysis** - distance to schools via bus
- **Socioeconomic equity** - do deprived areas have school access?
- **Service planning** - peak times (school runs)
- **Policy impact** - bus service cuts affecting school access

## Expected Outcome

After fixing:
- **9/9 regions processed** (all 206 zip files)
- **All demographics merged** including schools
- **Ready for Phase 2:** Build analysis scripts for 57 questions

## Files Modified in This Session
- `data_pipeline/02_data_processing.py` - Added gc.collect() memory management
- `run_full_pipeline.py` - Created pipeline runner
- Committed: "Add aggressive memory management with gc.collect()"
