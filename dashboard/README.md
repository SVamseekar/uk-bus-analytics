# UK Bus Analytics Dashboard

Professional consulting intelligence platform for UK bus transport analysis.

## Design Philosophy

**This is NOT an academic research tool. This is a professional consulting intelligence platform.**

- ❌ NO academic language ("Question A1", "8 questions", "Data Story")
- ✅ Professional consulting report style (McKinsey, Deloitte, PwC aesthetic)
- ✅ Executive summary approach
- ✅ Decision-maker focused
- ✅ Clean, spacious layouts

See `docs/imp/FINAL_IMPLEMENTATION_ROADMAP_PART1.md` Section 3 for full design philosophy.

## Project Structure

```
dashboard/
├── Home.py                                  # Homepage with national overview
├── pages/
│   └── 01_Coverage_Accessibility.py         # Category A (2/8 sections complete)
├── components/
│   └── category_template.py                 # Reusable template for all categories
└── utils/
    └── data_loader.py                       # Cached data loading functions
```

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install streamlit pandas plotly loguru
```

### Data Preparation

```bash
# Generate regional summary data (required for dashboard)
python3 utils/create_regional_summary.py
```

This creates `data/processed/outputs/regional_summary.csv` with:
- 9 regions
- 779,262 total stops
- 2,749 routes
- Key metrics: stops_per_1000, routes_per_100k, rankings

## Running the Dashboard

```bash
# Start dashboard (runs on http://localhost:8501)
streamlit run dashboard/Home.py
```

## Current Status (Task 1.4 - Week 1 Day 3)

### ✅ Completed

1. **Global Design Philosophy** - Added to roadmap (Section 3)
   - Professional consulting style enforced everywhere
   - No academic language allowed
   - User-facing content vs backend code separation

2. **Category Template (`category_template.py`)** - Production-ready
   - Reusable for all 10 categories
   - Professional layout: 60% viz, 40% narrative
   - Clean section structure: Summary → Key Finding → Policy Recommendation
   - Custom CSS for OECD/World Bank aesthetic

3. **Data Loader Utilities (`data_loader.py`)** - Complete
   - Cached loading functions (1 hour TTL)
   - Regional summary, stops, routes data
   - National statistics aggregation
   - Urban/rural filtering support

4. **Homepage (`Home.py`)** - Basic version ready
   - National overview metrics
   - Regional performance table
   - Category navigation guide

5. **Category A Page (`01_Coverage_Accessibility.py`)** - 2/8 sections complete
   - ✅ Section 1: Regional Route Density Analysis (fully implemented)
   - ✅ Section 2: Service Coverage Assessment (fully implemented)
   - ⚠️ Sections 3-8: Placeholder (Task 1.5)

### Professional Section Titles (User-Facing)

**Category A: Coverage & Accessibility**
1. Regional Route Density Analysis (A1)
2. Service Coverage Assessment (A2)
3. High-Density Underserved Areas (A3) - *pending*
4. Service Desert Identification (A4) - *pending*
5. Walking Distance Analysis (A5) - *pending*
6. Accessibility Standard Compliance (A6) - *pending*
7. Urban-Rural Coverage Disparity (A7) - *pending*
8. Population-Service Mismatch Zones (A8) - *pending*

## Example: Professional vs Academic Style

### ❌ BEFORE (Academic Style)
```
QUESTION A1: Which regions have the highest bus routes per capita?

📖 DATA STORY
Manchester has 42 routes per 100k...

💡 KEY INSIGHT
Route density varies...
```

### ✅ AFTER (Consulting Style)
```
Regional Route Density Analysis

Manchester leads the nation with 42 routes per 100,000 population,
providing extensive network connectivity...

Key Finding
Route density varies 7.4x between regions. Network design and policy
choices matter more than population scale alone...

Policy Recommendation
Five regions fall below national average. Estimated investment: £42M
(BCR: 2.1 - High value for money).

Priority actions: (1) Identify underserved corridors...
```

## Next Steps (Task 1.5 - Week 1 Day 4-5)

Complete remaining 6 sections of Category A:
- A3: High-Density Underserved Areas (scatter plot analysis)
- A4: Service Desert Identification (LSOA with 0 stops)
- A5: Walking Distance Analysis (average distance to nearest stop)
- A6: Accessibility Standard Compliance (>500m analysis)
- A7: Urban-Rural Coverage Disparity (box plot comparison)
- A8: Population-Service Mismatch Zones (heatmap overlay)

Each section needs:
1. Data loading function
2. Visualization function (Plotly chart)
3. Narrative function (summary, key finding, recommendation)

## Data Sources

- **BODS** - Bus Open Data Service (October 2025 snapshot)
- **ONS Census 2021** - Demographics, LSOA boundaries
- **NaPTAN** - National Public Transport Access Nodes
- **NOMIS** - Official labor market statistics
- **IMD 2019** - Index of Multiple Deprivation

## File Locations

**Input Data:**
- `data/processed/outputs/regional_summary.csv` - Regional metrics
- `data/processed/regions/{region}/stops_processed.csv` - Individual region data
- `data/processed/outputs/all_stops_deduplicated.csv` - Combined stops (68,572 unique)

**Dashboard Assets:**
- `dashboard/components/` - Reusable UI components
- `dashboard/utils/` - Data loading and helper functions
- `dashboard/pages/` - Category analysis pages

## Testing

```bash
# Test data availability
python3 -c "
import pandas as pd
df = pd.read_csv('data/processed/outputs/regional_summary.csv')
print(f'Regions: {len(df)}')
print(f'Total stops: {df.total_stops.sum():,}')
"

# Should output:
# Regions: 9
# Total stops: 779,262
```

## Task 1.4 Success Criteria

- [x] Global design philosophy documented in roadmap
- [x] Category template built with consulting style
- [x] Data loader utilities created with caching
- [x] Category A page created (2/8 sections functional)
- [x] Regional summary data generated
- [x] Homepage created
- [ ] Local testing (requires: `pip install streamlit`)

**Status: Task 1.4 READY FOR TESTING**

To complete: Install Streamlit and test locally, then proceed to Task 1.5.
