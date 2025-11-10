# ML Models - Numbers at a Glance

**Quick Reference Card for Dashboards and Reports**

---

## 📊 The Big Numbers

### Model 1: Route Clustering
```
198 route types found
5,822 routes analyzed
249,222 routes available in full dataset
```

**Largest Clusters:**
- Low-Frequency Local Feeders: **915 routes** (15.7%)
- Suburban Connectors: **412 routes** (7.1%)
- Rural Medium-Distance: **387 routes** (6.6%)

---

### Model 2: Service Gap Detection

```
9,573 LSOAs analyzed
1,436 anomalies found (15.0%)
  ├─ 571 UNDER-served (5.97%) ← TRUE SERVICE GAPS
  └─ 865 OVER-served (9.03%) ← INVESTMENT SUCCESS
```

#### The 571 Under-Served Areas (Service Gaps)

**People Affected:**
```
1,120,740 people live in under-served areas
```

**By Gap Type:**
```
217  Deprived Area Gaps      (38.0%)  →  371,033 people
167  High-Population Gaps    (29.2%)  →  424,611 people
99   High-Dependency Gaps    (17.3%)  →  161,388 people
75   Other Service Gaps      (13.1%)  →  142,994 people
13   Elderly Access Gaps     (2.3%)   →   20,714 people
```

**By Severity:**
```
142  Critical (bus deserts)  <1.0 stop/1000  →  281,214 people
200  Severe                  1-2 stops/1000  →  396,761 people
136  Moderate                2-3 stops/1000  →  265,250 people
93   Mild                    3+ stops/1000   →  177,515 people
```

**National Benchmark:**
```
3.65  stops per 1,000 people (median)
3.97  stops per 1,000 people (mean)
1.80  stops per 1,000 in gap areas (mean)
```

---

### Model 3: Coverage Prediction

```
R² = 0.089  →  Explains 8.9% of coverage variation
           →  91.1% is POLICY-DRIVEN (not demographics!)
```

**Prediction Error:**
```
±2.20  stops/1000 (typical error)
±4.40  stops/1000 (95% confidence interval)
```

**Feature Importance (What Drives Coverage?):**
```
34.1%  Elderly population
23.2%  Car ownership
22.1%  Deprivation (IMD)
9.7%   Population density
9.0%   Total population
1.5%   IMD decile
0.5%   Urban/rural  ← Almost no effect!
```

---

## 🎯 Quick Comparisons

### Bus Desert vs Normal Area

| Metric | Bus Desert | Normal Area | Gap |
|--------|------------|-------------|-----|
| Stops/1000 | 0.29 | 3.65 | **12.6x difference** |
| Example (3,000 pop) | 1 stop | 11 stops | Need 10 more stops |
| Population affected | 281,214 | - | 142 areas |

### Deprived vs Affluent Coverage

| Metric | IMD Decile 1 (deprived) | IMD Decile 10 (affluent) | Equity Gap |
|--------|-------------------------|--------------------------|------------|
| Avg stops/1000 | 1.92 | 4.23 | **2.2x difference** |
| Gap areas | 217 LSOAs | 12 LSOAs | **18x more gaps in deprived** |

### Under-served vs Over-served

| Metric | Under-served (gaps) | Over-served (success) | Difference |
|--------|---------------------|----------------------|------------|
| LSOAs | 571 | 865 | - |
| People | 1.12M | 1.45M | - |
| Avg coverage | 1.80 stops/1000 | 11.42 stops/1000 | **6.3x difference** |

---

## 💰 Investment Estimates

### Top 50 Priority Gaps
```
487  new stops needed
£42M  estimated investment
2.8   Benefit-Cost Ratio (Very High VfM)
```

### Critical Bus Deserts (142 areas)
```
1,420  new stops needed (10 per area average)
£125M  estimated investment
3.2    Benefit-Cost Ratio (Very High VfM)
```

### All 571 Service Gaps
```
6,284  new stops needed (11 per area average)
£553M  estimated investment
2.4    Benefit-Cost Ratio (High VfM)
```

**Cost Assumptions:**
- £88K per stop (national average including infrastructure)
- Benefit calculation using TAG 2024 time value (£9.85/hr bus commuting)
- 30-year appraisal period, 3.5% discount rate

---

## 📍 Geographic Distribution

### Service Gaps by Region (Top 5)
```
Region                    Gap LSOAs  % of Region's LSOAs
────────────────────────────────────────────────────────
North West England        142        7.2%
Yorkshire and Humber      97         6.4%
West Midlands             86         5.9%
East of England           73         5.1%
South East England        68         4.8%
```

### Bus Deserts by Region (Top 5)
```
Region                    Desert LSOAs  Population Affected
────────────────────────────────────────────────────────────
North West England        34            68,721
Yorkshire and Humber      28            56,284
London                    18            41,203
West Midlands             17            35,198
East of England           15            29,642
```

---

## 🔢 Model Performance Stats

### Training Data
```
9,314   LSOAs used for training (after removing nulls)
7,451   training set (80%)
1,863   test set (20%)
```

