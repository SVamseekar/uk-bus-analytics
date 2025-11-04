# Data Update Schedule Guide

## Quick Answer

**No, you DON'T need to run the full pipeline daily!**

Most data sources update infrequently, so running daily wastes time and resources.

---

## Recommended Update Frequencies

### **Weekly Updates (Recommended for Most Users)**

```bash
# Run every Monday morning
python3 scripts/smart_pipeline_update.py
```

This checks what needs updating and only runs necessary components.

---

## Data Source Update Frequencies

| Data Source | Update Frequency | Pipeline Component |
|------------|------------------|-------------------|
| **BODS Timetables** | Weekly/Monthly | `01_data_ingestion.py` |
| **NaPTAN Stops** | Monthly | `01_data_ingestion.py` |
| **ONS Demographics** | Annual | `01_data_ingestion.py` |
| **NOMIS Employment** | Quarterly | `01_data_ingestion.py` |
| **IMD Scores** | Every 3-5 years | `01_data_ingestion.py` |

---

## Smart Update Strategy

### Option 1: Smart Weekly Update (Recommended)

```bash
# Every Monday at 6 AM (add to crontab)
0 6 * * 1 cd /path/to/uk_bus_analytics && python3 scripts/smart_pipeline_update.py
```

**What it does:**
- ✅ Checks last update times
- ✅ Only downloads data if > 7 days old
- ✅ Only reprocesses if new data downloaded
- ✅ Only recomputes metrics if processing changed
- ✅ Only retrains ML models if > 30 days old

### Option 2: Manual Control

```bash
# Force all components (e.g., after major data release)
python3 scripts/smart_pipeline_update.py --force

# Force specific component only
python3 scripts/smart_pipeline_update.py --component ingestion
python3 scripts/smart_pipeline_update.py --component processing
python3 scripts/smart_pipeline_update.py --component metrics
python3 scripts/smart_pipeline_update.py --component ml
```

### Option 3: Manual Pipeline Run

```bash
# Run full pipeline manually (for major updates)
python3 data_pipeline/01_data_ingestion.py
python3 data_pipeline/02_data_processing.py
python3 analysis/spatial/01_compute_spatial_metrics_v2.py
python3 analysis/spatial/02_train_ml_models.py  # Only if needed
```

---

## When to Force Full Pipeline

Run the full pipeline in these cases:

1. **First Time Setup** - Initial data ingestion
2. **Major BODS Release** - Significant timetable changes (check BODS website)
3. **ONS Census Data** - New census release (happens every 10 years!)
4. **After Code Changes** - Modified processing logic
5. **Data Corruption** - Need to rebuild from scratch

---

## Optimized Schedules by Use Case

### **Production Dashboard (Public-Facing)**
```bash
# Weekly updates are sufficient
0 6 * * 1 python3 scripts/smart_pipeline_update.py

# Dashboard runs continuously
streamlit run dashboard/Home.py
```

### **Research/Analysis Project**
```bash
# Monthly updates unless actively analyzing new data
# Run manually when needed:
python3 scripts/smart_pipeline_update.py
```

### **Development Environment**
```bash
# Don't auto-update during development
# Run manually after code changes:
python3 scripts/smart_pipeline_update.py --force
```

---

## What Actually Needs Daily Updates?

**Nothing in your current pipeline needs daily updates!**

If you want **real-time bus positions** (which you're NOT currently using):
- BODS provides GTFS-RT feeds for live vehicle positions
- Would need separate real-time data pipeline
- Updates every 30 seconds
- **NOT included in your current setup**

---

## Data Freshness Check

Check when data was last updated:

```bash
# View pipeline status
python3 -c "
import json
from pathlib import Path

status_file = Path('data/pipeline_status.json')
if status_file.exists():
    with open(status_file) as f:
        status = json.load(f)
    print('Pipeline Last Run Times:')
    for component, timestamp in status.items():
        print(f'  {component}: {timestamp}')
else:
    print('Pipeline never run - run smart_pipeline_update.py first')
"
```

---

## Storage Considerations

Your data grows over time:

| Data | Size | Frequency |
|------|------|-----------|
| `data/raw/` | ~2-5 GB | Downloads weekly |
| `data/processed/` | ~500 MB | Regenerates weekly |
| `analytics/outputs/` | ~50 MB | Regenerates weekly |
| `models/` | ~100 MB | Updates monthly |

**Total:** ~3-6 GB per update

To save space, old raw data can be deleted after processing:

```bash
# Keep only last 2 weeks of raw data
find data/raw/ -type f -mtime +14 -delete
```

---

## Automation Setup (Linux/Mac)

### Crontab Setup

```bash
# Edit crontab
crontab -e

# Add weekly update (every Monday 6 AM)
0 6 * * 1 cd /Users/souravamseekarmarti/Projects/uk_bus_analytics && /usr/bin/python3 scripts/smart_pipeline_update.py >> logs/auto_update.log 2>&1

# Optional: Monthly full update (1st of month, 3 AM)
0 3 1 * * cd /Users/souravamseekarmarti/Projects/uk_bus_analytics && /usr/bin/python3 scripts/smart_pipeline_update.py --force >> logs/auto_update.log 2>&1
```

### Systemd Timer (Linux)

Create `/etc/systemd/system/bus-analytics-update.service`:

```ini
[Unit]
Description=UK Bus Analytics Pipeline Update
After=network.target

[Service]
Type=oneshot
User=yourusername
WorkingDirectory=/path/to/uk_bus_analytics
ExecStart=/usr/bin/python3 scripts/smart_pipeline_update.py
StandardOutput=append:/path/to/logs/auto_update.log
StandardError=append:/path/to/logs/auto_update.log
```

Create `/etc/systemd/system/bus-analytics-update.timer`:

```ini
[Unit]
Description=Weekly UK Bus Analytics Update
Requires=bus-analytics-update.service

[Timer]
OnCalendar=Mon *-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable bus-analytics-update.timer
sudo systemctl start bus-analytics-update.timer
```

---

## Summary: Recommended Approach

1. **Install smart update script** ✅ (Already created above)

2. **Set up weekly cron job:**
   ```bash
   0 6 * * 1 cd /path/to/uk_bus_analytics && python3 scripts/smart_pipeline_update.py
   ```

3. **Run dashboard continuously:**
   ```bash
   streamlit run dashboard/Home.py
   ```

4. **Manual updates only when:**
   - Major BODS release announced
   - Code changes to pipeline
   - Data issues detected

**Result:** Fresh data weekly, minimal resource usage, always-ready dashboard!

---

## Testing the Smart Update

Test it now:

```bash
# First run (will download everything)
python3 scripts/smart_pipeline_update.py

# Immediate re-run (should skip everything)
python3 scripts/smart_pipeline_update.py

# Force specific component
python3 scripts/smart_pipeline_update.py --component ingestion
```

You should see:
- First run: Downloads all data
- Second run: "No updates needed - all components up-to-date!"
- Force run: Runs only specified component
