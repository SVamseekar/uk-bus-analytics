# Analytics Directory

This directory contains all analytical scripts and their outputs for the UK Bus Analytics project.

## Structure

```
analytics/
├── descriptive_analysis.py          # Comprehensive descriptive statistics
├── 05_correlation_analysis.py       # Socio-economic correlation analysis
│
├── data/                             # Analysis input/output datasets
│   └── lsoa_analysis_results.csv    # LSOA-level analysis results
│
├── images/                           # Generated visualizations
│   ├── descriptive/                 # Descriptive analysis charts
│   │   ├── 01_stops_distribution.png
│   │   ├── 02_geographic_coverage.png
│   │   └── 07_analysis_dashboard.png
│   └── correlation/                 # Correlation heatmaps and charts
│
└── outputs/                          # Analysis results (JSON, CSV)
    ├── descriptive/                 # Descriptive statistics outputs
    │   ├── analytics_results_*.json
    │   ├── regional_summary.csv
    │   ├── all_57_answers.json
    │   ├── comprehensive_analysis_report.txt
    │   └── comprehensive_kpis.json
    └── correlation/                 # Correlation analysis outputs
        ├── correlation_analysis_*.json
        └── lsoa_metrics.csv
```

## Scripts

### `descriptive_analysis.py`
**Purpose:** Comprehensive descriptive analysis answering 57 research questions

**Outputs:**
- Regional statistics and KPIs
- Bus coverage metrics
- Service frequency analysis
- Temporal trends
- Visualizations

**Run:**
```bash
python analytics/descriptive_analysis.py
```

### `05_correlation_analysis.py`
**Purpose:** Advanced correlation analysis between bus coverage and socio-economic indicators

**Outputs:**
- Correlation matrices
- Underserved area identification
- Equity gap analysis
- LSOA-level metrics

**Run:**
```bash
python analytics/05_correlation_analysis.py
```

## Data Files

### `data/`
- **lsoa_analysis_results.csv**: Comprehensive LSOA-level analysis results
- Contains merged transport and demographic data
- Used for correlation and equity analysis

## Output Organization

### `outputs/descriptive/`
- JSON files with timestamped analysis results
- Regional summaries in CSV format
- Comprehensive KPI reports
- Answers to all 57 research questions

### `outputs/correlation/`
- Correlation coefficients and p-values
- Statistical significance tests
- LSOA-level metrics linking transport and demographics

### `images/descriptive/`
- Geographic coverage maps
- Stop distribution charts
- Service frequency visualizations
- Dashboard screenshots

### `images/correlation/`
- Correlation heatmaps
- Scatter plots showing relationships
- Underserved area maps

## Naming Conventions

**Timestamped outputs:**
- Format: `{analysis_type}_YYYYMMDD_HHMMSS.json`
- Example: `analytics_results_20251028_163213.json`

**Image files:**
- Format: `{number}_{description}.png`
- Example: `01_stops_distribution.png`

## Notes

- All outputs are gitignored (too large for git)
- Run scripts from project root directory
- Results are automatically timestamped
- Images are organized by analysis type for easy reference

## Related Documentation

- **Analytics Guide**: `docs/ANALYTICS_GUIDE.md`
- **Research Questions**: See `outputs/descriptive/all_57_answers.json`
- **Project Structure**: `docs/PROJECT_STRUCTURE.md`
