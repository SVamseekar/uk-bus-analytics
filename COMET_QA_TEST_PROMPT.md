# Senior QA Testing Prompt for Comet AI Browser

**Your Role:** Act as a **Senior QA Testing Engineer** with 10+ years of experience in data analytics dashboard testing, statistical validation, and user acceptance testing for government/transport sector applications.

**Application Under Test:** UK Bus Analytics Dashboard - Coverage & Accessibility Analysis Page
**URL:** http://localhost:8501 (or the deployed URL)
**Page to Test:** Coverage & Accessibility (Category A Analysis)

---

## 🎯 Testing Objectives

Your mission is to comprehensively test the **Coverage & Accessibility** page by:

1. **Data Accuracy Verification** - Validate all displayed metrics against expected ground truth
2. **Filter Combination Testing** - Test ALL filter combinations systematically
3. **Narrative Consistency** - Verify dynamic narratives match the data shown
4. **Ranking & Comparison Logic** - Validate rankings, percentages, and comparative statements
5. **Edge Case Detection** - Identify bugs in single-region vs multi-region views
6. **UI/UX Issues** - Report any confusing, misleading, or broken UI elements

---

## 📊 Ground Truth Data (Source: regional_summary.csv)

### National Baseline Metrics
- **Total Stops:** 779,262
- **Total Population:** 34,826,550
- **Total Routes:** 2,749
- **National Average Stops per 1,000:** 22.38
- **National Average Routes per 100,000:** 7.89

### Regional Data Reference

| Rank | Region | Stops | Stops/1k | Routes | Routes/100k | Population |
|------|--------|-------|----------|--------|-------------|------------|
| 1 | North West England | 173,777 | 25.54 | 539 | 7.92 | 6,802,950 |
| 2 | South West England | 85,232 | 24.34 | 276 | 7.88 | 3,501,300 |
| 3 | Yorkshire and Humber | 117,221 | 23.93 | 326 | 6.65 | 4,898,850 |
| 4 | North East England | 61,012 | 23.21 | 156 | 5.94 | 2,628,450 |
| 5 | West Midlands | 86,586 | 22.39 | 278 | 7.19 | 3,867,600 |
| 6 | **Greater London** | 108,930 | 20.77 | 352 | 6.71 | 5,243,700 |
| 7 | East of England | 37,356 | 19.77 | 325 | 17.20 | 1,889,250 |
| 8 | South East England | 77,038 | 18.62 | 392 | 9.47 | 4,138,200 |
| 9 | East Midlands | 32,110 | 17.30 | 105 | 5.66 | 1,856,250 |

### Routes per 100k Rankings (Descending)
1. **East of England** - 17.20
2. **South East England** - 9.47
3. **North West England** - 7.92
4. **South West England** - 7.88
5. **West Midlands** - 7.19
6. **Greater London** - 6.71 ← **Rank #6 of 9**
7. **Yorkshire and Humber** - 6.65
8. **North East England** - 5.94
9. **East Midlands** - 5.66

---

## 🧪 Test Cases to Execute

### **Test Suite 1: Filter Combinations (30 Total Combinations)**

Test EVERY combination of these filters:

**Geographic Scope (10 options):**
- All Regions
- Yorkshire and Humber
- West Midlands
- East Midlands
- North East England
- South West England
- Greater London
- South East England
- North West England
- East of England

**Urban/Rural (3 options):**
- All
- Urban Only
- Rural Only

**Total Combinations: 10 × 3 = 30 filter combinations**

**Critical Filter Combinations to Test (All 30):**

**Group 1: All Regions**
1. ✅ All Regions + All
2. ✅ All Regions + Urban Only
3. ✅ All Regions + Rural Only

**Group 2: Yorkshire and Humber**
4. ✅ Yorkshire and Humber + All
5. ✅ Yorkshire and Humber + Urban Only
6. ✅ Yorkshire and Humber + Rural Only

**Group 3: West Midlands**
7. ✅ West Midlands + All
8. ✅ West Midlands + Urban Only
9. ✅ West Midlands + Rural Only

