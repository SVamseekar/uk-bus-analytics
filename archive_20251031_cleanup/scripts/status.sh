#!/bin/bash
# Quick status check script

echo "=================================="
echo "UK Bus Analytics - Quick Status"
echo "=================================="
echo ""

echo "📊 Data Files:"
echo "  Raw regions: $(find data_pipeline/raw/regions -name '*.zip' -o -name '*.xml' 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Demographic: $(find data_pipeline/raw/demographic -name '*.csv' 2>/dev/null | wc -l | tr -d ' ') datasets"
echo ""

echo "✅ Processed Data:"
if [ -d "data_pipeline/processed/regions" ]; then
    for region in data_pipeline/processed/regions/*/; do
        if [ -d "$region" ]; then
            region_name=$(basename "$region")
            stops_file="${region}${region_name}_stops_cleaned.csv"
            routes_file="${region}${region_name}_routes.csv"

            stops_count=0
            routes_count=0

            if [ -f "$stops_file" ]; then
                stops_count=$(wc -l < "$stops_file" 2>/dev/null | tr -d ' ')
                stops_count=$((stops_count - 1))  # Subtract header
            fi

            if [ -f "$routes_file" ]; then
                routes_count=$(wc -l < "$routes_file" 2>/dev/null | tr -d ' ')
                routes_count=$((routes_count - 1))  # Subtract header
            fi

            if [ $stops_count -gt 0 ] || [ $routes_count -gt 0 ]; then
                echo "  ✓ $region_name: $stops_count stops, $routes_count routes"
            fi
        fi
    done
else
    echo "  ⚠ No processed data yet"
fi

echo ""
echo "📝 Recent Logs:"
if [ -d "logs" ]; then
    latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        echo "  Latest: $(basename "$latest_log")"
        log_size=$(du -h "$latest_log" | cut -f1)
        echo "  Size: $log_size"
    fi
fi

echo ""
echo "💾 Git Status:"
git status -s | head -5
unpushed=$(git log origin/main..HEAD 2>/dev/null | grep -c "^commit")
if [ $unpushed -gt 0 ]; then
    echo "  ⚠ $unpushed unpushed commits"
fi

echo ""
echo "To run full status check: python3 tests/test_pipeline_status.py"
echo "To run processing: python3 data_pipeline/02_data_processing.py"
