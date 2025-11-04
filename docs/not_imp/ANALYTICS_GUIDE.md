# UK Bus Analytics - Phase 3: Analytics & Visualization Guide

## Overview

This guide covers the analytics, visualization, and dashboard components of the UK Bus Analytics project. Phase 3 builds upon the data ingestion (Phase 1) and processing (Phase 2) to provide comprehensive insights and interactive visualizations.

## Components

### 1. Descriptive Analytics (`data_pipeline/04_descriptive_analytics.py`)

**Purpose:** Compute comprehensive KPIs and metrics across all UK regions

**Features:**
- Coverage metrics (stops per region, LSOA coverage)
- Service quality metrics (routes, operators)
- Demographic correlations (population, unemployment)
- Accessibility metrics (coordinate coverage, spatial distribution)
- National aggregates

**Usage:**
```bash
python3 data_pipeline/04_descriptive_analytics.py
```

**Outputs:**
- `analytics/analytics_results_[timestamp].json` - Comprehensive results
- `analytics/regional_summary.csv` - Regional KPI summary

**Key Metrics Computed:**
- Total stops and routes per region
- LSOA coverage percentages
- Coordinate data quality
- Population vs coverage analysis
- Unemployment vs accessibility metrics

---

### 2. Correlation Analysis (`analytics/05_correlation_analysis.py`)

**Purpose:** Analyze relationships between bus coverage and socio-economic indicators

**Features:**
- Population vs coverage correlation
- Unemployment vs accessibility correlation
- Underserved area identification
- Equity gap analysis
- Statistical significance testing

**Usage:**
```bash
python3 analytics/05_correlation_analysis.py
```

**Outputs:**
- `analytics/correlations/correlation_analysis_[timestamp].json`
- `analytics/correlations/lsoa_metrics.csv`
- `visualizations/population_vs_stops.png`
- `visualizations/stops_by_region.png`

**Key Analyses:**
- Pearson correlation coefficients
- Statistical significance (p-values)
- Identification of high-population low-access areas
- High-unemployment low-access areas

---

### 3. Geospatial Visualization (`visualizations/geo_visualizer.py`)

**Purpose:** Create interactive maps with multiple layers

**Features:**
- Interactive Folium maps
- Bus stop markers with popups
- Heatmap layers for density
- Regional and national overview maps
- Multi-tile layer support

**Usage:**
```bash
python3 visualizations/geo_visualizer.py
```

**Outputs:**
- `visualizations/maps/uk_national_bus_map.html` - National overview
- `visualizations/maps/{region}_bus_map.html` - Regional maps

**Map Features:**
- Clustered markers for performance
- Heatmaps showing stop density
- Popup information with demographics
- Layer toggles (stops, density, map style)
- Responsive design

---

### 4. Interactive Dashboard (`dashboard/app.py`)

**Purpose:** Streamlit-based interactive web dashboard

**Features:**
- National overview with key metrics
- Regional comparison visualizations
- Interactive data explorer
- Insights and findings
- Real-time filtering

**Usage:**
```bash
streamlit run dashboard/app.py
```

**Access:**
- Local URL: http://localhost:8501
- Network URL: http://[your-ip]:8501

**Pages:**

#### Overview Page
- Total stops, routes, regions metrics
- Bar charts: stops and routes by region
- Regional comparison table
- Stops per route analysis

#### Regional Analysis
- Region selector
- Key metrics per region
- Data quality indicators
- Sample data preview

#### Data Explorer
- Multi-region filters
- Scatter plots (routes vs stops)
- Distribution visualizations
- Comparative analysis

#### Insights
- National statistics
- Key findings summary
- Data quality metrics
- Recommended next steps

---

## Installation

### Install Required Packages

```bash
# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows

# Install new dependencies
pip install streamlit streamlit-folium scikit-learn
```

### Verify Installation

```bash
python3 -c "import streamlit; import folium; import plotly; print('All packages installed successfully')"
```

---

## Workflow

### Complete Analytics Workflow

1. **Run Descriptive Analytics**
   ```bash
   python3 data_pipeline/04_descriptive_analytics.py
   ```
   - Computes all KPIs
   - Generates regional summaries
   - Creates national aggregates

