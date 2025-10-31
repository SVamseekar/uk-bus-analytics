#!/bin/bash
# Script to safely merge data/raw/transport/ into data/raw/regions/
# Identifies duplicates and moves only unique files

set -e

echo "=========================================="
echo "Transport to Regions Merge Analysis"
echo "=========================================="
echo ""

REGIONS=("yorkshire" "west_midlands" "east_midlands" "north_east" "south_west" "london" "south_east" "north_west" "east_england")

TOTAL_DUPLICATES=0
TOTAL_UNIQUE=0
TOTAL_MOVED=0

for region in "${REGIONS[@]}"; do
    echo "=== Region: $region ==="

    TRANSPORT_DIR="data/raw/transport/$region"
    REGIONS_DIR="data/raw/regions/$region"

    if [ ! -d "$TRANSPORT_DIR" ]; then
        echo "  ⚠️  Transport directory not found, skipping..."
        continue
    fi

    if [ ! -d "$REGIONS_DIR" ]; then
        echo "  ℹ️  Regions directory doesn't exist, creating..."
        mkdir -p "$REGIONS_DIR"
    fi

    DUPLICATES=0
    UNIQUE=0
    MOVED=0

    # Check each file in transport
    shopt -s nullglob
    for file in "$TRANSPORT_DIR"/*.zip; do
        if [ ! -f "$file" ]; then
            continue
        fi

        filename=$(basename "$file")

        if [ -f "$REGIONS_DIR/$filename" ]; then
            # File exists in both - it's a duplicate
            echo "  🔄 Duplicate: $filename"
            DUPLICATES=$((DUPLICATES + 1))
        else
            # File only in transport - move it
            echo "  ➡️  Moving unique file: $filename"
            cp "$file" "$REGIONS_DIR/$filename"
            MOVED=$((MOVED + 1))
            UNIQUE=$((UNIQUE + 1))
        fi
    done

    echo "  📊 Summary: $DUPLICATES duplicates, $UNIQUE unique files moved"
    echo ""

    TOTAL_DUPLICATES=$((TOTAL_DUPLICATES + DUPLICATES))
    TOTAL_UNIQUE=$((TOTAL_UNIQUE + UNIQUE))
    TOTAL_MOVED=$((TOTAL_MOVED + MOVED))
done

echo "=========================================="
echo "Overall Summary"
echo "=========================================="
echo "Total duplicates found: $TOTAL_DUPLICATES"
echo "Total unique files moved: $TOTAL_UNIQUE"
echo ""

if [ $TOTAL_MOVED -gt 0 ]; then
    echo "✅ Successfully merged $TOTAL_MOVED unique files from transport/ to regions/"
    echo ""
    echo "Next step: Verify the merge and then delete data/raw/transport/"
    echo "Command: rm -rf data/raw/transport/"
else
    echo "ℹ️  All files were duplicates. Safe to delete data/raw/transport/"
    echo "Command: rm -rf data/raw/transport/"
fi
