#!/bin/bash
# UK Bus Analytics - Dashboard Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to project root (parent of scripts/)
cd "$SCRIPT_DIR/.."

echo "🚌 UK Bus Analytics Dashboard"
echo "=============================="
echo ""
echo "Starting Streamlit dashboard..."
echo "Access at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

source venv/bin/activate
streamlit run dashboard/app.py