2. **Run Correlation Analysis**
   ```bash
   python3 analytics/05_correlation_analysis.py
   ```
   - Analyzes demographic relationships
   - Identifies equity gaps
   - Creates visualizations

3. **Generate Interactive Maps**
   ```bash
   python3 visualizations/geo_visualizer.py
   ```
   - Creates regional maps
   - Generates national overview
   - Produces HTML outputs

4. **Launch Dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```
   - Interactive web interface
   - Real-time exploration
   - Export capabilities

---

## Key Results

### National Statistics
- **60,275 bus stops** across UK
- **3,578 bus routes** catalogued
- **9 regions** fully covered
- **100% data processing** success rate

### Regional Breakdown
| Region | Stops | Routes |
|--------|-------|--------|
| South East | 18,010 | 243 |
| North West | 11,064 | 756 |
| Yorkshire | 8,995 | 546 |
| South West | 5,766 | 640 |
| West Midlands | 5,183 | 510 |
| East England | 4,130 | 440 |
| North East | 3,860 | 276 |
| London | 2,078 | 80 |
| East Midlands | 1,189 | 87 |

---

## Next Steps (Phase 4)

### Machine Learning Integration

1. **Route Clustering**
   - Use sentence transformers for route embeddings
   - Identify similar routes for optimization
   - Cluster analysis for service planning

2. **Time-Series Forecasting**
   - Implement demand prediction
   - Forecast service requirements
   - Seasonal pattern analysis

3. **Anomaly Detection**
   - Identify service gaps
   - Detect unusual patterns
   - Quality monitoring

4. **Natural Language Queries**
   - LLM-powered data exploration
   - Conversational analytics
   - Automated insights

---

## Troubleshooting

### Common Issues

**Issue: Dashboard shows "No data available"**
```bash
# Solution: Run analytics pipeline first
python3 data_pipeline/04_descriptive_analytics.py
```

**Issue: Maps don't display markers**
```bash
# Check if stops have coordinates
python3 -c "import pandas as pd; df = pd.read_csv('data_pipeline/processed/regions/yorkshire/stops_processed.csv'); print(df['latitude'].notna().sum())"
```

**Issue: Streamlit port already in use**
```bash
# Use different port
streamlit run dashboard/app.py --server.port 8502
```

---

## Performance Optimization

### For Large Datasets

1. **Use marker clustering** for maps with >10,000 points
2. **Enable caching** in Streamlit (@st.cache_data)
3. **Filter data** before visualization
4. **Limit heatmap** resolution for large regions

### Memory Management

```python
# For very large regions, process in chunks
chunk_size = 10000
for chunk in pd.read_csv(file, chunksize=chunk_size):
    process_chunk(chunk)
```

---

## Customization

### Adding New Metrics

Edit `data_pipeline/04_descriptive_analytics.py`:

```python
def compute_custom_metric(self, region_code: str, data: Dict) -> Dict:
    """Your custom metric computation"""
    metrics = {
        'region': region_code,
        'your_metric': calculated_value
    }
    return metrics
```

### Adding Dashboard Pages

Edit `dashboard/app.py`:

```python
def show_custom_page(data):
    st.header("Your Custom Page")
    # Your visualizations here
```

---

## Outputs Summary

### Files Generated

- `analytics/analytics_results_*.json` - Complete analytics results
- `analytics/regional_summary.csv` - Regional KPI table
- `analytics/correlations/correlation_analysis_*.json` - Correlation results
- `analytics/correlations/lsoa_metrics.csv` - LSOA-level metrics
- `visualizations/*.png` - Static charts
- `visualizations/maps/*.html` - Interactive maps

### Data Quality

- ✅ 100% regional coverage (9/9 regions)
- ✅ 60,275 stops processed
- ✅ 3,578 routes catalogued
- ⚠️ Coordinate enrichment in progress
- ⚠️ Demographic integration ongoing

---

## Support

For issues or questions:
1. Check this guide
2. Review logs in `logs/` directory
3. Verify data processing completed successfully
4. Ensure all dependencies are installed

---

## License

This project is part of the UK Bus Analytics initiative.

**Generated:** October 28, 2025