**Group 4: East Midlands**
10. ✅ East Midlands + All
11. ✅ East Midlands + Urban Only
12. ✅ East Midlands + Rural Only

**Group 5: North East England**
13. ✅ North East England + All
14. ✅ North East England + Urban Only
15. ✅ North East England + Rural Only

**Group 6: South West England**
16. ✅ South West England + All
17. ✅ South West England + Urban Only
18. ✅ South West England + Rural Only

**Group 7: Greater London**
19. ✅ Greater London + All
20. ✅ Greater London + Urban Only
21. ✅ Greater London + Rural Only

**Group 8: South East England**
22. ✅ South East England + All
23. ✅ South East England + Urban Only
24. ✅ South East England + Rural Only

**Group 9: North West England**
25. ✅ North West England + All
26. ✅ North West England + Urban Only
27. ✅ North West England + Rural Only

**Group 10: East of England**
28. ✅ East of England + All
29. ✅ East of England + Urban Only
30. ✅ East of England + Rural Only

For EACH of the 30 combinations, verify:
- [ ] Active filter label displays correctly
- [ ] Metrics update appropriately
- [ ] Visualizations render without errors
- [ ] No console errors (check browser dev tools)
- [ ] Numbers match expected values from ground truth table

---

### **Test Suite 2: Section A1 - Regional Route Density Analysis**

**Filter: All Regions + All**

Expected Results:
- [ ] Chart shows all 9 regions
- [ ] East of England appears at top (17.20 routes/100k)
- [ ] East Midlands appears at bottom (5.66 routes/100k)
- [ ] Narrative mentions "East of England leads" and "East Midlands operates only"
- [ ] National average cited should be **7.89 routes per 100,000**

---

#### **Test All 9 Regions Individually (Section A1)**

**Filter: Yorkshire and Humber + All**
- [ ] Routes per 100k: **6.65**
- [ ] Total Routes: **326**
- [ ] Population: **4,898,850**
- [ ] Rank: **#7 of 9**
- [ ] vs National Avg: **-15.72%** (calculated: (6.65/7.89 - 1) × 100)
- [ ] Narrative: "Yorkshire and Humber ranks #7 of 9 regions with 6.65 routes per 100k, 15.72% below the national average of 7.89"

**Filter: West Midlands + All**
- [ ] Routes per 100k: **7.19**
- [ ] Total Routes: **278**
- [ ] Population: **3,867,600**
- [ ] Rank: **#5 of 9**
- [ ] vs National Avg: **-8.87%** (calculated: (7.19/7.89 - 1) × 100)
- [ ] Narrative: "West Midlands ranks #5 of 9 regions with 7.19 routes per 100k, 8.87% below the national average of 7.89"

**Filter: East Midlands + All**
- [ ] Routes per 100k: **5.66**
- [ ] Total Routes: **105**
- [ ] Population: **1,856,250**
- [ ] Rank: **#9 of 9** (WORST)
- [ ] vs National Avg: **-28.26%** (calculated: (5.66/7.89 - 1) × 100)
- [ ] Narrative: "East Midlands ranks #9 of 9 regions with 5.66 routes per 100k, 28.26% below the national average of 7.89"

**Filter: North East England + All**
- [ ] Routes per 100k: **5.94**
- [ ] Total Routes: **156**
- [ ] Population: **2,628,450**
- [ ] Rank: **#8 of 9**
- [ ] vs National Avg: **-24.71%** (calculated: (5.94/7.89 - 1) × 100)
- [ ] Narrative: "North East England ranks #8 of 9 regions with 5.94 routes per 100k, 24.71% below the national average of 7.89"

**Filter: South West England + All**
- [ ] Routes per 100k: **7.88**
- [ ] Total Routes: **276**
- [ ] Population: **3,501,300**
- [ ] Rank: **#4 of 9**
- [ ] vs National Avg: **-0.13%** (calculated: (7.88/7.89 - 1) × 100)
- [ ] Narrative: "South West England ranks #4 of 9 regions with 7.88 routes per 100k, 0.13% below the national average of 7.89" (essentially at national avg)

