# Critical Data Pipeline Bugs - Analysis Summary

## Date: 2025-10-31

## Executive Summary
Comprehensive analysis revealed 6 critical bugs causing data quality issues:
- **Actual stops**: ~30,000-60,000 expected vs 16,865-35,021 reported (inflated duplicates + missing data)
- **Actual routes**: ~2,000-5,000 expected vs 335 reported (wrong uniqueness key)
- **Demographics**: 0% merged (except schools at 50%)

---

## Bug #1: Parser 10-File XML Limit 🔴 CRITICAL

**File**: `utils/gtfs_parser.py:122`

**Issue**:
```python
for xml_file in xml_files[:10]:  # ← Processes ONLY 10 files
```

**Impact**:
- First_Bus has 47 XML files → only 10 processed = **79% data loss**
- Phoenix has 12 files → only 10 processed = **17% data loss**
- Missing ~40-50% of all stops and routes

**Expected stops (from web research)**:
- West Yorkshire alone: 14,000+ stops
- South West: 13,227 stops
- West Midlands: 12,784 stops
- **Total 5 regions: ~60,000 stops**

**Current count**: 35,021 (58% of expected)

**Fix**:
```python
for xml_file in xml_files:  # Process ALL files
```

---

## Bug #2: Cross-Region Operator Duplication 🔴 CRITICAL

**File**: `data_pipeline/01_data_ingestion.py` (download logic)

**Issue**:
- Same operator file (e.g., `Phoenix_Taxis_1738.zip`) downloaded in ALL 5 regions
- Each region processes the same stops independently
- Stop "3100U029022" (Newcastle) appears in 5 region folders

**Impact**:
```
Same physical stop appears 5 times:
├── east_midlands/stops_processed.csv (with wrong LSOA E01013894)
├── north_east/stops_processed.csv (with wrong LSOA E01008288)
├── south_west/stops_processed.csv (with wrong LSOA E01014493)
├── west_midlands/stops_processed.csv (with wrong LSOA E01008881)
└── yorkshire/stops_processed.csv (with wrong LSOA E01011264)

Actual location: Newcastle (55.31°N, -1.96°W)
Only ONE LSOA is correct!
```

**Stats**:
- 35,021 stop records claimed
- 16,865 unique stops actual
- 51.9% duplication rate

**Fix**: Deduplicate operator files before processing OR filter stops by actual geographic region

---

## Bug #3: Wrong LSOA Assignment Logic 🔴 CRITICAL

**File**: `data_pipeline/02_data_processing.py:535-629`

**Issue**:
```python
# Lines 593-623: Assigns stops to region's major cities
# Even if stop is in Newcastle, Yorkshire processor assigns it to Leeds!
for city in major_cities:  # ['Leeds', 'Sheffield', 'Bradford']
    assign_stops_to_these_lsoas(city)
```

**Impact**:
- Newcastle stops assigned Leeds LSOA codes
- Birmingham stops assigned Manchester LSOA codes
- **100% wrong demographic linkage for out-of-region stops**

**Fix**: Use proper postcode → LSOA geographic lookup API

---

## Bug #4: Demographics Not Merging 🔴 CRITICAL

**File**: `data_pipeline/02_data_processing.py:631-694`

**Issue**:
```python
# Merge reports success but transfers NO data
merged_df = stops.merge(demographics, on='lsoa_code', how='left')
logger.success(f"✓ {dataset}: {matched} matches")  # ← LIES!
# matched = len(stops), not actual data matches
```

**Impact**:
- 2,235 demographic columns exist but are ALL NULL
- Only schools_by_lsoa works (50% coverage)
- Age, population, unemployment, business data: 0% coverage

**Root causes**:
1. LSOA codes don't match (see Bug #3)
2. No validation after merge
3. Some demographic files missing `lsoa_code` column

**Fix**:
1. Fix LSOA assignment (Bug #3)
2. Add post-merge validation
3. Check LSOA code format matches before merge

---

## Bug #5: Route Uniqueness Key Wrong 🔴 CRITICAL

**File**: `data_pipeline/02_data_processing.py:393`

**Issue**:
```python
stops_df.drop_duplicates(subset=['route_id'], keep='first')
# But route_id "1" exists for 4 different operators!
```

**Impact**:
- 6,150 route records
- 335 "unique" routes (by route_id alone)
- **Real unique routes: 2,000-5,000+**

**Example**:
```
Route "1" appears 33 times in North East:
- Stanley Travel Route 1 (different route)
- Hodgson Coach Route 1 (different route)
- Durham Council Route 1 (different route)
- Weardale Motor Route 1 (different route)
```

**Fix**: Use `operator_id + route_id` as uniqueness key

---

## Bug #6: Missing Route-Stop Linkage ⚠️ IMPORTANT

**File**: `data_pipeline/02_data_processing.py:696-724`

**Issue**:
- Parser extracts `trips` and `stop_times` from GTFS
- But save function doesn't save them!
- Only saves: stops, routes, services

**Impact**:
- Can't answer "which stops does route X serve?"
- Can't link routes → stops → demographics
- Can't calculate service frequency
- 57 policy questions unanswerable

**Fix**: Save trips/stop_times data

---

## Corrected Numbers

### Current State (5/9 regions, with bugs):
| Metric | Claimed | Actual | Notes |
|--------|---------|--------|-------|
| Stops | 35,021 | 16,865 unique | 51.9% cross-region duplicates |
| Routes | 873 | ~6,000? | Wrong uniqueness key |
| Demographics | "Merged" | 0% (except schools 50%) | NULL data |

### Expected After Fixes (5/9 regions):
| Metric | Expected | Source |
|--------|----------|--------|
| Stops | 30,000-35,000 | Web research: 60K total / 2 regions ×  5 = 30K |
| Routes | 1,000-2,500 | Estimated from operator counts |
| Demographics | 100% | After LSOA fix |

### Full UK (9/9 regions):
| Metric | Expected |
|--------|----------|
| Stops | 60,000-70,000 |
| Routes | 2,000-5,000 |

---

## Priority Fix Order

1. **Bug #1**: Remove 10-file XML limit → Get all data
2. **Bug #2**: Deduplicate cross-region operators → Remove duplicates
3. **Bug #3**: Fix LSOA assignment → Correct geography
4. **Bug #4**: Fix demographic merge → Get demographics working
5. **Bug #5**: Fix route uniqueness → Accurate route counts
6. **Bug #6**: Save route-stop linkage → Enable analysis

---

## References

### Web Research - Stop Counts:
- West Yorkshire alone: 14,000+ stops
- South West: 13,227 stops (2017 LGA data)
- West Midlands: 12,784 stops (2017 LGA data)
- Yorkshire: 12,318 stops (2017 LGA data)
- North East: 6,000+ stops (Nexus alone)
- East Midlands: 12,000+ stops

**Source**: Local Government Association 2017 analysis, regional transport authorities

### Route Research:
- No specific totals found
- Estimated 2,000-5,000 routes UK-wide based on operator counts
- Route duplication analysis shows 335 is severely undercount

---

## Next Steps

1. Apply fixes to utils/gtfs_parser.py
2. Apply fixes to data_pipeline/02_data_processing.py
3. Re-run full pipeline
4. Validate results against expected ranges
5. Commit with message: "Fix 6 critical data quality bugs in processing pipeline"
