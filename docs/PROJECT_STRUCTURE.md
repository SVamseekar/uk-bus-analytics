# UK Bus Analytics - Project Structure

This document provides a comprehensive guide to the project's directory structure, explaining the purpose and significance of each folder and file.

## Table of Contents
- [Root Directory](#root-directory)
- [Core Directories](#core-directories)
- [Data Management](#data-management)
- [Documentation](#documentation)
- [Scripts and Tools](#scripts-and-tools)
- [File Naming Conventions](#file-naming-conventions)

---

## Root Directory

```
uk_bus_analytics/
├── README.md                   # Main project overview and getting started guide
├── requirements.txt            # Python package dependencies
├── .env                        # Environment variables (API keys, credentials)
├── .env.example               # Template for environment variables
├── .gitignore                 # Git ignore rules
└── .github/                   # GitHub workflows and configurations
```

**Key Files:**
- **README.md**: First point of reference - project overview, setup instructions, usage examples
- **requirements.txt**: All Python dependencies needed to run the project
- **.env**: Contains sensitive credentials (never committed to git)

---

## Core Directories

### 1. `data_pipeline/` - ETL Pipeline
The heart of the data processing system.

```
data_pipeline/
├── 01_data_ingestion.py        # Downloads data from BODS, ONS, NaPTAN
├── 02_data_processing.py       # Cleans, transforms, integrates data
├── 03_data_validation.py       # Data quality checks and validation
├── 04_descriptive_analytics.py # Initial statistical analysis
├── raw/                        # Downloaded raw data (gitignored)
│   ├── bods/                  # Bus Open Data Service files
│   ├── boundaries/            # Geographic boundary files
│   ├── demographics/          # ONS demographic data
│   ├── gtfs/                  # GTFS transit feeds
│   ├── naptan/                # NaPTAN stop data
│   ├── ons/                   # ONS statistical data
│   ├── regions/               # Regional transport data
│   └── transxchange/          # TransXChange XML files
├── processed/                  # Cleaned, processed data (gitignored)
│   ├── demographics/          # Processed demographic datasets
│   ├── integrated/            # Combined transport + demographic data
│   ├── regions/               # Regional processed data
│   │   ├── london/
│   │   ├── manchester/
│   │   └── ...                # Other UK regions
│   └── transport/             # Processed transport data
└── staging/                    # Temporary processing files
    ├── temp/                  # Temporary work files
    └── validation/            # Validation intermediate files
```

**Pipeline Flow:**
1. **Ingestion** → Downloads and caches raw data
2. **Processing** → Cleans, transforms, links LSOA codes
3. **Validation** → Quality checks, completeness verification
4. **Analytics** → Initial descriptive statistics

---

### 2. `analytics/` - Advanced Analysis
All analytical scripts and outputs.

```
analytics/
├── descriptive_analysis.py     # Comprehensive descriptive statistics
├── 05_correlation_analysis.py  # Socio-economic correlations
├── results/                    # Analysis outputs
│   └── comprehensive_analysis_report.txt
├── correlations/               # Correlation analysis outputs
├── regional_summary.csv        # Regional summary statistics
└── analytics_results_*.json    # Timestamped analysis results
```

**Purpose:**
- Answers the 57+ research questions
- Computes KPIs (stops per capita, coverage, frequency)
- Analyzes correlations between transport and demographics
- Identifies underserved areas and equity gaps

---

### 3. `dashboard/` - Web Interface
Interactive visualization and user interface.

```
dashboard/
├── app.py                      # Main Dash/Streamlit application
└── assets/                     # Dashboard resources
    ├── styles.css             # Custom styling
    ├── images/                # Logo, icons
    └── data/                  # Dashboard-specific data cache
```

**Features:**
- Interactive maps with multiple layers
- Real-time filtering and exploration
- KPI dashboards
- Export capabilities

---

### 4. `utils/` - Utility Functions
Reusable helper functions and modules.

```
utils/
├── api_client.py               # API interaction utilities
├── geographic_data_client.py   # Geographic data handling
├── gtfs_parser.py              # GTFS file parser
├── transxchange_stop_extractor.py  # TransXChange XML parser
├── merge_naptan_coordinates.py # NaPTAN coordinate merging
└── final_lsoa_linker.py        # LSOA spatial linkage
```

**Purpose:**
- Shared code across pipeline stages
- API clients for external data sources
- Parsing utilities for different data formats
- Geographic processing functions

---

### 5. `visualizations/` - Visual Outputs
Generated charts, maps, and figures.

```
visualizations/
├── geo_visualizer.py           # Geographic visualization tools
└── output/                     # Generated visualizations
    ├── stops_by_region.png
    ├── correlation_heatmaps/
    ├── coverage_maps/
    └── temporal_trends/
```

---

### 6. `config/` - Configuration
All configuration files and settings.

```
config/
├── settings.py                 # Application settings and paths
├── ingestion_config.yaml       # Data source configurations
├── api_keys/                   # API credentials (gitignored)
└── data_sources/               # Data source definitions
```

**Key Settings:**
- File paths and directories
- API endpoints
- Processing parameters
- Regional definitions

---

## Data Management

### 7. `data/` - Large Data Files
Storage for large datasets not suitable for git.

```
data/
├── Stops.csv                   # 100MB NaPTAN stops dataset
├── pipeline_status_report.json # Pipeline execution status
└── cache/                      # Cached API responses
```

**Note:** This directory is gitignored due to file sizes.

---

## Documentation

### 8. `docs/` - Documentation Hub
All project documentation organized by purpose.

```
docs/
├── PROJECT_STRUCTURE.md        # This file - structure guide
├── QUICKSTART.md               # Quick start guide
├── ANALYTICS_GUIDE.md          # Analytics methodology
├── LAUNCH_INSTRUCTIONS.md      # Deployment instructions
├── reports/                    # Status and completion reports
│   ├── PHASE3_COMPLETION_REPORT.md
│   ├── PROCESSING_COMPLETE_REPORT.md
│   ├── FIXED_LSOA_REPORT.md
│   ├── PROJECT_STATUS_REPORT.md
│   └── READY_TO_LAUNCH.md
└── guides/                     # User guides
    └── MANUAL_DOWNLOAD_GUIDE.md
```

**Documentation Types:**
- **Guides**: How-to documentation for users
- **Reports**: Status updates and milestone reports
- **Technical**: Architecture and methodology docs

---

## Scripts and Tools

### 9. `scripts/` - Operational Scripts
Utility scripts for common operations.

```
scripts/
├── run_dashboard.sh            # Launch dashboard server
├── status.sh                   # Quick pipeline status check
└── check_downloads.py          # Verify downloaded data
```

**Usage:**
```bash
# Check pipeline status
./scripts/status.sh

# Launch dashboard
./scripts/run_dashboard.sh

# Verify downloads
python scripts/check_downloads.py
```

---

### 10. `tests/` - Test Suite
All test files for quality assurance.

```
tests/
├── test_setup.py               # Environment setup tests
├── test_pipeline_status.py     # Pipeline health checks
├── test_processing_quick.py    # Quick processing tests
└── test_transport_download.py  # Download functionality tests
```

**Run Tests:**
```bash
pytest tests/
```

---

### 11. `logs/` - Application Logs
Timestamped logs for all operations.

```
logs/
├── ingestion_YYYY-MM-DD_HH-MM-SS_*.log
├── processing_YYYY-MM-DD_HH-MM-SS_*.log
├── validation_YYYY-MM-DD_HH-MM-SS_*.log
└── analytics_YYYY-MM-DD_HH-MM-SS_*.log
```

**Log Retention:** 30 days with daily rotation

---

### 12. `notebooks/` - Jupyter Notebooks
Exploratory analysis and prototyping.

```
notebooks/
├── exploratory_analysis.ipynb
├── visualization_prototypes.ipynb
└── ml_experiments.ipynb
```

---

## File Naming Conventions

### Python Scripts
- **Pipeline stages**: `0X_stage_name.py` (e.g., `01_data_ingestion.py`)
- **Tests**: `test_*.py`
- **Utilities**: `descriptive_name.py`

### Data Files
- **Regional data**: `{region_name}_{data_type}.csv`
- **Processed data**: `*_cleaned.csv`, `*_processed.csv`
- **Timestamped outputs**: `{name}_YYYYMMDD_HHMMSS.{ext}`

### Documentation
- **Guides**: `UPPER_CASE.md` (e.g., `QUICKSTART.md`)
- **Reports**: `*_REPORT.md`

---

## Directory Significance Summary

| Directory | Purpose | Gitignored | Critical |
|-----------|---------|-----------|----------|
| `data_pipeline/` | Core ETL processing | Partially (raw/processed) | ✅ Yes |
| `analytics/` | Statistical analysis | No (code only) | ✅ Yes |
| `dashboard/` | Web interface | No | ✅ Yes |
| `utils/` | Shared utilities | No | ✅ Yes |
| `config/` | Settings | Partially (api_keys) | ✅ Yes |
| `docs/` | Documentation | No | ⚠️ Important |
| `scripts/` | Operational tools | No | ⚠️ Important |
| `tests/` | Test suite | No | ⚠️ Important |
| `data/` | Large datasets | ✅ Yes | ⚠️ Important |
| `logs/` | Application logs | ✅ Yes | ℹ️ Reference |
| `visualizations/` | Generated visuals | Partially (output/) | ℹ️ Reference |
| `notebooks/` | Exploration | No | ℹ️ Optional |

---

## Quick Navigation

**To add new features:**
1. **New data source** → Add to `data_pipeline/01_data_ingestion.py`
2. **New analysis** → Create in `analytics/`
3. **New visualization** → Update `dashboard/app.py` or `visualizations/`
4. **New utility** → Add to `utils/`

**Common Paths (in code):**
```python
from config.settings import DATA_RAW, DATA_PROCESSED, LOGS_DIR
from utils.gtfs_parser import GTFSParser
```

---

## Maintenance Guidelines

### Regular Cleanup
```bash
# Clean temporary files
rm -rf data_pipeline/staging/temp/*

# Archive old logs (older than 30 days)
find logs/ -name "*.log" -mtime +30 -delete

# Clean cache
rm -rf data/cache/*
```

### Backup Strategy
- **Code**: Git repository (GitHub)
- **Raw data**: External backup (not in git)
- **Processed data**: Can be regenerated from raw
- **Logs**: 30-day retention, archive if needed

---

## Troubleshooting

**Import errors after reorganization:**
- Ensure you're running from project root
- Check `sys.path` includes project root
- Python files use: `sys.path.append(str(Path(__file__).parent.parent))`

**Scripts not working:**
- Scripts now in `scripts/` directory
- Update paths: `python scripts/check_downloads.py`
- Shell scripts navigate to project root automatically

**Missing data:**
- Check `data/` directory exists
- Run ingestion: `python data_pipeline/01_data_ingestion.py`
- Check logs in `logs/` for errors

---

**Last Updated:** 2025-10-28
**Maintainer:** UK Bus Analytics Team
**Version:** 2.0 (Post-Reorganization)
