# Quick Directory Reference

## 📁 Where to Find Everything

| What You Need | Location | Description |
|--------------|----------|-------------|
| **Documentation** | `docs/` | All project docs, guides, reports |
| **Quick Start** | `docs/QUICKSTART.md` | Get started in 15 minutes |
| **Project Structure** | `docs/PROJECT_STRUCTURE.md` | Detailed structure guide |
| **Pipeline Code** | `data_pipeline/` | ETL scripts (01-04) |
| **Analytics** | `analytics/` | Analysis scripts & results |
| **Dashboard** | `dashboard/app.py` | Web interface |
| **Tests** | `tests/` | All test files |
| **Scripts** | `scripts/` | Operational utilities |
| **Large Data** | `data/` | CSV files, reports |
| **Logs** | `logs/` | Application logs |

## 🚀 Common Commands

```bash
# Check pipeline status
./scripts/status.sh

# Run dashboard
./scripts/run_dashboard.sh

# Run data pipeline
python data_pipeline/01_data_ingestion.py
python data_pipeline/02_data_processing.py
python data_pipeline/03_data_validation.py

# Run analytics
python analytics/descriptive_analysis.py
python analytics/05_correlation_analysis.py

# Run tests
pytest tests/

# Check downloads
python scripts/check_downloads.py
```

## 📊 Directory Structure

```
uk_bus_analytics/
├── analytics/              # Analysis & insights
├── config/                 # Settings & configs
├── dashboard/              # Web dashboard
├── data/                   # Large data files
├── data_pipeline/          # ETL pipeline
├── docs/                   # Documentation hub
│   ├── guides/            # User guides
│   └── reports/           # Status reports
├── logs/                   # Application logs
├── notebooks/              # Jupyter notebooks
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── utils/                  # Helper functions
└── visualizations/         # Charts & maps
```

## 📖 Documentation Map

- **Getting Started**: `docs/QUICKSTART.md`
- **Structure Guide**: `docs/PROJECT_STRUCTURE.md`
- **Reorganization Details**: `docs/REORGANIZATION_SUMMARY.md`
- **Analytics Guide**: `docs/ANALYTICS_GUIDE.md`
- **Launch Instructions**: `docs/LAUNCH_INSTRUCTIONS.md`
- **Manual Download**: `docs/guides/MANUAL_DOWNLOAD_GUIDE.md`

## 🎯 Quick Tips

- All scripts should be run from project root
- Documentation is organized by purpose in `docs/`
- Tests are in `tests/`, not root
- Scripts are in `scripts/`, not root
- Large data files go in `data/`, not root

For detailed information, see `docs/PROJECT_STRUCTURE.md`
