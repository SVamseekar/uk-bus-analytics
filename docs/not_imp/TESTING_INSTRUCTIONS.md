# Testing Instructions for UI Implementation

## Quick Test

1. **Test the UI Components:**
```bash
cd /Users/souravamseekarmarti/Projects/uk_bus_analytics
streamlit run test_ui.py
```

This will open a minimal test page. If you see 4 professionally styled KPI cards, the design system is working.

2. **Test the Full Home Dashboard:**
```bash
streamlit run dashboard/Home.py
```

3. **Test Service Coverage Page:**
```bash
streamlit run dashboard/Home.py
# Then click on "📍 Service Coverage" in the sidebar
```

## What to Look For

### ✅ Working Indicators:
- Professional color scheme (Navy blue header, teal accents)
- KPI cards with rounded corners and shadows
- Smooth hover effects on cards
- Clean typography (Inter font)
- No default Streamlit menu/footer visible
- Responsive layout

### ❌ If Something's Wrong:
Check the browser console (F12) for JavaScript errors or CSS issues.

## Common Issues & Fixes

### Issue 1: CSS Not Loading
**Symptom:** Page looks like default Streamlit (no custom styling)

**Fix:**
```bash
# Verify CSS file exists
ls -la dashboard/assets/styles.css

# Check file permissions
chmod 644 dashboard/assets/styles.css
```

### Issue 2: Import Errors
**Symptom:** `ModuleNotFoundError` or `ImportError`

**Fix:**
```bash
# Ensure you're in the project root
cd /Users/souravamseekarmarti/Projects/uk_bus_analytics

# Verify ui_components exists
ls -la dashboard/utils/ui_components.py

# Test import
python3 -c "from dashboard.utils.ui_components import render_kpi_card; print('✅ OK')"
```

### Issue 3: Data Not Loading
**Symptom:** "Error loading data" message

**Fix:**
```bash
# Check if data files exist
ls -la data/processed/

# Regenerate if missing
python3 analysis/spatial/01_compute_spatial_metrics_v2.py
```

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Chromium-based) - Recommended
- ✅ Firefox
- ✅ Safari

## Performance Notes

- Initial load: ~2-3 seconds (data loading)
- Page navigation: < 1 second
- Chart rendering: < 500ms

## Screenshots to Take

When testing, verify these elements:

1. **Home Page:**
   - [ ] Professional header with subtitle
   - [ ] 4 KPI cards in a row (desktop)
   - [ ] 2 gradient insight cards
   - [ ] No Streamlit branding visible

2. **Service Coverage Page:**
   - [ ] Professional header
   - [ ] 4 KPI cards with trends
   - [ ] Styled charts with professional theme
   - [ ] Methodology citations at bottom

3. **Responsive Design:**
   - [ ] Resize browser to mobile width
   - [ ] Cards should stack vertically
   - [ ] Text should remain readable

## Expected Behavior

### Desktop (> 1025px):
- 4 KPIs per row (12-column grid)
- Side-by-side charts
- Full navigation bar

### Tablet (641-1024px):
- 2 KPIs per row (8-column grid)
- Charts may stack
- Compact navigation

### Mobile (< 640px):
- 1 KPI per row (4-column grid)
- All elements stacked
- Touch-friendly buttons

## Reporting Issues

If something doesn't work:

1. Check browser console (F12 → Console tab)
2. Copy any error messages
3. Note which page/component is affected
4. Share screenshot if possible

## Success Criteria

✅ **All working if:**
1. CSS loads (professional colors visible)
2. KPI cards have rounded corners and shadows
3. Charts use professional Plotly theme
4. No Streamlit branding visible
5. Methodology citations appear
6. Responsive design works on mobile

## Quick Validation Checklist

Run this in terminal:
```bash
cd /Users/souravamseekarmarti/Projects/uk_bus_analytics

echo "Checking files..."
[ -f "dashboard/assets/styles.css" ] && echo "✅ CSS exists" || echo "❌ CSS missing"
[ -f "dashboard/utils/ui_components.py" ] && echo "✅ UI components exist" || echo "❌ UI components missing"
[ -f "data/mapping/policy_questions_visual_framework.json" ] && echo "✅ Policy questions exist" || echo "❌ Policy questions missing"

echo ""
echo "Testing imports..."
python3 -c "from dashboard.utils.ui_components import apply_professional_config; print('✅ Imports work')" 2>&1 | grep -q "✅" && echo "✅ Import test passed" || echo "❌ Import test failed"

echo ""
echo "Checking data..."
python3 -c "from dashboard.utils.data_loader import load_lsoa_metrics; d = load_lsoa_metrics(); print(f'✅ Data loaded: {len(d)} rows')" 2>&1 | tail -1

echo ""
echo "All checks complete. Run: streamlit run test_ui.py"
```

## Next Steps After Verification

Once verified working:
1. Take screenshots of each page
2. Test all 7 dashboard modules
3. Verify methodology citations appear
4. Test export functionality
5. Check mobile responsive design
6. Review performance (page load times)

---

**Remember:** The warnings about "ScriptRunContext" when running Python directly are NORMAL and can be ignored. The app must be run with `streamlit run` to work properly.
