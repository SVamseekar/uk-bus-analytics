#!/bin/bash
# UK Bus Analytics Dashboard Launcher
# Ensures the dashboard runs from the correct directory

cd "$(dirname "$0")/dashboard"
echo "Starting UK Bus Analytics Dashboard..."
echo "Directory: $(pwd)"
echo ""
echo "Dashboard will be available at: http://localhost:8501"
echo ""

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run Streamlit
streamlit run Home.py --server.headless=false

