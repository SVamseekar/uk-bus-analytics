# Quick Start: Comet AI Testing Instructions

## 🎯 Your Mission
Test the **Coverage & Accessibility** page at http://localhost:8501

Act as a Senior QA Engineer. Test all filter combinations, verify data accuracy, and report bugs.

---

## 🔢 Ground Truth (Verify Against These Numbers)

**National Averages:**
- Routes per 100k: **7.89**
- Stops per 1,000: **22.38**

**All 9 Regions - Expected Values:**

| Region | Routes/100k | Rank A1 | Stops/1k | Rank A2 | Population |
|--------|-------------|---------|----------|---------|------------|
| East of England | 17.20 | #1 | 19.77 | #7 | 1,889,250 |
| South East England | 9.47 | #2 | 18.62 | #8 | 4,138,200 |
| North West England | 7.92 | #3 | 25.54 | #1 | 6,802,950 |
| South West England | 7.88 | #4 | 24.34 | #2 | 3,501,300 |
| West Midlands | 7.19 | #5 | 22.39 | #5 | 3,867,600 |
| **Greater London** | **6.71** | **#6** | **20.77** | **#6** | **5,243,700** |
| Yorkshire and Humber | 6.65 | #7 | 23.93 | #3 | 4,898,850 |
| North East England | 5.94 | #8 | 23.21 | #4 | 2,628,450 |
| East Midlands | 5.66 | #9 | 17.30 | #9 | 1,856,250 |

---

## ✅ Test Plan (30 Combinations)

### For EACH of these 30 filter combinations:

**10 Geographic Scopes:**
1. All Regions
2. Yorkshire and Humber
3. West Midlands
4. East Midlands
5. North East England
6. South West England
7. Greater London
8. South East England
9. North West England
10. East of England

**× 3 Urban/Rural Options:**
- All
- Urban Only
- Rural Only

### What to Check:

#### Section A1: Routes per 100k
- [ ] Displayed value matches table above
- [ ] Rank shown matches "Rank A1" column
- [ ] % vs national avg = `(region_value / 7.89 - 1) × 100`
- [ ] Narrative mentions rank and percentage
- [ ] Chart renders correctly

**Example for Greater London:**
```
✅ Routes per 100k: 6.71
✅ Total Routes: 352
✅ Population: 5,243,700
✅ Rank: "#6 of 9 regions"
✅ vs National Avg: -14.96% (calculated: (6.71/7.89-1)×100)
✅ Narrative: "Greater London ranks #6 of 9 regions with 6.71 routes per 100,000 population. This is 14.96% below the national average of 7.89 routes per 100,000."
```

❌ **BUG if you see:**
- Rank #0 or #1 (should be #6)
- 0% vs national avg (should be -14.96%)
- National avg = 6.71 (should be 7.89)
- "Greater London ranks #0 of 9 regions"

#### Section A2: Stops per 1,000
- [ ] Displayed value matches table above
- [ ] Rank shown matches "Rank A2" column
- [ ] % vs national avg = `(region_value / 22.38 - 1) × 100`
- [ ] Narrative mentions rank and percentage
- [ ] Chart renders correctly

**Example for Greater London:**
```
✅ Stops per 1,000: 20.77
✅ Total Stops: 108,930
✅ Population: 5,243,700
✅ Rank: "#6 of 9 regions"
✅ vs National Avg: -7.19% (calculated: (20.77/22.38-1)×100)
✅ Narrative: "Greater London ranks #6 of 9 regions with 20.77 stops per 1,000 population. This is 7.19% below the national average of 22.38 stops per 1,000."
```

#### Section A3-A8: Other Sections
- [ ] No crashes or blank outputs
- [ ] Single-region filters show appropriate messages for sections requiring multi-region data
- [ ] Charts render without errors
- [ ] LSOA statistics are reasonable

---

## 🐛 Critical Bug to Verify is FIXED

**Bug:** Single-region filters compared region to itself (showing rank #0, 0% vs national avg)

**Test:** Select "Greater London + All"
- ✅ PASS: Shows rank #6, -14.96% vs national avg 7.89
- ❌ FAIL: Shows rank #0, 0% vs national avg 6.71

---

## 📋 How to Execute

1. **Navigate:** Open http://localhost:8501 → Go to "Coverage Accessibility" page
2. **Test systematically:**
   - Start with "All Regions + All"
   - Then test each region individually with "All"
   - Then test urban/rural variants
3. **For each filter:**
   - Screenshot the page
   - Note displayed metrics
   - Compare to ground truth table
   - Check console for errors (F12)
4. **Report bugs:** Use format below

---

## 🚨 Bug Report Format

```
BUG-XXX: [Short title]
Severity: Critical/High/Medium/Low
Filter: [Geographic Scope] + [Urban/Rural]
Section: A1/A2/A3/etc.

Expected: [from ground truth table]
Actual: [what dashboard shows]

Screenshot: [attach]
Console errors: [if any]

Impact: [how this affects users]
```

---

## ✅ Success Criteria

**PASS if:**
- All metrics ±2% of ground truth (rounding acceptable)
- All rankings 100% correct
- Single-region views compare against full 9-region dataset
- No console errors
- All 30 filter combinations work

**FAIL if:**
- Any metric >5% different from ground truth
- Wrong rankings
- Self-comparison bug (rank #0, 0%)
- Crashes or blank sections

---

## 📊 Priority Test Cases

**HIGH PRIORITY (Test First):**
1. ✅ All Regions + All (baseline)
2. ✅ Greater London + All (recently fixed bug)
3. ✅ East Midlands + All (worst performer - #9 both metrics)
4. ✅ East of England + All (best routes/100k - potential outlier)
5. ✅ North West England + All (best stops/1k)

**MEDIUM PRIORITY:**
6-15. All other single regions with "All" filter

**LOW PRIORITY:**
16-30. Urban/Rural variants

---

## 🤖 Final Deliverable

Provide:
1. **Summary:** X of 30 tests passed
2. **Bug List:** All bugs found with screenshots
3. **Recommendation:** Production-ready? Yes/No
4. **Data Quality Issues:** Flag East of England outlier (17.20 routes/100k is 2.4x higher than nearest region)

---

**Ready? Start testing!** 🚀