**Filter: Greater London + All**
- [ ] Routes per 100k: **6.71**
- [ ] Total Routes: **352**
- [ ] Population: **5,243,700**
- [ ] Rank: **#6 of 9**
- [ ] vs National Avg: **-14.96%** (calculated: (6.71/7.89 - 1) × 100)
- [ ] Narrative: "Greater London ranks #6 of 9 regions with 6.71 routes per 100k, 14.96% below the national average of 7.89"
- [ ] **CRITICAL:** Should NOT say "ranks #0" or "0% below national average"

**Filter: South East England + All**
- [ ] Routes per 100k: **9.47**
- [ ] Total Routes: **392**
- [ ] Population: **4,138,200**
- [ ] Rank: **#2 of 9**
- [ ] vs National Avg: **+20.03%** (calculated: (9.47/7.89 - 1) × 100)
- [ ] Narrative: "South East England ranks #2 of 9 regions with 9.47 routes per 100k, 20.03% above the national average of 7.89"

**Filter: North West England + All**
- [ ] Routes per 100k: **7.92**
- [ ] Total Routes: **539**
- [ ] Population: **6,802,950**
- [ ] Rank: **#3 of 9**
- [ ] vs National Avg: **+0.38%** (calculated: (7.92/7.89 - 1) × 100)
- [ ] Narrative: "North West England ranks #3 of 9 regions with 7.92 routes per 100k, 0.38% above the national average of 7.89"

**Filter: East of England + All**
- [ ] Routes per 100k: **17.20** (HIGHEST - ANOMALY!)
- [ ] Total Routes: **325**
- [ ] Population: **1,889,250**
- [ ] Rank: **#1 of 9** (BEST)
- [ ] vs National Avg: **+117.87%** (calculated: (17.20/7.89 - 1) × 100)
- [ ] Narrative: "East of England ranks #1 of 9 regions with 17.20 routes per 100k, 117.87% above the national average of 7.89"
- [ ] **NOTE:** This is an outlier - verify if data is correct or if there's a data quality issue

**CRITICAL BUG CHECK (All Regions):**
- [ ] Verify narrative does NOT compare region to itself
- [ ] Percentage vs national should NOT be 0% (unless region value exactly equals 7.89)
- [ ] Rank should NOT be #0
- [ ] National average should ALWAYS be 7.89 in single-region view

---

### **Test Suite 3: Section A2 - Regional Stop Coverage Analysis**

**Filter: All Regions + All**

Expected Results:
- [ ] Chart shows all 9 regions
- [ ] North West England at top (25.54 stops/1k)
- [ ] East Midlands at bottom (17.30 stops/1k)
- [ ] National average should be **22.38 stops per 1,000**

---

#### **Test All 9 Regions Individually (Section A2)**

**Filter: Yorkshire and Humber + All**
- [ ] Stops per 1,000: **23.93**
- [ ] Total Stops: **117,221**
- [ ] Population: **4,898,850**
- [ ] Rank: **#3 of 9**
- [ ] vs National Avg: **+6.93%** (calculated: (23.93/22.38 - 1) × 100)
- [ ] Narrative: "Yorkshire and Humber ranks #3 of 9 regions with 23.93 stops per 1,000 population, 6.93% above the national average of 22.38"

**Filter: West Midlands + All**
- [ ] Stops per 1,000: **22.39**
- [ ] Total Stops: **86,586**
- [ ] Population: **3,867,600**
- [ ] Rank: **#5 of 9**
- [ ] vs National Avg: **+0.04%** (calculated: (22.39/22.38 - 1) × 100)
- [ ] Narrative: "West Midlands ranks #5 of 9 regions with 22.39 stops per 1,000 population, essentially at the national average of 22.38"

**Filter: East Midlands + All**
- [ ] Stops per 1,000: **17.30**
- [ ] Total Stops: **32,110**
- [ ] Population: **1,856,250**
- [ ] Rank: **#9 of 9** (WORST)
- [ ] vs National Avg: **-22.70%** (calculated: (17.30/22.38 - 1) × 100)
- [ ] Narrative: "East Midlands ranks #9 of 9 regions with 17.30 stops per 1,000 population, 22.70% below the national average of 22.38"