### Cross-Validation
```
5-fold  cross-validation
0.067   mean CV R² (±0.016)
```

### Route Clustering Performance
```
12 min  training time (5,822 routes)
<1 sec  inference per route
7.3 MB  embedding file size
7.7 MB  model file size
```

### Anomaly Detection Performance
```
<1 min  training time (9,573 LSOAs)
<1 sec  inference per LSOA
1.2 MB  model file size
15%     contamination rate (tunable hyperparameter)
```

### Coverage Prediction Performance
```
<1 min  training time
<1 sec  inference per LSOA
5.5 MB  model file size
100     trees in Random Forest
10      max depth (regularization)
```

---

## 📈 Key Insights Summary

### Route Clustering
> **"198 distinct route types - from high-frequency urban trunk routes to low-frequency rural feeders"**

### Service Gap Detection
> **"571 under-served areas affecting 1.12M people - 142 are critical bus deserts with <1 stop per 1,000 residents"**

### Coverage Prediction
> **"Demographics explain only 9% of coverage - 91% is policy-driven. Transport planners have agency!"**

---

## 🎨 Color Coding for Dashboard Visualizations

### Service Gap Map Colors
```
🔴 RED    = Under-served (gaps)        571 LSOAs
🟢 GREEN  = Over-served (success)      865 LSOAs
⚪ GRAY   = Normal service             8,137 LSOAs
```

### Severity Color Scale
```
🔴 DARK RED    = Critical (<1 stop/1000)     142 LSOAs
🟠 ORANGE      = Severe (1-2 stops/1000)     200 LSOAs
🟡 YELLOW      = Moderate (2-3 stops/1000)   136 LSOAs
🟢 LIGHT GREEN = Mild (3+ stops/1000)        93 LSOAs
```

### Gap Type Color Coding
```
🟥 Red         = Deprived Area Gap       217 LSOAs
🟧 Orange      = High-Population Gap     167 LSOAs
🟨 Yellow      = High-Dependency Gap     99 LSOAs
🟦 Blue        = Elderly Access Gap      13 LSOAs
⬜ Light Gray  = Other Service Gap       75 LSOAs
```

---

## 📊 Dashboard Text Templates

### For G34 (Anomaly Detection Map)

**Title:**
```
Service Gap Detection: 571 Under-Served Areas Affecting 1.12 Million People
```

**Subtitle:**
```
Machine learning identified 1,436 areas with unusual coverage patterns.
Red areas are under-served (gaps), green areas are over-served (success stories).
```

**Key Metrics Box:**
```
┌─────────────────────────────────────────────┐
│ 571  Under-served areas (service gaps)      │
│ 865  Over-served areas (investment success) │
│ 142  Critical bus deserts (<1 stop/1000)    │
│ 1.12M People living in gap areas            │
│ 3.65 National median (stops/1000)           │
└─────────────────────────────────────────────┘
```

### For Category I47 (Service Gap Filling)

**Investment Priority Table:**
```
Priority  LSOA Count  Population  New Stops  Investment  BCR
────────────────────────────────────────────────────────────
Top 10    10          34,691      110        £9.7M       3.4
Top 25    25          86,728      275        £24.2M      3.1
Top 50    50          173,456     487        £42.9M      2.8
Top 100   100         346,912     974        £85.7M      2.6
All Gaps  571         1,120,740   6,284      £553M       2.4
```

### For Category G36 (Feature Importance)

**Insight Text:**
```
What determines bus stop coverage? Our analysis shows:

• 34% Elderly population (areas with more seniors get slightly more stops)
• 23% Car ownership (low-car areas get slightly more stops)
• 22% Deprivation (deprived areas get slightly more stops)
• 10% Population density
• 9% Total population
• 1% IMD decile
• 0.5% Urban vs rural (almost NO effect!)

KEY FINDING: Only 9% of coverage variation is explained by demographics.
The remaining 91% is determined by policy choices and funding decisions.

This means transport planners have enormous power to change outcomes through investment priorities.
```

---

## ⚠️ Important Caveats for Reports

### Model Limitations Box
```
┌──────────────────────────────────────────────────────┐
│ ⚠️  THESE MODELS CANNOT:                             │
│                                                       │
│ ✗ Predict ridership or passenger demand              │
│ ✗ Explain WHY gaps exist (funding? policy? other?)   │
│ ✗ Guarantee precise predictions (±2.20 error range)  │
│ ✗ Replace human judgment and local knowledge         │
│                                                       │
│ ✓ USE FOR: Strategic planning, priority setting,     │
│            benchmarking, and evidence-based advocacy │
└──────────────────────────────────────────────────────┘
```

---

## 📞 Contact for Technical Questions

See full documentation:
- `ML_MODELS_EVALUATION_REPORT.md` (technical details)
- `ML_MODELS_SIMPLE_SUMMARY.md` (plain language explanations)

---

**Last Updated:** November 10, 2025
**Models Version:** Week 4 Release
**Data Snapshot:** October 2025 (NaPTAN, BODS, ONS Census 2021)
