# UK Bus Analytics Platform - FINAL IMPLEMENTATION ROADMAP (Part 1)

**Date:** November 2, 2025 | **Last Updated:** November 4, 2025
**Status:** Week 1 Days 1-3 COMPLETE + Insight Engine Built
**Timeline:** 6 weeks (aggressive, disciplined execution)
**Deployment:** Hugging Face Spaces (FREE)
**Philosophy:** Data stories for policy makers, not just dashboards

---

## 🚨 CRITICAL ARCHITECTURAL UPDATE (Nov 4, 2025)

**During Task 1.4, we built a comprehensive Insight Engine to eliminate hardcoded narratives across all 50+ sections.**

**What Changed:**
- ✅ All dashboard sections now use **dynamic narrative generation**
- ✅ Zero hardcoded values (£42M, BCR 2.1, correlations, etc.)
- ✅ Context-aware narratives (adapts to filters intelligently)
- ✅ Evidence-gated insights (only shows what data supports)
- ✅ TAG 2024 & HM Treasury Green Book compliant

**Insight Engine: 7 modules, 1,633 lines**
```
dashboard/utils/insight_engine/
├── context.py      - Filter-aware view resolution
├── calc.py         - TAG 2024 constants + calculators
├── config.py       - Metric configurations
├── rules.py        - 6 evidence-gated insight rules
├── templates.py    - Jinja2 consulting-tone templates
├── engine.py       - Orchestrator
└── README.md       - Architecture docs
```

**Impact:**
- Task 1.4: 8h → 12h (one-time investment)
- Future sections: 3h → 2h each (engine does narrative work)
- Maintenance: Zero (no hardcoded text to update)
- Quality: Professional consulting standard across all 50 sections

---

## 📋 TABLE OF CONTENTS (Part 1)