**Filter: North East England + All**
- [ ] Stops per 1,000: **23.21**
- [ ] Total Stops: **61,012**
- [ ] Population: **2,628,450**
- [ ] Rank: **#4 of 9**
- [ ] vs National Avg: **+3.71%** (calculated: (23.21/22.38 - 1) × 100)
- [ ] Narrative: "North East England ranks #4 of 9 regions with 23.21 stops per 1,000 population, 3.71% above the national average of 22.38"

**Filter: South West England + All**
- [ ] Stops per 1,000: **24.34**
- [ ] Total Stops: **85,232**
- [ ] Population: **3,501,300**
- [ ] Rank: **#2 of 9**
- [ ] vs National Avg: **+8.76%** (calculated: (24.34/22.38 - 1) × 100)
- [ ] Narrative: "South West England ranks #2 of 9 regions with 24.34 stops per 1,000 population, 8.76% above the national average of 22.38"

**Filter: Greater London + All**
- [ ] Stops per 1,000: **20.77**
- [ ] Total Stops: **108,930**
- [ ] Population: **5,243,700**
- [ ] Rank: **#6 of 9**
- [ ] vs National Avg: **-7.19%** (calculated: (20.77/22.38 - 1) × 100)
- [ ] Narrative: "Greater London ranks #6 of 9 regions with 20.77 stops per 1,000 population, 7.19% below the national average of 22.38"
- [ ] **CRITICAL:** Should NOT say "ranks #0" or "0% vs national average"

**Filter: South East England + All**
- [ ] Stops per 1,000: **18.62**
- [ ] Total Stops: **77,038**
- [ ] Population: **4,138,200**
- [ ] Rank: **#8 of 9**
- [ ] vs National Avg: **-16.82%** (calculated: (18.62/22.38 - 1) × 100)
- [ ] Narrative: "South East England ranks #8 of 9 regions with 18.62 stops per 1,000 population, 16.82% below the national average of 22.38"

**Filter: North West England + All**
- [ ] Stops per 1,000: **25.54**
- [ ] Total Stops: **173,777**
- [ ] Population: **6,802,950**
- [ ] Rank: **#1 of 9** (BEST)
- [ ] vs National Avg: **+14.12%** (calculated: (25.54/22.38 - 1) × 100)
- [ ] Narrative: "North West England ranks #1 of 9 regions with 25.54 stops per 1,000 population, 14.12% above the national average of 22.38"

**Filter: East of England + All**
- [ ] Stops per 1,000: **19.77**
- [ ] Total Stops: **37,356**
- [ ] Population: **1,889,250**
- [ ] Rank: **#7 of 9**
- [ ] vs National Avg: **-11.66%** (calculated: (19.77/22.38 - 1) × 100)
- [ ] Narrative: "East of England ranks #7 of 9 regions with 19.77 stops per 1,000 population, 11.66% below the national average of 22.38"

**CRITICAL BUG CHECK (All Regions):**
- [ ] National average should ALWAYS be **22.38 stops per 1,000** in single-region view
- [ ] Rank should NOT be #0
- [ ] Percentage should NOT be 0% (unless exactly 22.38)
- [ ] Narrative should compare to ALL 9 regions, not to itself

---

### **Test Suite 4: Section A3 - High-Density Underserved Areas**

**Filter: All Regions + All**
- [ ] Should show scatter plot or analysis of multiple regions
- [ ] Should display correlation analysis if available

**Filter: Greater London + All**
- [ ] Should show message: "Note: Population-service mismatch analysis is only available in 'All Regions' comparison mode"
- [ ] Should NOT attempt to show scatter plot with 1 data point
- [ ] Should explain that multiple regions are needed

---

### **Test Suite 5: Section A4 - Stop Coverage Distribution**

**Filter: Greater London + All**

Expected Results:
- [ ] **Total LSOAs Analyzed:** Should be ~3,178 (Greater London LSOAs)
- [ ] **LSOAs with Zero Stops:** Should be low (check exact number)
- [ ] **Avg Stops per LSOA:** Calculate from 108,930 stops / 3,178 LSOAs ≈ 34.3
- [ ] Population stats should sum to ~5.24 million

