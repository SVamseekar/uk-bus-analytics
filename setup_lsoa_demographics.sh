#!/bin/bash
# Master setup script for LSOA demographics fix
# Run this to download and prepare all LSOA-level demographic data

set -e  # Exit on error

echo "========================================"
echo "LSOA DEMOGRAPHICS SETUP"
echo "========================================"
echo ""

# Step 1: Download LSOA demographics from Nomis
echo "[1/3] Downloading LSOA demographics from Nomis API..."
python utils/download_lsoa_demographics.py

if [ $? -ne 0 ]; then
    echo "❌ Download failed. Check your internet connection or download manually."
    exit 1
fi

echo ""
echo "[2/3] Creating LSOA-to-MSOA lookup table..."
python utils/create_lsoa_msoa_lookup.py

if [ $? -ne 0 ]; then
    echo "❌ Lookup creation failed."
    exit 1
fi

echo ""
echo "[3/3] Verifying files..."
echo ""

# Check if files were created
FILES=(
    "data/raw/demographics/age_population_lsoa.csv"
    "data/raw/demographics/claimant_count_lsoa_processed.csv"
    "data/raw/demographics/lsoa_to_msoa_lookup.csv"
)

ALL_FOUND=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "✓ $file ($SIZE)"
    else
        echo "❌ Missing: $file"
        ALL_FOUND=false
    fi
done

echo ""
if [ "$ALL_FOUND" = true ]; then
    echo "========================================"
    echo "✅ SETUP COMPLETE!"
    echo "========================================"
    echo ""
    echo "All LSOA demographic files are ready."
    echo ""
    echo "Next step: Run the pipeline"
    echo "  python run_full_pipeline.py"
    echo ""
else
    echo "========================================"
    echo "⚠️  SETUP INCOMPLETE"
    echo "========================================"
    echo ""
    echo "Some files are missing. Check errors above."
    exit 1
fi
