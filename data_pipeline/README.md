# Data Pipeline Directory

This directory contains the core ETL (Extract, Transform, Load) pipeline for the UK Bus Analytics project.

## Structure

```
data_pipeline/
├── 01_data_ingestion.py              # Data download and ingestion
├── 02_data_processing.py             # Data transformation and cleaning
├── 03_data_validation.py             # Data quality checks
├── 04_descriptive_analytics.py       # Initial statistical analysis
│
├── raw/                              # Downloaded raw data (gitignored)
│   ├── boundaries/                  # Geographic boundary files
│   ├── demographics/                # ONS demographic data (consolidated)
│   ├── naptan/                      # NaPTAN stop data
│   ├── ons/                         # ONS statistical datasets
│   ├── regions/                     # Regional transport data
│   ├── transport/                   # Transport data by region
│   ├── transxchange/                # TransXChange XML files
│   ├── bods/                        # Bus Open Data Service files
│   └── gtfs/                        # GTFS transit feeds
│
├── processed/                        # Cleaned, processed data (gitignored)
│   ├── demographics/                # Processed demographic datasets
│   ├── integrated/                  # Combined transport + demographic data
│   ├── regions/                     # Regional processed data
│   │   ├── london/
│   │   ├── manchester/
│   │   └── [other UK regions]/
│   ├── transport/                   # Processed transport data
│   ├── outputs/                     # Processing outputs (CSV, JSON)
│   └── reports/                     # Validation and processing reports
│
└── staging/                          # Temporary processing files
    ├── temp/                        # Temporary work files
    └── validation/                  # Validation intermediate files
```

## Pipeline Scripts

### 1. `01_data_ingestion.py`
**Purpose:** Downloads data from external sources

**Data Sources:**
- BODS (Bus Open Data Service)
- ONS (Office for National Statistics)
- NaPTAN (National Public Transport Access Nodes)
- Geographic boundaries
- Regional transport operators

**Outputs:**
- Raw data files in `raw/` subdirectories
- Ingestion report: `raw/ingestion_report.json`

**Run:**
```bash
python data_pipeline/01_data_ingestion.py
```

### 2. `02_data_processing.py`
**Purpose:** Cleans, transforms, and integrates data

**Processing Steps:**
1. Parse GTFS and TransXChange files
2. Clean and standardize stops data
3. Link stops to LSOA codes (geographic areas)
4. Merge transport and demographic data
5. Calculate derived metrics

**Outputs:**
- Processed files in `processed/` subdirectories
- Processing stats: `processed/outputs/processing_stats.json`

**Run:**
```bash
python data_pipeline/02_data_processing.py
```

### 3. `03_data_validation.py`
**Purpose:** Validates data quality and completeness

**Checks:**
- Missing values
- Data type consistency
- Geographic coordinate validity
- LSOA code coverage
- Temporal completeness

**Outputs:**
- Validation report: `processed/outputs/validation_report.json`
- Validation summary: `processed/outputs/validation_summary.txt`

**Run:**
```bash
python data_pipeline/03_data_validation.py
```

### 4. `04_descriptive_analytics.py`
**Purpose:** Initial statistical analysis and KPI calculation

**Metrics:**
- Bus stops per region
- Routes per capita
- Service frequency
- Coverage statistics

**Outputs:**
- Initial analytics in `processed/outputs/`

**Run:**
```bash
python data_pipeline/04_descriptive_analytics.py
```

## Data Organization

### `raw/` Directory

**Purpose:** Stores unmodified downloaded data

**Subdirectories:**
- **boundaries/**: Shapefiles, GeoJSON for geographic boundaries
- **demographics/**: Population, employment, deprivation data (consolidated from duplicate folders)
- **naptan/**: National bus stop database
- **ons/**: ONS statistical releases
- **regions/**: Regional transport data archives
- **transport/**: Transport data organized by region
- **transxchange/**: XML bus timetable files

**Note:** This directory is gitignored due to file sizes

### `processed/` Directory

**Purpose:** Stores cleaned, processed datasets

**Subdirectories:**
- **demographics/**: Processed demographic datasets
- **integrated/**: Transport + demographic merged data
- **regions/**: Regional processed files (9 UK regions)
- **transport/**: Processed transport datasets
- **outputs/**: Processing results, statistics, reports
- **reports/**: Validation and quality reports

**Note:** This directory is gitignored; can be regenerated from raw data

### `staging/` Directory

**Purpose:** Temporary files during processing

**Subdirectories:**
- **temp/**: Intermediate processing files
- **validation/**: Validation intermediate results

**Note:** Can be safely deleted; automatically recreated

## Regional Coverage

The pipeline processes data for **9 UK regions:**
1. London
2. South East
3. South West
4. East of England (East England)
5. West Midlands
6. East Midlands
7. Yorkshire and the Humber (Yorkshire)
8. North West
9. North East

Each region has dedicated subdirectories in both `raw/regions/` and `processed/regions/`.

## File Naming Conventions

### Raw Data
- Format: `{source}_{date}.{ext}`
- Example: `population_2021.csv`

### Processed Data
- Format: `{region}_{datatype}_processed.csv`
- Example: `london_stops_cleaned.csv`

### Reports
- Format: `{report_type}_YYYY-MM-DD_HH-MM-SS.{ext}`
- Example: `validation_2025-10-28_15-50-59.json`

## Data Flow

```
Raw Data Sources
       ↓
[01_data_ingestion.py]  → raw/
       ↓
[02_data_processing.py] → processed/
       ↓
[03_data_validation.py] → processed/outputs/
       ↓
[04_descriptive_analytics.py] → processed/outputs/
       ↓
analytics/ (correlation & advanced analysis)
```

## Common Operations

### Re-run Entire Pipeline
```bash
python data_pipeline/01_data_ingestion.py
python data_pipeline/02_data_processing.py
python data_pipeline/03_data_validation.py
```

### Check Pipeline Status
```bash
./scripts/status.sh
```

### Clean Processed Data (Force Reprocessing)
```bash
rm -rf data_pipeline/processed/*
python data_pipeline/02_data_processing.py
```

### Clean Staging Files
```bash
rm -rf data_pipeline/staging/temp/*
```

## Important Notes

### Demographic Data Consolidation
- **Previous Issue**: Duplicate `demographic/` and `demographics/` folders
- **Resolution**: Consolidated into single `demographics/` folder
- **Content**: Merged unique files from both sources
- **Files**: age_structure, business_counts, IMD, population, unemployment, schools

### Gitignore
All data directories (`raw/`, `processed/`, `staging/`) are gitignored because:
- Files are too large for git
- Data can be re-downloaded
- Processing can be re-run
- Prevents repository bloat

### Logs
Pipeline execution logs are stored in project-level `logs/` directory:
- `logs/ingestion_*.log`
- `logs/processing_*.log`
- `logs/validation_*.log`

## Troubleshooting

**Missing raw data?**
```bash
python data_pipeline/01_data_ingestion.py
```

**Processing errors?**
- Check logs in `logs/processing_*.log`
- Verify raw data completeness
- Run validation: `python data_pipeline/03_data_validation.py`

**LSOA linkage issues?**
- See `docs/reports/FIXED_LSOA_REPORT.md`
- Check boundary files in `raw/boundaries/`

## Related Documentation

- **Processing Report**: `docs/reports/PROCESSING_COMPLETE_REPORT.md`
- **LSOA Linkage**: `docs/reports/FIXED_LSOA_REPORT.md`
- **Project Structure**: `docs/PROJECT_STRUCTURE.md`
- **Analytics Guide**: `docs/ANALYTICS_GUIDE.md`