**Filter: All Regions + All**
- [ ] Should aggregate across all England (33,755 LSOAs total)
- [ ] Total population should be ~34.8 million

---

### **Test Suite 6: Section A5 - Walking Distance Analysis**

**Filter: Greater London + All**

Verify:
- [ ] Shows distance distribution for London LSOAs only
- [ ] Reports LSOAs within 400m standard
- [ ] Median distance makes sense (typically 200-400m in urban areas)
- [ ] Maximum distance is reasonable (not absurdly high like 50km)

**Filter: All Regions + All**
- [ ] Shows national aggregated statistics
- [ ] DfT 400m standard compliance is calculated

---

### **Test Suite 7: Section A6 - Accessibility Standard Compliance**

**Filter: All Regions + All**

Expected:
- [ ] Shows compliance by region (bar chart or table)
- [ ] Lists which regions meet/fail the 400m DfT standard
- [ ] National summary shows % of LSOAs within 400m

**Filter: Greater London + All**
- [ ] Shows London-specific compliance
- [ ] Reports % of London LSOAs meeting standard
- [ ] Should show green ✅ if >50% compliance

---

### **Test Suite 8: Section A7 - Urban-Rural Coverage Disparity**

**Filter: All Regions + All**

Expected:
- [ ] Shows urban vs rural average stops/1000
- [ ] Calculates disparity ratio (urban/rural)
- [ ] Narrative interprets if ratio > 1.5x is "significant disparity"

**Filter: Greater London + All**
- [ ] Should show London's urban vs rural breakdown
- [ ] May show "not enough rural areas for comparison" if London is highly urbanized

**Filter: All Regions + Rural Only**
- [ ] Shows only rural area statistics
- [ ] Recalculates metrics excluding urban LSOAs

---

### **Test Suite 9: Section A8 - Population-Service Mismatch Zones**

**Filter: All Regions + All**
- [ ] Should show regions with high population but low service
- [ ] Uses correlation or scoring methodology

**Filter: Greater London + All**
- [ ] Should show similar message to A3: "only available in All Regions mode"
- [ ] Should NOT crash or show empty chart

---

## 🐛 Known Bugs to Verify Are FIXED

### Bug #1: Single-Region Self-Comparison (FIXED)
**Symptom:** When filtering to "Greater London", narratives showed:
- "Greater London ranks #0 of 9 regions"
- "0% below the national average"
- National average = London's own value

**Verification:**
- [ ] Filter to "Greater London + All"
- [ ] Go to Section A1
- [ ] Verify narrative shows: "Greater London ranks #6 of 9 regions"
- [ ] Verify: "14.96% below the national average of 7.89 routes per 100k"
- [ ] National average should be 7.89, NOT 6.71

**If bug still exists:** Report with screenshots showing the incorrect rank/percentage

---

## 📋 Testing Checklist

### Data Validation
- [ ] All displayed numbers match ground truth data
- [ ] Rankings are mathematically correct
- [ ] Percentages vs national average are calculated correctly: `((region_value / national_avg) - 1) × 100`
- [ ] Population figures match source data

### Narrative Validation
- [ ] Narratives dynamically update based on filters
- [ ] Comparative statements (best/worst) are accurate
- [ ] Single-region narratives compare against ALL regions, not itself
- [ ] Investment calculations use HM Treasury Green Book methodology
- [ ] BCR (Benefit-Cost Ratio) is calculated correctly

### UI/UX Issues
- [ ] No visual glitches or overlapping elements
- [ ] Charts render correctly without cutoff text
- [ ] Filter changes trigger immediate UI updates
- [ ] Loading states are shown for slow operations
- [ ] No broken images or missing icons

### Performance
- [ ] Page loads within 5 seconds
- [ ] Filter changes respond within 2 seconds
- [ ] No browser console errors
- [ ] No memory leaks with repeated filter changes

### Edge Cases
- [ ] Switching rapidly between filters doesn't break state
- [ ] Selecting "Urban Only" for rural-heavy regions shows appropriate message
- [ ] Sections that require multi-region data show proper warnings for single-region filters

---

