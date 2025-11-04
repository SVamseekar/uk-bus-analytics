# Quick Start Guide - Analytics & Dashboard

## Run Analytics in 3 Steps

### Step 1: Run Descriptive Analytics
```bash
python3 data_pipeline/04_descriptive_analytics.py
```
**Output:** Regional KPIs and national statistics

### Step 2: Run Correlation Analysis
```bash
python3 analytics/05_correlation_analysis.py
```
**Output:** Demographic correlations and visualizations

### Step 3: Launch Dashboard
```bash
streamlit run dashboard/app.py
```
**Access:** http://localhost:8501

---

## Optional: Generate Interactive Maps

```bash
python3 visualizations/geo_visualizer.py
```
**Output:** Interactive HTML maps in `visualizations/maps/`

---

## View Results

### Analytics Results
- `analytics/regional_summary.csv` - Regional KPI table
- `analytics/analytics_results_*.json` - Complete results

### Dashboard
- Open browser to http://localhost:8501
- Navigate through 4 pages:
  - Overview
  - Regional Analysis
  - Data Explorer
  - Insights

### Maps
- Open `visualizations/maps/uk_national_bus_map.html` in browser
- Regional maps: `visualizations/maps/{region}_bus_map.html`

---

## Current Statistics

- **60,275** bus stops across UK
- **3,578** bus routes
- **9** regions fully covered
- **100%** data processing success

---

## Need Help?

See `ANALYTICS_GUIDE.md` for detailed documentation.