1. [Executive Summary - The Vision](#executive-summary)
2. [Reality Check - Where We Actually Are](#reality-check)
3. [Project Philosophy - Lessons from the Journey](#project-philosophy)
4. [Homepage Design - Interactive UK Map](#homepage-design)
5. [The 10 Categories - Interlinked Structure](#categories-structure)
6. [Week 1: Foundation Repair](#week-1)
7. [Week 2-3: Build Core Categories](#week-2-3)

**→ Continue to PART 2 for:** Week 4-6, AI Assistant, Deployment, Revolutionary Features

---

<a name="executive-summary"></a>
## 1. EXECUTIVE SUMMARY - THE VISION

### What We're Building

**A consulting-grade interactive website** that transforms UK bus transport data into compelling policy narratives for decision-makers.

**NOT:** A dashboard with charts
**YES:** An intelligence platform with data stories

### Target Audience

- **Policy Makers:** Need simple insights, BCR justification, investment priorities
- **Transport Company CEOs:** Need efficiency metrics, profitability analysis, optimization opportunities
- **Urban Planners:** Need coverage gaps, equity analysis, service recommendations
- **Researchers:** Need methodology transparency, data quality, reproducibility

### Core Deliverable

**Interactive Streamlit Website with:**
- **Homepage:** Big interactive UK map with 5 switchable views
- **10 Category Pages:** Each category contains questions → visualizations → data stories
- **AI Assistant Page:** Llama Index-powered chatbot (FREE) with comprehensive knowledge base
- **50 Spatial Questions Answered:** Systematic analysis with professional visualizations

### Key Metrics

- **Data:** 767,011 bus stops, 3,578 routes, 9 regions, 97% demographic accuracy
- **Cost:** £0 ongoing (no APIs, no subscriptions)
- **Deployment:** Hugging Face Spaces (FREE tier, ~300MB optimized data)
- **Timeline:** 6 weeks aggressive execution
- **Value:** £225k+ consulting equivalent

---

<a name="reality-check"></a>
## 2. REALITY CHECK - WHERE WE ACTUALLY ARE

### ✅ WHAT WORKS (Production-Ready Foundation)

**Data Pipeline (942 lines, YAML-configured):**
- ✅ 767,011 bus stops processed (October 2025 snapshot)
- ✅ 97-99% demographic integration (REAL ONS data, not synthetic)
- ✅ 9/9 English regions covered (100% coverage)
- ✅ 8 demographic datasets integrated (age, IMD, unemployment, schools, business counts)
- ✅ Automated ETL with robust error handling
- ✅ Zero ongoing costs (no APIs)

**Files:**
- `data_pipeline/01_data_ingestion.py` - BODS, ONS, NOMIS downloads
- `data_pipeline/02_data_processing.py` - TransXChange/GTFS parsing
- `data/processed/regions/*/stops_processed.csv` - 9 regional files ready

**Data Quality:**
- Age structure: 97-98% match rate (LSOA level)
- IMD 2019: 99-100% match rate
- Unemployment 2024: 96-99% match rate
- Schools: 76-81% match rate
- Business counts: 96-99% match rate (MSOA level)

### 📦 WHAT'S ARCHIVED (Salvageable Assets)

**Location:** `archive_20251031_cleanup/`

**High-Value Components:**
- ✅ Dashboard skeleton (7 pages built with OECD-style CSS)
- ✅ BCR calculator (UK Treasury Green Book compliant - 482 lines)
- ✅ Policy scenario simulator (550 lines - fare caps, frequency changes)
- ✅ Economic impact modeling (554 lines - GDP multipliers, employment)
- ✅ ML models (need retraining on real data):
  - Route clustering (93MB)
  - Anomaly detector (1.4MB)
  - Coverage predictor (2.4MB)
- ✅ Professional UI components (776 lines custom CSS)

**Status:** Ready to rebuild on TRUE DATA foundation

### ⚠️ WHAT NEEDS WORK

**Critical Path Items:**

1. **TransXChange Schedule Parsing (NOT DONE YET)**
   - Have: 206 XML files with route/schedule data
   - Need: Extract trip schedules, frequencies, route geometries
   - Effort: 6-8 hours
   - Unlocks: 11 questions (B9, B10, B12, B15, C17-C21, C23)

2. **Update to 2024 TAG Standards**
   - Current: Generic monetary values
   - Need: DfT TAG 2024 official values
   - Time savings: £12.65/hr (bus commuting)
   - Carbon: £80/tonne CO₂
   - Effort: 4 hours

3. **Missing Quick-Win Datasets (30 minutes total)**
   - Rural-Urban Classification (5 min download)
   - LSOA Boundaries GeoJSON (5 min download)
   - Car Ownership Census 2021 (5 min download)
   - Unlocks: 5 questions (A6, A7, B16, D28, D29)

4. **Category Pages (NOT BUILT YET)**
   - Have: Dashboard skeleton
   - Need: 10 categories × questions with visualizations + data stories
   - This is the MAIN WORK (Weeks 2-4)

5. **AI Assistant Knowledge Base**
   - Have: Plan and architecture
   - Need: Llama Index integration + knowledge base loading
   - Effort: 2 days (not 5 with Llama Index!)

### ❌ WHAT'S GENUINELY MISSING (Accept as Limitation)

**Not Available for Now:**
- ❌ Ridership data (operator-proprietary, consulting firms pay £10k-50k for this)
- ❌ Real-time reliability tracking (need operator SIRI-VM access)
- ❌ Multi-year temporal trends (need historical data collection - DEFERRED)
- ❌ Journey time reliability (need real-time feeds)

**Impact:** These are consulting firm advantages. We deliver 85-90% of consulting value without them.

---

<a name="project-philosophy"></a>
## 3. PROJECT PHILOSOPHY - LESSONS FROM THE JOURNEY

### 🎯 GLOBAL DESIGN PHILOSOPHY (APPLIES TO ENTIRE PLATFORM)

**CRITICAL: This is NOT an academic research tool. This is a professional consulting intelligence platform.**

#### User Interface & Language Style

**❌ NEVER USE (Academic/Questionnaire Style):**
- "8 questions analyzing..."
- "Question A1:", "Question D24:"
- "📖 Data Story"
- "💡 Key Insight"
- "Answer:", "Analysis:", "Findings:"
- Academic section numbering (1.1, 1.2, etc.)
- Research paper terminology
- Overly technical jargon without context

**✅ ALWAYS USE (Consulting Report Style):**
- **Professional section titles:** "Regional Route Density Analysis", "Service Coverage Assessment", "Investment Priority Zones"
- **Executive language:** "Key Finding", "Policy Recommendation", "Investment Requirement"
- **Actionable headers:** "What This Means", "Action Required", "Expected Impact"
- **Consulting firm tone:** McKinsey, Deloitte, PwC style
- **Decision-maker focus:** Clear, concise, actionable
- **Evidence-based:** Data-driven but accessible

#### Visual Design

**❌ AVOID:**
- Cluttered dashboards with too many metrics
- Academic chart titles ("Figure 1: Distribution of...")
- Unnecessary labels and annotations
- Question IDs visible to users (A1, D24, etc.)

**✅ IMPLEMENT:**
- Clean, spacious layouts
- Professional chart titles ("Bus Routes per 100,000 Population by Region")
- Minimal but meaningful annotations
- Question IDs only in backend code/comments
- White space and visual hierarchy
- OECD/World Bank report aesthetic

#### Content Structure

**Every Analysis Section Should Have:**
1. **Professional Title** - Clear, descriptive (not "Question X")
2. **Visualization** - Clean chart/map (no "📊 Visualization" label needed)
3. **Narrative** - Executive summary style (2-3 paragraphs max)
4. **Key Finding** - One critical insight highlighted
5. **Policy Recommendation** - Actionable next steps with BCR/cost estimates
6. **Related Analysis Links** - Cross-references to other sections

#### Navigation & Organization

**Homepage:**
- Interactive UK map (no labels like "5 switchable views")
- National overview metrics (clean cards)
- Auto-generated insights (professional language)

**Category Pages:**
- Single scrollable page per category
- Professional category titles in sidebar
- No mention of "X questions" to users
- Smooth scrolling between analysis sections

**Cross-Linking:**
- "View related analysis" (not "See Question D24")
- Contextual recommendations
- Intelligent navigation flows

#### Target Audience Adaptation

**For Policy Makers:**
- Lead with impact and BCR
- Clear investment requirements
- Headline findings first, details second

**For Transport Company CEOs:**
- Efficiency metrics prominent
- Profitability implications
- Operational optimization opportunities

**For Urban Planners:**
- Spatial analysis emphasis
- Gap identification clear
- Service recommendations specific

**For Researchers:**
- Methodology transparency
- Data quality metrics
- Reproducibility notes

#### Example Transformation

**❌ BEFORE (Academic Style):**
```
QUESTION A1: Which regions have the highest number of bus routes per capita?

📖 DATA STORY
Manchester has 42 routes per 100k...

💡 KEY INSIGHT
Route density varies...
```

**✅ AFTER (Consulting Style):**
```
Regional Route Density Analysis

Manchester leads the nation with 42 routes per 100,000 population,
providing extensive network connectivity and multiple journey options
for residents. In contrast, East Midlands operates only 5.7 routes
per 100k, limiting travel options for 4.8 million residents.

Key Finding
Route density varies 7.4x between regions. Network design and policy
choices matter more than population scale alone - smaller regions can
achieve high route density through strategic investment.

Policy Recommendation
Five regions fall below the national average of 8.3 routes per 100k.
Estimated investment to bring bottom 3 regions to average: £42M
(BCR: 2.1 - High value for money per HM Treasury Green Book standards).

Priority actions: (1) Identify underserved corridors, (2) Design routes
connecting employment centers, (3) Integrate with existing services.

[View Optimization Scenarios →]
```

---

**This philosophy applies to:**
- All 10 category pages
- Homepage design
- All visualizations
- All data stories
- AI assistant responses
- Export reports
- Documentation shown to users

**Exception:** Internal code comments and developer documentation can use technical references (A1, D24, etc.)

---

### The Honest Reset (October 31, 2025)

**What Happened:**
- Built dashboard in 3 weeks (Sept 27 - Oct 29)
- Discovered critical data quality issues on Oct 29
- Made decisive choice: Archive everything, fix foundation
- Committed to TRUTH over POLISH

**Key Learnings:**

1. **Data Quality First, Features Second**
   - DON'T build dashboards on fake data
   - DO validate demographic integration before building analytics
   - DON'T claim 3 million stops when you have duplicates
   - DO honest audits with brutal honesty

2. **Foundation Over Features**
   - 3 weeks of work archived without hesitation
   - Rebuilt data pipeline properly
   - Achieved 97% demographic accuracy with REAL ONS data
   - Result: Production-grade foundation

3. **Document Actual, Not Aspirational**
   - Tech spec claimed "GPT-4" → Actually used Sentence Transformers (FREE)
   - Claimed "PostgreSQL" → Actually used CSV/Parquet (simpler)
   - Learning: Document what you BUILT, not what you PLANNED

4. **Honest Problem-Solving**
   - 6 critical bugs found and documented
   - Data accuracy report showed reality
   - Chose to restart rather than polish broken system
   - Integrity > Speed

### Your Philosophy: Data Stories, Not Just Charts

**From Your Vision:**
- **Categories → Questions → Data Stories** (not just visualizations)
- Each answer includes narrative explaining "what this means"
- Insight cards showing policy implications
- Visualizations support the story, not the other way around

**Example - NOT This:**
```
❌ Chart showing stops per capita by region
   (no context, no interpretation)
```

**Example - YES This:**
```
✅ "The North East faces a service coverage crisis"

   DATA: 4.1 stops per 1,000 population (34% below national average)

   VISUALIZATION: Choropleth map showing North East in red

   INSIGHT: "This gap affects 2.6 million residents, with 1,247 LSOAs
            classified as underserved. Deprived areas (IMD Decile 1-3)
            are disproportionately affected, receiving 42% less service
            than affluent areas."

   POLICY IMPLICATION: "Targeted investment of £87M could close this gap,
                       delivering a BCR of 2.3 (High value for money per
                       HM Treasury standards)."

   [Link to Investment Appraisal for this scenario →]
```

### Revolutionary Vision (Optional Phase 2)

**From REVOLUTIONARY_FEATURE_DESIGN.md:**
- Graph Neural Network policy simulator
- Real-time scenario testing (<1 second vs 6-8 week consulting reports)
- Network effects modeling (spillover benefits)
- Causal inference (not just correlation)
- AI discovers optimal policies

**Status:** Defer to Phase 2 AFTER core 50 questions complete and deployed

---

<a name="homepage-design"></a>
## 4. HOMEPAGE DESIGN - INTERACTIVE UK MAP

### The Landing Experience

**Goal:** Visitors should immediately understand the scale and see the entire UK bus network at a glance.

**Layout:**

```
┌──────────────────────────────────────────────────────────────────┐
│  🚌 UK BUS TRANSPORT INTELLIGENCE PLATFORM                       │
│  Real-time insights from 767,011 bus stops across England        │
└──────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┬──────────────────────────────┐
│                                     │  📊 NATIONAL OVERVIEW        │
│                                     │  ──────────────────────────  │
│      🗺️ INTERACTIVE UK MAP         │  🚏 767,011 Bus Stops       │
│                                     │  🚌 3,578 Routes            │
│   [Choropleth showing selected      │  📍 9 Regions               │
│    metric with regional boundaries] │  👥 56M Population          │
│                                     │                              │
│   • Hover: Region stats popup       │  ──────────────────────────  │
│   • Click: Drill down to region     │  SELECT VIEW:               │
│   • Color: Intensity by metric      │  ○ Coverage                 │
│                                     │  ○ Frequency                │
│   [Cities labeled: London,          │  ● Equity Score             │
│    Manchester, Birmingham,          │  ○ Service Gaps             │
│    Leeds, Newcastle]                │  ○ Demographics             │
│                                     │                              │
│   [Legend showing color scale]      │  🎯 KEY METRICS:            │
│                                     │  • Avg: 6.2 stops/1000 pop  │
│                                     │  • Equity Gini: 0.34        │
│                                     │  • Underserved: 13.7%       │
│                                     │                              │
└────────────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  🔍 AUTO-GENERATED INSIGHTS (from your data)                     │
│  ──────────────────────────────────────────────────────────────  │
│  ⚠️  North East: 18% below national coverage average             │
│  ✅  London: Best equity score (0.82) - services well-distributed │
│  📈  Manchester: Highest route density (42 routes/100k pop)      │
│  🎯  4,832 LSOAs identified as priority intervention areas       │
└──────────────────────────────────────────────────────────────────┘
```

### 5 Switchable Map Views

#### VIEW 1: Coverage Score (Default) 🟢

**Metric:** Stops per 1,000 population by region

**Color Scale:**
- Dark Green (#1a9850): >8 stops/1000 (excellent)
- Light Green (#91cf60): 6-8 stops/1000 (good)
- Yellow (#fee08b): 4-6 stops/1000 (moderate)
- Orange (#fc8d59): 2-4 stops/1000 (poor)
- Red (#d73027): <2 stops/1000 (critical)

**Hover Tooltip Example:**
```
┌─────────────────────────────┐
│ GREATER LONDON              │
│ ────────────────────────────│
│ Coverage: 8.4 stops/1000    │
│ Rank: #1 of 9               │
│ Population: 9.0M            │
│ Bus Stops: 107,708          │
│ Routes: 892                 │
│ Status: ✅ Well-served      │
│ [Click for details →]       │
└─────────────────────────────┘
```

**Click Action:** Navigate to Coverage category page (A) filtered to Greater London

---

#### VIEW 2: Service Frequency 🔵

**Metric:** Average buses per hour by region

**Color Scale:**
- Dark Blue: >12 buses/hr (high frequency)
- Blue: 8-12 buses/hr (good)
- Light Blue: 4-8 buses/hr (moderate)
- Yellow: 2-4 buses/hr (low)
- Red: <2 buses/hr (very low)

**Hover Shows:**
- Avg buses per hour
- Total daily trips
- Peak vs off-peak ratio
- Comparison to national average
- Rank among 9 regions

**Click Action:** Navigate to Frequency category page (B)

---

#### VIEW 3: Equity Score 🟣

**Metric:** How fairly services are distributed (inverted Gini coefficient)

**Calculation:**
- 1.0 = Perfect equity (everyone has equal access)
- 0.0 = Total inequality (services concentrated in small areas)

**Color Scale:**
- Purple (0.8-1.0): Excellent equity
- Blue (0.6-0.8): Good equity
- Yellow (0.4-0.6): Moderate inequality
- Orange (0.2-0.4): High inequality
- Red (<0.2): Severe inequality

**Hover Shows:**
- Equity score (0-1)
- Gini coefficient
- % deprived areas (IMD 1-3) served adequately
- Lorenz curve preview (mini)
- Comparison to national equity

**Why This Matters:** Shows if wealthy areas monopolize services while deprived areas lack coverage

**Click Action:** Navigate to Equity category page (F)

---

#### VIEW 4: Service Gaps (Underserved Areas) 🔴

**Metric:** % of population living >500m from nearest bus stop

**Color Scale:**
- Green (<10%): Well-covered
- Yellow (10-25%): Moderate gaps
- Orange (25-50%): Concerning
- Red (>50%): Critical service deserts

**Hover Shows:**
- % population >500m from stop
- # of "bus desert" LSOAs (0 stops)
- Investment priority level (High/Medium/Low)
- Estimated cost to achieve 90% coverage
- BCR projection for gap-filling investment

**Click Action:** Shows detailed gap analysis + recommended interventions (Category I - Optimization)

---

#### VIEW 5: Demographics Overlay 👥

**Metric:** Deprivation (IMD) with service density overlay

**Dual Layer Visualization:**
- **Background color:** IMD average (red = deprived, green = affluent)
- **Hatching pattern density:** Service coverage (dense = good, sparse = poor)

**Identifies Critical Combinations:**
- 🔴 Red + Sparse hatching = **CRITICAL** (deprived + underserved)
- 🟢 Green + Dense = Affluent areas with good service
- 🟢 Red + Dense = **SUCCESS STORIES** (deprived but well-served)
- ⚠️ Green + Sparse = Opportunity (affluent but underserved - unusual)

**Hover Shows:**
- IMD average score (0-100, where 100 = most deprived)
- IMD decile (1 = most deprived 10%)
- Coverage score (stops/1000)
- Correlation coefficient (service vs deprivation)
- Social equity grade (A-F)

**Click Action:** Navigate to Socio-Economic category page (D)

---

### Right Sidebar: Dynamic Statistics

**Updates Based on Selected View:**

**When Coverage View Active:**
```
📊 COVERAGE STATISTICS
────────────────────────
National Average: 6.2 stops/1000
Best: London (8.4)
Worst: South West (4.1)
Std Deviation: 1.8

🎯 REGIONAL RANKING
────────────────────────
1. London         8.4 ⭐⭐⭐
2. North West     7.2 ⭐⭐⭐
3. West Midlands  6.8 ⭐⭐
...
9. South West     4.1 ⚠️

[Bar chart visualization]
```

**When Equity View Active:**
```
⚖️ EQUITY ANALYSIS
────────────────────────
National Gini: 0.34 (moderate)
Most Equitable: London (0.18)
Least Equitable: SW (0.51)

📉 DISTRIBUTION
────────────────────────
[Mini Lorenz curve]

✅ Well-Served Deprived: 42%
⚠️  Underserved Deprived: 13.7%
🎯 Priority Investment: 4,832 LSOAs
```

**When Service Gaps View Active:**
```
🚨 SERVICE GAPS
────────────────────────
Underserved LSOAs: 4,832
Population Affected: 7.2M
Investment Required: £247M
Expected BCR: 2.1 (High VfM)

🎯 TOP PRIORITIES
────────────────────────
1. North East: 1,247 LSOAs
   Cost: £87M, BCR: 2.3
2. South West: 982 LSOAs
   Cost: £68M, BCR: 2.0
3. East Midlands: 634 LSOAs
   Cost: £44M, BCR: 2.4
```

---

### Bottom Section: Auto-Generated Insights

**AI-Powered Key Findings (refreshes with data):**

```python
def generate_homepage_insights():
    """
    Auto-generate 4-5 key insights from current data
    Runs every time homepage loads
    """
    insights = []

    # Insight 1: Biggest coverage gap
    worst_region = regional_data.sort_values('stops_per_1000').iloc[0]
    gap_pct = ((national_avg - worst_region.stops_per_1000) / national_avg) * 100

    insights.append({
        'type': 'warning',
        'icon': '⚠️',
        'text': f"{worst_region.name}: {gap_pct:.0f}% below national coverage average",
        'detail': f"Only {worst_region.stops_per_1000:.1f} stops/1000 vs national {national_avg:.1f}",
        'link': f'/coverage?region={worst_region.code}'
    })

    # Insight 2: Best equity performer
    best_equity = regional_data.sort_values('equity_score', ascending=False).iloc[0]

    insights.append({
        'type': 'success',
        'icon': '✅',
        'text': f"{best_equity.name}: Best equity score ({best_equity.equity_score:.2f})",
        'detail': "Services well-distributed across all demographic groups",
        'link': f'/equity?region={best_equity.code}'
    })

    # Insight 3: Correlation finding
    corr_imd_coverage = calculate_correlation('imd_score', 'stops_per_1000')

    if abs(corr_imd_coverage) > 0.5:
        insights.append({
            'type': 'info',
            'icon': '📊',
            'text': f"Strong correlation: Deprived areas receive {abs(corr_imd_coverage)*100:.0f}% less service",
            'detail': f"Correlation coefficient: {corr_imd_coverage:.2f} (statistically significant)",
            'link': '/socioeconomic'
        })

    # Insight 4: High-value opportunity
    high_pop_low_service = find_mismatched_lsoas(
        population_threshold=5000,
        coverage_threshold=4.0
    )

    insights.append({
        'type': 'opportunity',
        'icon': '🎯',
        'text': f"{len(high_pop_low_service)} high-density areas with minimal service",
        'detail': "Prime investment targets with high BCR potential (>2.5)",
        'link': '/optimization'
    })

    # Insight 5: Route density leader
    best_routes = regional_data.sort_values('routes_per_100k', ascending=False).iloc[0]

    insights.append({
        'type': 'info',
        'icon': '📈',
        'text': f"{best_routes.name}: Highest route density ({best_routes.routes_per_100k:.0f} routes/100k pop)",
        'detail': "Extensive network providing multiple connection options",
        'link': f'/routes?region={best_routes.code}'
    })

    return insights[:4]  # Show top 4 insights
```

**Display Format:**
```
🔍 KEY INSIGHTS

⚠️  North East: 34% below national coverage average
    Only 4.1 stops/1000 vs national 6.2
    [View Coverage Analysis →]

✅  London: Best equity score (0.82)
    Services well-distributed across all demographic groups
    [View Equity Analysis →]

📊  Strong correlation: Deprived areas receive 67% less service
    Correlation coefficient: -0.67 (statistically significant)
    [View Socio-Economic Analysis →]

🎯  1,834 high-density areas with minimal service
    Prime investment targets with high BCR potential (>2.5)
    [View Optimization Opportunities →]
```

---

### Technical Implementation

**Map Library:** Folium + streamlit-folium

**File:** `dashboard/pages/00_Home.py`

```python
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd

st.set_page_config(
    page_title="UK Bus Analytics",
    page_icon="🚌",
    layout="wide"
)

# Title
st.title("🚌 UK Bus Transport Intelligence Platform")
st.markdown("Real-time insights from **767,011 bus stops** across England")

# Layout: Map on left, stats on right
col_map, col_stats = st.columns([3, 1])

with col_stats:
    st.markdown("### 📊 NATIONAL OVERVIEW")
    st.metric("🚏 Bus Stops", "767,011")
    st.metric("🚌 Routes", "3,578")
    st.metric("📍 Regions", "9")
    st.metric("👥 Population", "56M")

    st.markdown("---")
    st.markdown("### SELECT VIEW:")

    view_type = st.radio(
        "",
        ['coverage', 'frequency', 'equity', 'service_gaps', 'demographics'],
        format_func=lambda x: {
            'coverage': '🟢 Coverage',
            'frequency': '🔵 Frequency',
            'equity': '🟣 Equity Score',
            'service_gaps': '🔴 Service Gaps',
            'demographics': '👥 Demographics'
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Dynamic stats based on view
    if view_type == 'coverage':
        st.markdown("### 📊 COVERAGE STATS")
        st.metric("National Avg", "6.2 stops/1000")
        st.metric("Best", "London (8.4)")
        st.metric("Worst", "South West (4.1)")

    elif view_type == 'equity':
        st.markdown("### ⚖️ EQUITY STATS")
        st.metric("National Gini", "0.34")
        st.metric("Most Equitable", "London (0.18)")
        st.metric("Underserved", "13.7%")

with col_map:
    # Create interactive map
    @st.cache_data
    def create_uk_map(view):
        # Load UK regional boundaries
        uk_regions = gpd.read_file('data/boundaries/uk_regions.geojson')
        regional_stats = pd.read_csv('data/processed/regional_summary.csv')

        # Merge geometry with stats
        uk_regions = uk_regions.merge(regional_stats, on='region_code')

        # Create base map centered on UK
        m = folium.Map(
            location=[54.5, -2.0],
            zoom_start=6,
            tiles='CartoDB positron',
            scrollWheelZoom=False
        )

        # Define metric based on view
        metric_config = {
            'coverage': {
                'column': 'stops_per_1000',
                'colorscale': ['#d73027', '#fee08b', '#91cf60', '#1a9850'],
                'vmin': 2, 'vmax': 10,
                'legend': 'Stops per 1,000 Population'
            },
            'frequency': {
                'column': 'avg_buses_per_hour',
                'colorscale': ['#d73027', '#fee08b', '#91bfdb', '#4575b4'],
                'vmin': 1, 'vmax': 15,
                'legend': 'Average Buses per Hour'
            },
            'equity': {
                'column': 'equity_score',
                'colorscale': ['#d73027', '#fee08b', '#91bfdb', '#7b3294'],
                'vmin': 0, 'vmax': 1,
                'legend': 'Equity Score (0=inequality, 1=perfect)'
            }
            # ... other views
        }

        config = metric_config[view]

        # Add choropleth
        folium.Choropleth(
            geo_data=uk_regions,
            data=regional_stats,
            columns=['region_code', config['column']],
            key_on='feature.properties.region_code',
            fill_color='YlGnBu',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=config['legend']
        ).add_to(m)

        # Add tooltips
        for idx, row in uk_regions.iterrows():
            tooltip_html = f"""
            <div style="font-family: Arial; font-size: 13px; padding: 8px;">
                <b style="font-size: 15px;">{row['region_name']}</b><br>
                <hr style="margin: 5px 0;">
                Coverage: <b>{row['stops_per_1000']:.1f}</b> stops/1000<br>
                Rank: <b>#{row['rank']}</b> of 9<br>
                Population: <b>{row['population']/1e6:.1f}M</b><br>
                Bus Stops: <b>{row['total_stops']:,}</b><br>
                Status: <b>{'✅ Well-served' if row['stops_per_1000'] > 6 else '⚠️ Below average'}</b>
            </div>
            """

            folium.GeoJson(
                row['geometry'],
                tooltip=folium.Tooltip(tooltip_html),
                style_function=lambda x: {
                    'fillOpacity': 0.6,
                    'weight': 1,
                    'color': 'black'
                }
            ).add_to(m)

        # Add major city markers
        cities = [
            {'name': 'London', 'coords': [51.5074, -0.1278]},
            {'name': 'Manchester', 'coords': [53.4808, -2.2426]},
            {'name': 'Birmingham', 'coords': [52.4862, -1.8904]},
            {'name': 'Leeds', 'coords': [53.8008, -1.5491]},
            {'name': 'Newcastle', 'coords': [54.9783, -1.6178]},
        ]

        for city in cities:
            folium.CircleMarker(
                location=city['coords'],
                radius=4,
                color='black',
                fill=True,
                fillColor='white',
                fillOpacity=0.8,
                popup=city['name'],
                tooltip=city['name']
            ).add_to(m)

        return m

    # Display map
    map_obj = create_uk_map(view_type)
    st_folium(map_obj, width=900, height=600, returned_objects=[])

# Auto-generated insights section
st.markdown("---")
st.markdown("## 🔍 Key Insights")

insights = generate_homepage_insights()  # Function defined above

cols = st.columns(2)
for i, insight in enumerate(insights):
    with cols[i % 2]:
        if insight['type'] == 'warning':
            st.warning(f"{insight['icon']} **{insight['text']}**\n\n{insight['detail']}")
        elif insight['type'] == 'success':
            st.success(f"{insight['icon']} **{insight['text']}**\n\n{insight['detail']}")
        else:
            st.info(f"{insight['icon']} **{insight['text']}**\n\n{insight['detail']}")

        st.markdown(f"[View Analysis →]({insight['link']})")
```

---

<a name="categories-structure"></a>
## 5. THE 10 CATEGORIES - INTERLINKED STRUCTURE

### Overview: Spatial Analysis Only (NO TEMPORAL)

**Total Questions:** 50 spatial questions across 10 categories
**Temporal Analysis:** DEFERRED to Phase 2

| Category | Questions | Status | Priority |
|----------|-----------|--------|----------|
| A. Coverage & Accessibility | 8 | ✅ Spatial | Week 1 |
| B. Service Frequency & Reliability | 5 | ✅ Spatial (3 temporal deferred) | Week 2 |
| C. Route Characteristics | 7 | ✅ Spatial | Week 2 |
| D. Socio-Economic Correlations | 8 | ✅ Spatial | Week 2 |
| E. Temporal & Trend Analysis | 0 | ❌ ALL DEFERRED | Phase 2 |
| F. Equity & Social Inclusion | 6 | ✅ Spatial | Week 3 |
| G. Advanced ML Insights | 5 | ✅ Spatial (2 temporal deferred) | Week 4 |
| H. Accessibility Features | 4 | ✅ Spatial | Week 4 |
| I. Route Optimization | 4 | ✅ Spatial | Week 4 |
| J. Economic Impact & BCR | 4 | ✅ Spatial | Week 4 |
| **TOTAL** | **50** | **50 Spatial, 0 Temporal** | **6 weeks** |

### How Categories Interlink

```
HOMEPAGE (Interactive Map)
    ↓
    ├── COVERAGE (A) ──→ feeds into ──→ EQUITY (F)
    │       ↓                              ↓
    │   FREQUENCY (B) ──→ affects ──→ ROUTES (C)
    │       ↓                              ↓
    │   SOCIO-ECONOMIC (D) ←── correlates ←── ACCESSIBILITY (H)
    │       ↓
    │   ML INSIGHTS (G) ──→ identifies ──→ OPTIMIZATION (I)
    │       ↓                              ↓
    │   ECONOMIC (J) ←── justifies ←──────┘
    │
    └── AI ASSISTANT (answers questions, explains all categories)
```

**Navigation Flow:**
1. User lands on **Homepage** → sees UK map with coverage gaps in red
2. Clicks North East region → navigates to **Category A (Coverage)**
3. Coverage page shows "North East underserved" → link to **Category F (Equity)**
4. Equity page shows "Deprived areas affected" → link to **Category D (Socio-Economic)**
5. Socio-Economic shows correlation → link to **Category I (Optimization)** for solutions
6. Optimization suggests routes → link to **Category J (Economic)** for BCR justification

### Build Order (Based on Data Dependencies)

**Priority Order:**
1. **Week 1:** Category A (Coverage) - Foundation
2. **Week 2:** Category D (Socio-Economic) - Demographics ready
3. **Week 2:** Category F (Equity) - Depends on A + D
4. **Week 2:** Category C (Routes) - After TransXChange parsing
5. **Week 3:** Category B (Frequency) - Depends on C
6. **Week 3:** Category H (Accessibility) - Deep dive on A
7. **Week 4:** Category I (Optimization) - Depends on A, D, F
8. **Week 4:** Category J (Economic) - BCR for optimization scenarios
9. **Week 4:** Category G (ML Insights) - Train models on all above data

---

### CATEGORY A: Coverage & Accessibility (8 Questions)

**Page URL:** `/coverage`

**Navigation From:** Homepage map (Coverage view), AI Assistant

**Questions:**

**A1.** Which regions have the highest number of bus routes per capita?
**Implementation:** Aggregate routes by region, divide by population
**Visualization:** Horizontal bar chart (sorted descending)
**Data Story:** "Manchester leads with 42 routes per 100k population, providing extensive network connectivity..."

**A2.** Which regions have the lowest number of bus stops per 1,000 residents?
**Implementation:** Count stops by region, normalize by population
**Visualization:** Choropleth map + ranking table
**Data Story:** "South West ranks lowest at 4.1 stops/1000, affecting 5.6M residents..."

**A3.** Are there regions where bus stop density is low relative to population density?
**Implementation:** Scatter plot (stop density vs population density), identify outliers
**Visualization:** Interactive scatter plot with quadrant analysis
**Data Story:** "High-population-low-coverage quadrant reveals 1,834 LSOAs as priority targets..."

**A4.** How many areas lack any bus service (bus deserts)?
**Implementation:** Count LSOAs with 0 bus stops
**Visualization:** Map showing bus deserts in red + count metric
**Data Story:** "247 LSOAs (0.7%) are complete bus deserts, home to 380k residents..."

**A5.** What is the average distance from a household to the nearest bus stop in each region?
**Implementation:** Haversine distance calculation, aggregate by region
**Visualization:** Regional comparison with box plots showing distribution
**Data Story:** "Rural LSOAs average 1.2km to nearest stop vs 180m in urban areas..."

**A6.** Which local authorities have more than 50% of residents living >500m from a bus stop?
**Implementation:** Buffer analysis (500m radius), calculate population coverage
**Visualization:** Map with LA highlighted + table of worst performers
**Data Story:** "23 local authorities fail the 500m accessibility standard..."

**A7.** How does bus coverage vary between urban and rural areas?
**Implementation:** Classify LSOAs as urban/rural, compare stop density
**Visualization:** Box plot comparison + distribution histogram
**Data Story:** "Urban areas average 8.1 stops/1000 vs rural 2.3 - a 3.5x disparity..."

**A8.** Are there regions where population density is high but bus services are minimal?
**Implementation:** Identify high-pop-density + low-coverage LSOAs
**Visualization:** Heatmap overlay (population vs coverage)
**Data Story:** "1,247 high-density LSOAs are critically underserved - £87M investment could close this gap with BCR 2.3..."

**Page Template Structure:**
```
┌──────────────────────────────────────────────────────────────┐
│  CATEGORY A: COVERAGE & ACCESSIBILITY                        │
│  8 Questions | Data from 767,011 stops across 9 regions      │
└──────────────────────────────────────────────────────────────┘

[Filter: Region ▼] [Filter: Urban/Rural ▼] [Export PDF] [Ask AI Assistant]

─────────────────────────────────────────────────────────────

QUESTION A1: Which regions have the highest bus routes per capita?

📊 VISUALIZATION
[Horizontal bar chart: Routes per 100k population by region]

📖 DATA STORY
Manchester leads the nation with 42 routes per 100,000 population,
providing extensive network connectivity and multiple journey options.
London follows at 38 routes/100k, leveraging dense urban layout...

💡 KEY INSIGHT
Route density correlates strongly with urban density (r=0.82) but
not with population size, suggesting network design matters more
than scale alone.

📈 POLICY IMPLICATION
Regions below 25 routes/100k should prioritize network expansion
over frequency increases to improve connectivity options.

[Link to Optimization Scenarios for Route Expansion →]

─────────────────────────────────────────────────────────────

QUESTION A2: Which regions have lowest stops per 1,000 residents?

[Repeat structure for each question...]
```

---

### CATEGORY D: Socio-Economic Correlations (8 Questions)

**Page URL:** `/socioeconomic`

**Navigation From:** Homepage (Demographics view), Equity page, AI Assistant

**Questions:**

**D24.** Is there a correlation between bus coverage and deprivation (IMD)?
**Visualization:** Scatter plot with regression line
**Data Story:** "Strong negative correlation (r=-0.67): deprived areas receive 34% less service..."

**D25.** Do areas with higher unemployment have fewer bus services?
**Visualization:** Dual-axis choropleth map (unemployment + coverage overlay)
**Data Story:** "Employment barriers compound: high-unemployment LSOAs also lack job center access..."

**D26.** How does bus coverage correlate with elderly population percentage?
**Visualization:** Heatmap correlation matrix
**Data Story:** "Elderly populations (70+) in rural areas face double burden: mobility limits + sparse service..."

**D27.** Do regions with higher car ownership have lower bus service provision?
**Visualization:** Bubble chart (car ownership vs coverage, bubble = population)
**Data Story:** "Car ownership doesn't explain all variance - policy priorities matter more than demand..."

**D28.** Is there a relationship between bus coverage and educational attainment?
**Visualization:** Regional comparison with education levels
**Data Story:** "Limited transport access correlates with lower university enrollment from deprived LSOAs..."

**D29.** How does bus frequency vary with the concentration of key amenities?
**Visualization:** Network map showing routes to schools, hospitals, job centers
**Data Story:** "52% of schools in deprived areas lack direct bus routes during school hours..."

**D30.** Are business-dense areas better served by public transport?
**Visualization:** Employment centers overlaid on service frequency map
**Data Story:** "Business parks show 2.3x better service than residential areas of similar density..."

**D31.** What is the relationship between population density and bus stop density?
**Visualization:** Log-scale scatter plot with urban/rural classification
**Data Story:** "Service provision lags population density in rapidly-growing suburbs..."

---

<a name="week-1"></a>
## 6. WEEK 1: FOUNDATION REPAIR (5 Days)

### ANTI-CHAOS RULES

**MANDATORY BEFORE STARTING:**
- ✅ No moving to Week 2 until ALL Week 1 tasks 100% complete
- ✅ No "quick features" or "just one more thing"
- ✅ Test with REAL data, not placeholders
- ✅ Document blockers immediately, don't work around silently
- ✅ Quality gate: If data missing, STOP and get data first

---

### DAY 1-2: Data Foundation Fixes

#### Task 1.1: Update BCR Calculator with 2024 TAG Values (4 hours)

**File:** `archive_20251031_cleanup/analysis/spatial/bcr_calculator.py`

**Changes Required:**

```python
# BEFORE (Generic values)
TIME_SAVINGS_VALUE = 25.0  # Generic £/hour
CARBON_VALUE = 250.0       # Outdated £/tonne

# AFTER (2024 DfT TAG official values)
TIME_SAVINGS = {
    'bus_commuting': 9.85,     # £/hour (TAG A1.3 Table 2)
    'car_commuting': 12.65,    # £/hour
    'business': 28.30,         # £/hour
    'leisure': 7.85            # £/hour
}

CARBON_VALUE = 80.0           # £/tonne CO₂ (2024 central estimate)
BUS_EMISSIONS = 0.0965        # kg CO₂e per passenger-km (BEIS 2024)

# Add agglomeration uplift
AGGLOMERATION_UPLIFT = {
    'urban': 0.25,            # 25% uplift for urban areas
    'city_center': 0.50       # 50% uplift for city centers
}

# BCR thresholds (HM Treasury Green Book)
BCR_CATEGORIES = {
    'poor': (0, 1.0),
    'low': (1.0, 1.5),
    'medium': (1.5, 2.0),
    'high': (2.0, 4.0),
    'very_high': (4.0, float('inf'))
}
```

**Validation:**
- Test BCR calculation for £50M investment scenario
- Compare to consulting report benchmarks
- Verify discount rate = 3.5% for 30-year appraisal

**Deliverable:** Updated `bcr_calculator.py` with 2024 values, unit tests passing

---

#### Task 1.2: Parse TransXChange XML Schedules (6-8 hours)

**Problem:** Have 206 XML files but schedules NOT extracted yet

**What to Extract:**
1. Vehicle journeys (trips) with departure times
2. Route geometries (stop sequences)
3. Service frequencies by time of day
4. Headway calculations

**New File:** `utils/transxchange_schedule_extractor.py`

```python
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

class TransXChangeScheduleExtractor:
    """Extract trip schedules, frequencies, and route geometries from TransXChange XML"""

    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.ns = {'txc': 'http://www.transxchange.org.uk/'}

    def extract_vehicle_journeys(self):
        """Extract all trips with departure times"""
        trips = []

        for journey in self.root.findall('.//txc:VehicleJourney', self.ns):
            trip = {
                'journey_code': journey.find('.//txc:PrivateCode', self.ns).text,
                'route_ref': journey.find('.//txc:LineRef', self.ns).text,
                'pattern_ref': journey.find('.//txc:JourneyPatternRef', self.ns).text,
                'departure_time': journey.find('.//txc:DepartureTime', self.ns).text,
                'operating_profile': self._extract_operating_profile(journey)
            }
            trips.append(trip)

        return pd.DataFrame(trips)

    def extract_route_geometry(self):
        """Extract stop sequences and link distances"""
        routes = []

        for section in self.root.findall('.//txc:JourneyPatternSection', self.ns):
            section_id = section.get('id')

            for link in section.findall('.//txc:JourneyPatternTimingLink', self.ns):
                route_link = {
                    'section_id': section_id,
                    'from_stop': link.find('.//txc:From/txc:StopPointRef', self.ns).text,
                    'to_stop': link.find('.//txc:To/txc:StopPointRef', self.ns).text,
                    'distance_m': int(link.find('.//txc:Distance', self.ns).text) if link.find('.//txc:Distance', self.ns) is not None else None,
                    'run_time_min': self._parse_duration(link.find('.//txc:RunTime', self.ns))
                }
                routes.append(route_link)

        return pd.DataFrame(routes)

    def calculate_frequencies(self, trips_df):
        """Calculate service frequency by hour of day"""
        # Parse departure times
        trips_df['hour'] = pd.to_datetime(trips_df['departure_time'], format='%H:%M:%S').dt.hour

        # Count trips per hour
        freq = trips_df.groupby(['route_ref', 'hour']).size().reset_index(name='trips_per_hour')

        # Calculate headway (average minutes between buses)
        freq['headway_min'] = 60 / freq['trips_per_hour']

        return freq

    def _parse_duration(self, duration_elem):
        """Parse ISO 8601 duration (PT15M) to minutes"""
        if duration_elem is None:
            return None
        duration_str = duration_elem.text
        # Simple parsing for PT{minutes}M format
        if 'PT' in duration_str and 'M' in duration_str:
            return int(duration_str.replace('PT', '').replace('M', ''))
        return None

# Process all 206 XML files
def process_all_transxchange_files():
    """Main processing function"""
    all_trips = []
    all_routes = []
    all_frequencies = []

    xml_files = list(Path('data/raw/regions/').rglob('*.xml'))
    print(f"Found {len(xml_files)} TransXChange XML files")

    for xml_file in xml_files:
        try:
            extractor = TransXChangeScheduleExtractor(xml_file)

            # Extract trips
            trips = extractor.extract_vehicle_journeys()
            all_trips.append(trips)

            # Extract route geometry
            routes = extractor.extract_route_geometry()
            all_routes.append(routes)

            # Calculate frequencies
            freq = extractor.calculate_frequencies(trips)
            all_frequencies.append(freq)

            print(f"✓ Processed {xml_file.name}: {len(trips)} trips, {len(routes)} route links")

        except Exception as e:
            print(f"✗ Failed {xml_file.name}: {e}")

    # Combine all data
    trips_combined = pd.concat(all_trips, ignore_index=True)
    routes_combined = pd.concat(all_routes, ignore_index=True)
    freq_combined = pd.concat(all_frequencies, ignore_index=True)

    # Save outputs
    trips_combined.to_csv('data/processed/outputs/trips_schedule.csv', index=False)
    routes_combined.to_csv('data/processed/outputs/route_geometries.csv', index=False)
    freq_combined.to_csv('data/processed/outputs/service_frequencies.csv', index=False)

    print(f"\n✅ COMPLETE")
    print(f"   Trips: {len(trips_combined):,}")
    print(f"   Route links: {len(routes_combined):,}")
    print(f"   Frequency records: {len(freq_combined):,}")

    return trips_combined, routes_combined, freq_combined

if __name__ == '__main__':
    process_all_transxchange_files()
```

**Run:**
```bash
python utils/transxchange_schedule_extractor.py
```

**Expected Output:**
```
Found 206 TransXChange XML files
✓ Processed First_Bus_Yorkshire.xml: 2,340 trips, 1,456 route links
✓ Processed Arriva_North_East.xml: 1,890 trips, 892 route links
...
✅ COMPLETE
   Trips: 41,234
   Route links: 28,976
   Frequency records: 5,432
```

**Deliverable:**
- `data/processed/outputs/trips_schedule.csv`
- `data/processed/outputs/route_geometries.csv`
- `data/processed/outputs/service_frequencies.csv`

**Unlocks Questions:** B9, B10, B12, B15, C17-C21, C23

---

#### Task 1.3: Download Missing Datasets (30 minutes)

**Quick wins to unlock 5 more questions:**

**Dataset 1: Rural-Urban Classification (5 min)**
```bash
# Download from ONS
wget https://www.gov.uk/government/statistics/rural-urban-classification-2011-of-lower-layer-super-output-areas-in-england-and-wales/file -O data/raw/boundaries/rural_urban_2011.csv

# Or use direct link
curl "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/239477/RUC11_LAD11_ENv2.csv" -o data/raw/boundaries/rural_urban_2011.csv
```

**Dataset 2: LSOA Boundaries GeoJSON (5 min)**
```bash
# Download from ONS Geography Portal
wget "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2021_Boundaries_EW_BGC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson" -O data/raw/boundaries/lsoa_2021.geojson
```

**Dataset 3: Car Ownership (Census 2021 Table TS045) (10 min)**
```python
# Use NOMIS API
import requests
import pandas as pd

def download_car_ownership():
    """Download Census 2021 car ownership by LSOA"""

    # NOMIS API for Table TS045
    url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2072_1.data.csv"
    params = {
        'geography': '1249934337...1249951436',  # All LSOAs
        'c_carsno': '0...5',  # 0 to 5+ cars
        'measures': '20100',  # Count
        'select': 'geography_code,c_carsno_name,obs_value'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Save raw CSV
        with open('data/raw/demographics/car_ownership_2021.csv', 'wb') as f:
            f.write(response.content)

        # Process to LSOA-level summary
        df = pd.read_csv('data/raw/demographics/car_ownership_2021.csv')

        # Calculate % households with no car
        summary = df.pivot_table(
            index='geography_code',
            columns='c_carsno_name',
            values='obs_value'
        ).reset_index()

        summary['pct_no_car'] = (summary['No cars or vans'] / summary.sum(axis=1)) * 100
        summary.to_csv('data/raw/demographics/car_ownership_processed.csv', index=False)

        print(f"✅ Downloaded car ownership for {len(summary)} LSOAs")
    else:
        print(f"❌ Failed: HTTP {response.status_code}")

download_car_ownership()
```

**Validation:**
```bash
# Check files exist
ls -lh data/raw/boundaries/rural_urban_2011.csv
ls -lh data/raw/boundaries/lsoa_2021.geojson
ls -lh data/raw/demographics/car_ownership_processed.csv

# Verify row counts
wc -l data/raw/boundaries/rural_urban_2011.csv
# Should be ~35,000 LSOAs
```

**Deliverable:** 3 new datasets ready for merging

**Unlocks Questions:** A6, A7, B16, D27, D28

---

### DAY 3: Build Category Page Template + Insight Engine

#### Task 1.4: Create Reusable Category Component + Dynamic Narrative System (12 hours)

**CRITICAL ARCHITECTURAL DECISION (Nov 4, 2025):**

During implementation, discovered that hardcoded narratives (£42M investments, BCR 2.1, "best/worst" comparisons) would create maintenance nightmares across 50+ sections.

**Solution:** Build a **Hybrid Insight Engine** that generates fully dynamic, context-aware narratives.

**Goal:** Build ONE perfect category page with intelligent narrative generation, then replicate for all 10 categories

**Files:**
- `dashboard/components/category_template.py` - UI template
- `dashboard/utils/insight_engine/` - Dynamic narrative generation system

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_category_page(category_config):
    """
    Reusable template for all category pages

    Args:
        category_config: Dict with structure:
        {
            'title': 'Coverage & Accessibility',
            'icon': '🟢',
            'description': '8 questions analyzing service coverage...',
            'questions': [
                {
                    'id': 'A1',
                    'text': 'Which regions have highest routes per capita?',
                    'data_function': load_A1_data,
                    'viz_function': create_A1_viz,
                    'story_function': generate_A1_story
                },
                ...
            ]
        }
    """

    # Page header
    st.set_page_config(page_title=category_config['title'], page_icon=category_config['icon'], layout="wide")

    st.title(f"{category_config['icon']} {category_config['title']}")
    st.markdown(category_config['description'])

    # Filters (common across all categories)
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        selected_region = st.selectbox(
            "Filter by Region:",
            ['All Regions'] + list(REGIONS),
            key=f"{category_config['id']}_region"
        )
    with col2:
        urban_rural = st.selectbox(
            "Urban/Rural:",
            ['All', 'Urban', 'Rural'],
            key=f"{category_config['id']}_urban"
        )
    with col3:
        export_format = st.selectbox("Export:", ['PDF', 'CSV', 'Excel'])
    with col4:
        if st.button("📥 Export"):
            export_category_report(category_config, selected_region, export_format)

    st.markdown("---")

    # Render each question
    for question in category_config['questions']:
        render_question(
            question=question,
            region_filter=selected_region,
            urban_rural_filter=urban_rural
        )
        st.markdown("---")

    # Bottom: Link to AI Assistant
    st.info("💬 Have questions about this analysis? [Ask the AI Assistant](/ai_assistant)")

def render_question(question, region_filter, urban_rural_filter):
    """Render individual question with viz + story"""

    # Question header
    st.markdown(f"### {question['id']}: {question['text']}")

    # Load data (with filters)
    data = question['data_function'](region_filter, urban_rural_filter)

    # Create visualization
    viz = question['viz_function'](data)

    # Layout: Viz on left, story on right
    col_viz, col_story = st.columns([2, 1])

    with col_viz:
        st.markdown("#### 📊 Visualization")
        st.plotly_chart(viz, use_container_width=True)

    with col_story:
        st.markdown("#### 📖 Data Story")
        story = question['story_function'](data)
        st.markdown(story['narrative'])

        st.markdown("#### 💡 Key Insight")
        st.info(story['insight'])

        st.markdown("#### 📈 Policy Implication")
        st.success(story['policy_implication'])

        # Related links
        if 'related_links' in story:
            st.markdown("#### 🔗 Related Analysis")
            for link in story['related_links']:
                st.markdown(f"- [{link['text']}]({link['url']})")
```

**Example Category Config (Coverage):**

```python
# dashboard/pages/01_Coverage_Accessibility.py

from category_template import render_category_page
import pandas as pd
import plotly.express as px

# Data loading functions
def load_A1_data(region_filter, urban_rural_filter):
    """Load routes per capita data"""
    df = pd.read_csv('data/processed/regional_summary.csv')

    if region_filter != 'All Regions':
        df = df[df['region_name'] == region_filter]

    return df

def create_A1_viz(data):
    """Create bar chart for routes per capita"""
    fig = px.bar(
        data.sort_values('routes_per_100k', ascending=False),
        x='routes_per_100k',
        y='region_name',
        orientation='h',
        title='Bus Routes per 100,000 Population',
        labels={'routes_per_100k': 'Routes per 100k', 'region_name': ''},
        color='routes_per_100k',
        color_continuous_scale='Greens'
    )
    fig.update_layout(height=500, showlegend=False)
    return fig

def generate_A1_story(data):
    """Generate narrative for routes per capita"""
    best = data.sort_values('routes_per_100k', ascending=False).iloc[0]
    worst = data.sort_values('routes_per_100k', ascending=True).iloc[0]
    national_avg = data['routes_per_100k'].mean()

    return {
        'narrative': f"""
        **{best.region_name}** leads the nation with **{best.routes_per_100k:.1f} routes
        per 100,000 population**, providing extensive network connectivity and multiple
        journey options for residents. This is {((best.routes_per_100k / national_avg - 1) * 100):.0f}%
        above the national average of {national_avg:.1f} routes per 100k.

        In contrast, **{worst.region_name}** has only **{worst.routes_per_100k:.1f} routes per 100k**,
        limiting connectivity and reducing travel options for {worst.population/1e6:.1f} million residents.
        """,

        'insight': f"""
        Route density correlates strongly with urban density (r=0.82) but NOT with
        population size alone. **Network design matters more than scale** - smaller
        regions can achieve high route density through strategic planning.
        """,

        'policy_implication': f"""
        Regions below 25 routes/100k should prioritize **network expansion over frequency
        increases** to improve connectivity options. Estimated investment: £42M to bring
        bottom 3 regions to national average (BCR: 2.1, High value for money).
        """,

        'related_links': [
            {'text': 'View Optimization Scenarios →', 'url': '/optimization'},
            {'text': 'Calculate BCR for Route Expansion →', 'url': '/economic'}
        ]
    }

# Page configuration
COVERAGE_CONFIG = {
    'id': 'coverage',
    'title': 'Coverage & Accessibility',
    'icon': '🟢',
    'description': '8 questions analyzing bus stop density, route coverage, and accessibility across regions',
    'questions': [
        {
            'id': 'A1',
            'text': 'Which regions have the highest number of bus routes per capita?',
            'data_function': load_A1_data,
            'viz_function': create_A1_viz,
            'story_function': generate_A1_story
        },
        # ... 7 more questions
    ]
}

# Render page
render_category_page(COVERAGE_CONFIG)
```

**Test with Real Data:**
- Load actual regional_summary.csv
- Verify visualizations render correctly
- Check story narratives make sense
- Test region filtering works

**Architecture: Insight Engine System**

To avoid hardcoding narratives across 50+ sections, we build a **5-layer dynamic narrative system**:

**Layer 1: Context Resolver**
- Detects filter state (all regions / single region / subset)
- Prevents "best/worst" comparisons on single-row datasets
- Adapts narrative structure based on data shape

**Layer 2: Centralized Calculators (`calc.py`)**
- TAG 2024 time values, carbon, BCR thresholds (single source of truth)
- BCR calculation wrapper (delegates to existing Green Book calculator)
- Statistical functions: correlations with p-values, CIs, effect sizes
- Equity metrics: Gini, Lorenz curves, Palma ratio
- Gap analysis: investment requirements, routes needed, population affected
- Ranking and distance from benchmarks

**Layer 3: Insight Rules (`rules.py`)**
- Small, testable rules that analyze data patterns
- Evidence-gated: only fire when statistical thresholds met
- Examples: RankingRule, SingleRegionPositioningRule, CorrelationRule, OutlierRule, GapToInvestmentRule
- Each rule has `applies(context, metrics)` and `emit(context, metrics)` methods
- Suppresses insights when data insufficient (low n, high p-values, weak correlations)

**Layer 4: Template Renderer (`templates.py`)**
- Jinja2 templates with conditional blocks
- Consulting-tone text with dynamic value injection
- Context-aware: different templates for all-regions vs single-region vs subsets
- No hardcoded numbers - all values from calculators

**Layer 5: Evidence & Guardrails**
- Data sufficiency checks (minimum n, match rate thresholds)
- Source stamping (NaPTAN, BODS, ONS, TAG 2024)
- Audit payload (JSON with all underlying numbers for QA)
- Unit tests for calculators, golden tests for narratives

**InsightEngine Orchestrator (`engine.py`):**
```python
class InsightEngine:
    def run(self, df, metric_config, filters):
        # 1. Resolve context (all-regions/single/subset)
        context = resolve_context(df, metric_config.groupby, filters)

        # 2. Compute metrics once (centralized calculators)
        metrics = compute_metrics(df, metric_config, context)

        # 3. Select applicable insight rules
        insights = []
        for rule in registry.for_metric(metric_config.id):
            if data_sufficient(metrics, rule.requirements) and rule.applies(context, metrics):
                insights.extend(rule.emit(context, metrics))

        # 4. Render templates
        blocks = [render_template(context, insight) for insight in insights]

        return {
            'summary': blocks['narrative'],
            'key_finding': blocks['key_finding'],
            'recommendation': blocks['policy'],
            'investment': blocks['investment'],
            'sources': metric_config.sources,
            'evidence': metrics  # For QA/export
        }
```

**Benefits:**
- ✅ Zero hardcoded values - all numbers computed dynamically
- ✅ Context-aware - adapts to filter selections intelligently
- ✅ Evidence-gated - only shows insights supported by data
- ✅ Reusable across all 50 sections - DRY architecture
- ✅ Testable - unit tests for calculators, golden tests for narratives
- ✅ Maintainable - TAG values updated once, reflected everywhere

**Deliverable:** Category A (Coverage) page 100% complete with dynamic Insight Engine

---

### ✅ TASK 1.4 COMPLETION STATUS (November 4, 2025)

**STATUS: COMPLETE** (Extended from 8 hours to 12 hours to build full Insight Engine)

**Files Created:**

1. **Insight Engine Core** (`dashboard/utils/insight_engine/`)
   - ✅ `__init__.py` - Package exports
   - ✅ `context.py` (154 lines) - ViewContext, resolve_context(), data_sufficient()
   - ✅ `calc.py` (388 lines) - TAG 2024 constants + all calculators
   - ✅ `config.py` (26 lines) - MetricConfig dataclass
   - ✅ `rules.py` (260 lines) - 6 insight rules + registry
   - ✅ `templates.py` (185 lines) - Jinja2 templates for all contexts
   - ✅ `engine.py` (220 lines) - InsightEngine orchestrator
   - ✅ `README.md` - Architecture docs

2. **Dashboard Pages**
   - ✅ `dashboard/pages/01_Coverage_Accessibility_v2.py` (290 lines) - Uses InsightEngine
   - ✅ `dashboard/pages/01_Coverage_Accessibility.py` - Original (preserved for reference)

3. **Supporting Infrastructure**
   - ✅ `dashboard/components/category_template.py` (302 lines) - UI template
   - ✅ `dashboard/utils/data_loader.py` (238 lines) - Cached data loading
   - ✅ `dashboard/Home.py` (95 lines) - Homepage
   - ✅ `utils/create_regional_summary.py` (182 lines) - Data aggregation

**Total Code Written:** ~2,340 lines

**Fixes Achieved:**
- ✅ Single-region filter bug - No more "best/worst" on 1-row datasets
- ✅ Hardcoded values eliminated - All numbers computed dynamically (£42M, BCR 2.1, etc.)
- ✅ Generic insights replaced - Evidence-gated, data-driven findings
- ✅ Context-aware narratives - Adapts to all-regions/single-region/subset views
- ✅ Reusable across 50 sections - DRY architecture with centralized calculations

**Testing Instructions:**
```bash
# Test new engine-powered page
python3 -m streamlit run dashboard/pages/01_Coverage_Accessibility_v2.py

# Compare with original (hardcoded version)
python3 -m streamlit run dashboard/pages/01_Coverage_Accessibility.py
```

**Engine Features:**
- TAG 2024 compliant (time values, carbon, BCR bands)
- HM Treasury Green Book appraisal methodology
- Statistical significance testing (p-values, CIs)
- Evidence-gated insights (only shows what data supports)
- Professional consulting tone throughout

**Next:** Task 1.5 - Complete 6 remaining Category A sections using the engine

---

### DAY 4-5: Complete Category A (Coverage & Accessibility)

#### Task 1.5: Answer All 8 Coverage Questions (16 hours)

**Now uses Insight Engine** - All 8 sections will use the dynamic narrative generation system built in Task 1.4

**For Each Question (A3 through A8):** *(A1 and A2 already complete)*

1. **Write data loading function** (30 min)
   - Follow pattern from A1/A2
   - Use dashboard/utils/data_loader.py functions
   - Load relevant datasets
   - Apply filters
   - Calculate metrics

2. **Create visualization** (1 hour)
   - Use Plotly Express or Graph Objects
   - Professional chart titles (no "Figure 1:")
   - Color schemes: Greens for positive, Reds for gaps
   - Interactive tooltips with data values

3. **Define MetricConfig and use Insight Engine** (30 min)
   ```python
   config = MetricConfig(
       id='your_metric_id',
       groupby='region_name',
       value_col='your_metric_column',
       unit='your unit description',
       sources=['NaPTAN', 'BODS', 'ONS 2021', 'TAG 2024'],
       rules=['ranking', 'single_region_positioning', 'variation', 'gap_to_investment']
   )

   result = ENGINE.run(data, config, filters)
   return result  # Contains summary, key_finding, recommendation, investment
   ```
   - **NO hardcoded narratives** - Engine generates everything dynamically
   - Engine handles all contexts (all-regions/single-region/subset)
   - Automatically calculates BCR, investment costs, correlations, gaps

4. **Test with real data** (30 min)
   - Verify numbers correct
   - Test filters work (all-regions vs single-region)
   - Check narrative adapts properly

**Expected Time Per Question:** ~2 hours (reduced from 3 with Insight Engine)
- 30 min: Data loading
- 1 hour: Visualization
- 30 min: MetricConfig + engine integration (replaces 1 hour of manual narrative writing)

**Questions Implementation Order:**

**Day 4 (8 hours):**
- ✅ A1: Routes per capita (COMPLETE with Insight Engine)
- ✅ A2: Stops per 1,000 residents (COMPLETE with Insight Engine)
- A3: Stop density vs population density scatter
- A4: Bus deserts count

**Day 5 (8 hours):**
- A5: Average distance to nearest stop
- A6: LAs with >50% residents >500m from stop
- A7: Urban vs rural coverage
- A8: High population + low coverage mismatches

---

### WEEK 1 SUCCESS CRITERIA

**Must Have Before Week 2:**
- ✅ BCR calculator updated with 2024 TAG values (tested)
- ✅ TransXChange schedules parsed (41k+ trips extracted)
- ✅ 3 missing datasets downloaded (rural-urban, boundaries, car ownership)
- ✅ Category page template built and tested
- ✅ Category A (Coverage) 100% complete:
  - All 8 questions answered
  - All visualizations working
  - All data stories written
  - Real data tested
  - Page deployed locally

**Quality Gate:**
```bash
# Run validation script
python scripts/validate_week1.py

# Expected output:
✅ BCR calculator: 2024 TAG values confirmed
✅ TransXChange parsing: 41,234 trips extracted
✅ Missing datasets: 3/3 downloaded
✅ Category A: 8/8 questions complete
✅ Data quality: 97%+ demographic match maintained
✅ All tests passing

WEEK 1: COMPLETE ✅
Proceed to Week 2
```

**If ANY item fails:** STOP, fix before Week 2. No exceptions.

---

<a name="week-2-3"></a>
## 7. WEEK 2-3: BUILD CORE CATEGORIES (10 Days)

**CRITICAL: All categories use Insight Engine built in Week 1 Task 1.4**

Every section follows this pattern:
1. Load data with data_loader functions
2. Create visualization (Plotly)
3. Define MetricConfig for the section
4. Call `ENGINE.run(data, config, filters)` → Returns dynamic narrative
5. No hardcoded narratives - all text generated by engine

### Week 2: Days 6-10

#### DAY 6-7: Category D (Socio-Economic Correlations - 8 Questions)

**Why This Category Second:**
- Demographics data ready (97% match rate)
- Builds on Coverage insights
- Feeds into Equity analysis (Week 3)

**Questions D24-D31:**

**D24.** Correlation between coverage and IMD
**Viz:** Scatter plot with regression line, color by region
**Story:** "Strong negative correlation (r=-0.67): IMD Decile 1 areas receive 34% less service..."

**D25.** Unemployment vs bus coverage
**Viz:** Dual-axis choropleth map
**Story:** "Employment barriers compound in areas with both high unemployment and poor transit access..."

**D26.** Elderly population vs coverage
**Viz:** Heatmap correlation matrix
**Story:** "Elderly populations (70+) in rural areas face mobility challenges with 2.3x less service..."

**D27.** Car ownership vs service provision
**Viz:** Bubble chart (car ownership vs coverage, size = population)
**Story:** "Low car ownership doesn't guarantee good transit - policy matters more than demand..."

**D28.** Coverage vs educational attainment
**Viz:** Regional comparison bars
**Story:** "Limited transport access correlates with lower HE enrollment from deprived LSOAs..."

**D29.** Frequency vs amenity concentration
**Viz:** Network map (routes to schools, hospitals, job centers)
**Story:** "52% of schools in deprived areas lack direct bus routes during school hours..."

**D30.** Business density vs service quality
**Viz:** Employment centers overlay on frequency map
**Story:** "Business parks receive 2.3x better service than residential areas of similar density..."

**D31.** Population density vs stop density
**Viz:** Log-scale scatter plot with trendline
**Story:** "Service provision lags population growth in rapidly-expanding suburbs..."

**Time Allocation:** 3 hours per question × 8 = 24 hours (parallelizable to 16 hours aggressive)

**Deliverable:** Category D page 100% complete

---

#### DAY 8-9: Category F (Equity & Social Inclusion - 6 Questions)

**Why Third:**
- Builds on Coverage (A) + Socio-Economic (D)
- Uses IMD, unemployment, demographics
- Critical for policy justification

**Questions F35-F40:**

**F35.** Service distribution across deprivation deciles
**Viz:** Box plot by IMD decile + Lorenz curve
**Story:** "Gini coefficient 0.34 indicates moderate inequality - bottom 40% receive 23% of services..."

**F36.** Accessibility for disabled/elderly
**Viz:** Accessibility features map (low-floor buses, shelters)
**Story:** "Only 37% of stops in high-elderly LSOAs have shelters or seating..."

**F37.** Ethnic minority access
**Viz:** Demographic overlay on coverage map
**Story:** "BME populations concentrated in urban areas with good coverage, but pockets of underservice..."

**F38.** Low-income household coverage
**Viz:** Household income vs service frequency scatter
**Story:** "<£20k households have 18% less service access than >£60k households..."

**F39.** Social exclusion risk zones
**Viz:** Multi-criteria heatmap (IMD + unemployment + coverage)
**Story:** "1,247 LSOAs face triple burden: deprived, unemployed, and transit-poor..."

**F40.** Gender-disaggregated accessibility
**Viz:** Journey time analysis for essential services
**Story:** "Women's typical journey chains (school-work-shop) require 1.7x more transfers..."

**Time:** 4 hours per question × 6 = 24 hours (16 hours aggressive)

**Deliverable:** Category F page 100% complete

---

#### DAY 10: Category C (Route Characteristics - First 4 Questions)

**Why Fourth:**
- Requires TransXChange parsed data (from Day 1-2)
- Builds network understanding
- Feeds into Frequency analysis (Day 11-12)

**Questions C17-C20 (Part 1):**

**C17.** Average route length by region
**Viz:** Box plot distribution
**Story:** "Urban routes average 12km vs rural 28km - different service models needed..."

**C18.** Routes with >50 stops
**Viz:** Map with route paths highlighted
**Story:** "67 mega-routes serve 200+ stops but suffer reliability issues..."

**C19.** Route overlap analysis
**Viz:** Network graph showing parallel routes
**Story:** "Manchester city center has 18 overlapping routes - optimization opportunity..."

**C20.** Circuitous routes
**Viz:** Actual path vs straight-line comparison
**Story:** "347 routes show >2x circuity ratio - journey time competitiveness compromised..."

**Time:** 3 hours per question × 4 = 12 hours

**Deliverable:** Category C partially complete (4/7 questions)

**WEEK 2 END STATUS:**
- ✅ Category A: 8/8 complete
- ✅ Category D: 8/8 complete
- ✅ Category F: 6/6 complete
- ⚠️ Category C: 4/7 complete (continue Week 3)

---

### Week 3: Days 11-15

#### DAY 11-12: Category C (Complete Remaining 3 Questions)

**Questions C21-C23:**

**C21.** Route mileage per day by operator
**Viz:** Stacked bar chart (operator × region)
**Story:** "First Bus operates 28% of total mileage but serves 42% of deprived LSOAs..."

**C22.** Overlapping route pairs
**Viz:** Sankey diagram (origin-destination flows)
**Story:** "32 route pairs share >80% of stops - consolidation could reduce costs by £12M/year..."

**C23.** School hour vs work hour route patterns
**Viz:** Time-series heatmap (routes × hour of day)
**Story:** "Morning peak optimized for commuters, but schools start 30 min earlier..."

**Time:** 4 hours per question × 3 = 12 hours

**Deliverable:** Category C 100% complete (7/7)

---

#### DAY 13-14: Category B (Frequency & Reliability - 5 Spatial Questions)

**Note:** 3 temporal questions deferred to Phase 2

**Spatial Questions B9, B10, B12, B15, B16:**

**B9.** Regions with highest trips per day
**Viz:** Bar chart + geographic distribution
**Story:** "London averages 12,400 trips/day vs South West 3,200..."

**B10.** Lowest frequency relative to population
**Viz:** Normalized frequency scatter plot
**Story:** "Rural regions operate 4.2 trips/1000 pop vs urban 18.7..."

**B12.** Late-night/early-morning services
**Viz:** 24-hour timeline heatmap
**Story:** "Only 12% of routes operate before 6am - shift workers underserved..."

**B15.** Average headway by region
**Viz:** Box plot distribution
**Story:** "Urban headways average 8min vs rural 47min - defines user experience..."

**B16.** Rural frequency proportionality
**Viz:** Equity index comparison (urban vs rural)
**Story:** "Rural areas receive 62% less service per capita after population adjustment..."

**Time:** 3 hours per question × 5 = 15 hours

**Deliverable:** Category B complete (5/5 spatial questions)

---

#### DAY 15: Buffer Day + Week 2-3 Integration

**Tasks:**
1. **Cross-link all category pages** (2 hours)
   - Add "Related Analysis" links between categories
   - Test navigation flows
   - Verify filters work across pages

2. **Update homepage insights** (2 hours)
   - Auto-generate insights from new categories
   - Add category-specific homepage views
   - Test all 5 map views with real data

3. **Polish visualizations** (2 hours)
   - Consistent color schemes
   - Professional titles and labels
   - Add source citations

4. **Test end-to-end** (2 hours)
   - User journey: Homepage → Category A → D → F → C → B
   - Verify all data stories make sense
   - Check performance (load times)

**WEEK 2-3 END STATUS:**
- ✅ Category A: 8/8 complete
- ✅ Category B: 5/5 complete (spatial only)
- ✅ Category C: 7/7 complete
- ✅ Category D: 8/8 complete
- ✅ Category F: 6/6 complete
- **Total: 34/50 questions complete (68%)**

---

## CONTINUE TO PART 2 FOR:
- Week 4: ML Models + Advanced Categories (H, I, J, G)
- Week 5: AI Assistant with Llama Index (2 days instead of 5!)
- Week 6: Polish, Optimize, Deploy to Hugging Face
- Revolutionary GNN Features (Phase 2 roadmap)
- Complete deployment guide
- Appendices (question mappings, code templates)

---

## 🎯 WEEK 1 IMPLEMENTATION STATUS (Updated: November 2, 2025)

### ✅ COMPLETED TASKS

#### Task 1.1: BCR Calculator Updated with 2024 TAG Values ✅
**Status:** COMPLETE
**Time Taken:** 4 hours
**File:** `archive_20251031_cleanup/analysis/spatial/utils/bcr_calculator.py`

**Updates Made:**
- ✅ Time Values (TAG A1.3 Table 2):
  - Bus commuting: £9.85/hour (was £25.19)
  - Car commuting: £12.65/hour
  - Business: £28.30/hour (was £47.32)
  - Leisure: £7.85/hour (was £12.85)
- ✅ Carbon Value: £80/tonne CO₂ (was £250) - TAG A3 2024 central
- ✅ Bus emissions: 0.0965 kg CO₂e/passenger-km (BEIS 2024)
- ✅ Agglomeration uplift factors added (25% urban, 50% city center)
- ✅ BCR categories defined (HM Treasury Green Book)

**Testing:** ✅ Sample calculation BCR: 8.17 (Very High VfM)

---

#### Task 1.2: TransXChange Schedule Extraction ✅
**Status:** COMPLETE
**Time Taken:** 8 hours
**Files Created:**
- `utils/extract_all_transxchange.py` - ZIP extraction
- `utils/transxchange_schedule_extractor.py` - XML parsing

**Results:**
```
Zip files processed:    114 across 9 regions (105 successful, 9 bad)
XML files extracted:    3,376 TransXChange files
Route links extracted:  6,791,124 with stop sequences & run times
Regions covered:        9/9 (100%)
```

**Output Files:**
- `data/raw/transxchange_extracted/` - 3,376 XML files
- `data/processed/outputs/route_geometries.csv` - 6.79M route links

**Data Extracted:**
- Stop-to-stop route links
- Distance (meters)
- Run time (minutes)
- Section IDs
- Region and operator mapping

**Questions Unlocked:** B9, B10, B12, B15, C17-C21, C23

---

#### Task 1.3: Missing Datasets Download & GeoJSON Fix ✅
**Status:** COMPLETE (with fixes applied Nov 3, 2025)
**Time Taken:** 2 hours

**Dataset 1: Rural-Urban Classification** ✅
- **Status:** Already integrated in `stops_processed.csv`
- **Columns:** `UrbanRural (code)`, `UrbanRural (name)`
- **Coverage:** 100% (from schools data merge)
- **Questions unlocked:** A6, A7, B16

**Dataset 2: LSOA Boundaries GeoJSON** ✅ FIXED
- **Issue:** Original file corrupted (11 bytes, "Bad Request")
- **Root cause:** ONS ArcGIS API now requires authentication token (changed Nov 2025)
- **Solution implemented:** Created GeoJSON from existing LSOA centroid data
- **Script:** `utils/download_lsoa_boundaries.py` (updated with two-method approach)
- **Method 1:** Attempt TopoJSON download from ONS Visual repository (failed - 404)
- **Method 2 (Used):** Generate GeoJSON from existing `lsoa_names_codes.csv`
- **File:** `data/raw/boundaries/lsoa_2021.geojson`
- **Content:** 35,672 LSOA point centroids (WGS84 coordinates)
- **Size:** 6.65 MB
- **Properties:** LSOA codes, names, British National Grid coordinates
- **Geometry:** Point centroids (sufficient for heatmaps/cluster analysis)
- **Note:** Full polygon boundaries can be downloaded manually from https://geoportal.statistics.gov.uk/ if needed
- **Questions unlocked:** A6 (visualization component)

**Dataset 3: Car Ownership (Census 2021 Table TS045)** ✅ PROCESSED, ⚠️ NOT YET INTEGRATED
- **Source:** Census 2021 TS045 bulk download from NOMIS
- **Input file:** `data/raw/demographics/census2021-ts045-lsoa.csv` (1.7 MB, downloaded Jan 2023)
- **Processing script:** `utils/process_car_ownership_bulk.py`
- **Processing method:**
  - Loaded bulk CSV with all car ownership categories
  - Renamed columns to pipeline format
  - Calculated `pct_no_car` and `pct_with_car` percentages
  - Filtered to England LSOAs only (E01 codes)
  - Extracted essential columns for pipeline integration
- **Output file:** `data/raw/demographics/car_ownership_2021.csv`
- **Size:** 2.6 MB
- **Processed:** November 3, 2025 00:46
- **Records:** 33,756 LSOAs
- **Columns:**
  - `lsoa_code`, `lsoa_name`
  - `total_households`, `households_no_car`, `households_1_car`, `households_2_cars`, `households_3plus_cars`
  - `pct_no_car`, `pct_with_car`
- **Status:** File exists and processed, but NOT merged into `stops_processed.csv` yet
- **Action required:** Add to data processing pipeline (02_data_processing.py) to merge by `lsoa_code`
- **Questions unlocked when integrated:** D27, D28

**Additional Datasets Already Verified:**
- ✅ IMD 2019: 99-100% match rate
- ✅ Employment/unemployment: 96-99% match rate
- ✅ Demographics: 97-98% match rate (age, population)
- ✅ Schools: 76-81% match rate
- ✅ Business counts: 96-99% match rate (MSOA level)

**Total Stops with Demographics:** 779,262 across 9 regions

**Summary:**
- Rural/Urban: Already integrated ✅
- LSOA GeoJSON: Fixed and ready ✅
- Car ownership: Processed from bulk download, needs pipeline integration ⚠️

---

#### Pipeline Integration ✅
**Status:** COMPLETE
**File:** `data_pipeline/03_transxchange_and_bcr_processing.py`

**Features:**
1. TransXChange data loading (cached for performance)
2. Route statistics calculation by region/operator
3. BCR analysis data preparation (combines all 9 regions)
4. Sample BCR calculation validation

**Output Files:**
- `data/processed/outputs/route_geometries.csv` - 6,791,124 links
- `data/processed/outputs/route_statistics.csv` - Regional summaries
- `data/processed/outputs/stops_with_demographics_all_regions.csv` - 779k stops
- `data/processed/outputs/sample_bcr_results.json` - BCR validation

**Run Command:**
```bash
python3 data_pipeline/03_transxchange_and_bcr_processing.py
```

---

### 📊 DATA ASSETS SUMMARY (As of Nov 2, 2025)

**Bus Stops:**
- Total: 779,262 (up from 767,011)
- Regions: 9/9 (100%)
- Demographic match: 97-99%

**Route Data (NEW):**
- Route links: 6,791,124
- XML files: 3,376
- Operators: 105
- Coverage: All 9 regions

**Analysis Tools:**
- BCR Calculator: 2024 TAG values ✅
- TransXChange Parser: Production-ready ✅
- Data Pipeline: Integrated ✅

---

### 🚧 REMAINING WEEK 1 TASKS

#### Task 1.4: Build Category Page Template (8 hours) - IN PROGRESS
**Target:** Create reusable Streamlit component for all 10 categories

#### Task 1.5: Complete Category A - Coverage & Accessibility (16 hours) - PENDING
**Target:** Answer all 8 questions with visualizations and data stories

---

### 🎯 WEEK 1 SUCCESS CRITERIA

**Foundation Complete:**
- [x] BCR calculator: 2024 TAG values confirmed
- [x] TransXChange parsing: 6,791,124 route links extracted
- [x] Missing datasets: 97%+ demographic match verified
- [x] Pipeline integration: Complete and tested
- [x] Data quality: Production-ready
- [x] All tests passing

**Remaining:**
- [ ] Category page template built and tested
- [ ] Category A: 8/8 questions complete
- [ ] Real data tested in all visualizations
- [ ] Page deployed locally

**Quality Gate:** ✅ Ready to proceed once Tasks 1.4 and 1.5 complete

---

**END OF PART 1**

**Implementation Progress:** Tasks 1.1, 1.2, 1.3 + Pipeline Integration COMPLETE ✅
**Next:** Complete Tasks 1.4-1.5, then proceed to Part 2 for Weeks 2-6 and deployment.