## 📝 Bug Report Format

For each bug found, report using this format:

```
**Bug ID:** BUG-001
**Severity:** Critical / High / Medium / Low
**Component:** Section A1 / Filters / Narrative / etc.

**Filter Combination:**
- Geographic Scope: [e.g., Greater London]
- Urban/Rural: [e.g., All]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Steps to Reproduce:**
1. Navigate to Coverage & Accessibility page
2. Select filter: [details]
3. Scroll to section: [details]
4. Observe: [issue]

**Supporting Evidence:**
- Screenshot: [if applicable]
- Console errors: [if applicable]
- Incorrect values: Expected X, Got Y

**Impact:**
[How this affects users/decision-makers]
```

---

## 🎯 Key Testing Scenarios

### **Scenario 1: Policy Maker Reviewing London**
**User Story:** A London Transport official wants to see how London compares to other regions.

**Test:**
1. Filter to "Greater London + All"
2. Review A1 and A2 sections
3. Verify: Rank #6, ~15% below national average for routes, ~7% below for stops
4. Verify: Investment recommendations are specific to London

**Expected Outcome:** User gets accurate comparative analysis showing London's underperformance vs national average

---

### **Scenario 2: National Transport Analyst**
**User Story:** DfT analyst comparing all regions to identify investment priorities.

**Test:**
1. Set filter to "All Regions + All"
2. Review all sections A1-A8
3. Verify: Rankings show East Midlands and North East as lowest performers
4. Verify: Recommendations mention specific regions needing investment

**Expected Outcome:** Clear national overview with actionable insights

---

### **Scenario 3: Urban vs Rural Comparison**
**User Story:** Researcher studying urban-rural service disparities.

**Test:**
1. Set filter to "All Regions + Urban Only" → Note metrics
2. Change to "All Regions + Rural Only" → Note metrics
3. Compare: Urban should have higher stops/1k (typically 1.5-2x rural)

**Expected Outcome:** Clear disparity shown, narrative explains policy implications

---

## 🚨 Critical Acceptance Criteria

The dashboard PASSES QA if:
- ✅ All displayed metrics ±2% of ground truth (accounting for rounding)
- ✅ Rankings are 100% correct
- ✅ Single-region narratives compare against full national dataset
- ✅ No console errors during normal usage
- ✅ All 18 filter combinations work without crashes
- ✅ Sections requiring multi-region data gracefully handle single-region filters

The dashboard FAILS QA if:
- ❌ Any metric differs by >5% from ground truth
- ❌ Rankings are incorrect
- ❌ Narratives compare regions to themselves (Bug #1 regression)
- ❌ Any section crashes or shows blank output
- ❌ Console shows critical errors

---

## 🤖 Instructions for Comet AI Browser

**Your Task:**
1. Navigate to the URL provided (http://localhost:8501 or deployed URL)
2. Go to the "Coverage Accessibility" page
3. Systematically test each filter combination listed above
4. For each test case, verify the expected results
5. Take screenshots of any discrepancies
6. Check browser console for errors (F12 → Console tab)
7. Report ALL findings in the bug report format above

**Focus Areas:**
- **Data Accuracy** (highest priority)
- **Greater London filter** (recently fixed, verify fix works)
- **Narrative consistency** with displayed numbers
- **Edge cases** (single region vs all regions)

**Deliverables:**
- Complete test execution report with pass/fail for each test case
- Bug reports for any failed tests
- Summary assessment: "Ready for Production" or "Requires Fixes"

---

## 📞 Questions to Answer

After testing, provide answers to:

1. **Does Greater London show correct rank #6 when filtered?** (Not #0)
2. **Is the national average always 7.89 routes/100k and 22.38 stops/1k in single-region view?**
3. **Do rankings match the ground truth table provided?**
4. **Are there any sections that crash or show empty output?**
5. **Do urban/rural filters produce meaningful different results?**
6. **Are investment recommendations reasonable and data-driven?**
7. **Overall assessment: Is the dashboard production-ready?**

---

**Good luck with the testing! Be thorough, be critical, and help us deliver a world-class analytics dashboard for UK bus services.** 🚌📊
