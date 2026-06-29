# Customer Analytics Pipeline

### Automated RFM Segmentation · Python · SQL Server · Power BI · Deneb

---

## What This Project Does

Every retail business has the same invisible problem: they know their total revenue, but they don't know who is generating it, who is quietly drifting away, and who they're about to lose forever.

This project answers those questions for a UK-based online retailer (the UCI Online Retail dataset) by analyzing 12 months of transaction history across 4,337 customers. It automatically classifies every customer into one of 10 behavioral segments. These groups range from Champions who buy frequently and recently, to Lost customers who haven't returned in months. The output tells the business exactly what to do about each group.

The result is not a static report. It is a pipeline. Drop in a new data file, run one command, and the entire analysis updates automatically from raw data through to a published dashboard.

---

## The Business Story: What We Found

### More than half the customer base has gone quiet

Of 4,337 customers, \*\*2,297 (53%)\*\* fall into the Hibernating, About to Sleep, or Lost categories. These are customers who have bought before but are no longer engaged. For a subscription or repeat-purchase business, this is the most important number on the dashboard. It means the majority of people who have ever trusted this retailer with their money are no longer coming back.

### A small group of Champions is carrying disproportionate weight

Only **395 customers (9.1%)** qualify as Champions, representing recent, frequent, high-spending buyers. This group almost certainly generates a revenue share far exceeding their 9% customer share. When a business's revenue depends this heavily on a small loyal core, the risk is concentration. Losing even a fraction of Champions has an outsized impact on the bottom line. The strategic implication is clear. The business must protect and reward this group before doing anything else.

### 29 customers require immediate attention

The **"Cannot Lose Them"** segment contains just 29 customers. However, these are historically high-value buyers who have recently gone silent. They bought often, they spent significantly, and now they've stopped. This is not a churn statistic. These are 29 specific people the business can identify by name and reach out to this week. A targeted win-back campaign on this group alone could recover meaningful revenue at minimal cost.

### One in four customers is a growth opportunity hiding in plain sight

**1,171 customers (27%)** are either Recent Customers or Potential Loyalists. These are people who are actively engaged but haven't yet developed habitual buying behavior. This is the segment where loyalty programs, onboarding sequences, and personalized recommendations have the highest return on investment. Converting even 20% of this group into Loyal Customers would meaningfully shift the overall health of the customer base.

### The business has a volume problem, not a customer problem

With 4,337 identifiable customers generating over £9.7M in revenue across the dataset period, revenue per customer is strong. The issue is not that individual customers spend poorly. The issue is that too many of them stop coming back. Retention, not acquisition, is the lever that moves this business.

---

## Power BI Report

The report is structured across four distinct pages:

| Page | Question Answered | Description \& Visual Approach |

| :--- | :--- | :--- |

| **1. Customer Health Overview** | What is the overall health of our customer base right now? | High-level macro trends utilizing a custom Deneb Treemap. |

| **2. Segment Deep Dive** | What does each segment look like and what should we do about it? | Behavioral matrix mapping via a layered 5x5 RFM heatmap. |

| **3. Customer Explorer** | Who specifically are our most and least valuable customers? | Granular scatter plot with conditional labeling for high-value targets. |

| **4. Revenue Analysis** | Where does revenue come from and how is it trending? | Relative growth momentum tracked via an indexed dual-trend chart. |

---

## Technical Implementation

### Architecture

```
UCI Online Retail Dataset (541,909 raw transactions · Excel)
   │
   ▼
Python Pipeline (automated, single-command execution)
   ├── Ingest      → load with dtype protection, validate file exists
   ├── Clean       → 7 defensive cleaning steps, fully logged
   ├── Transform   → RFM aggregation, quintile scoring, segment assignment
   └── Load        → SQLAlchemy bulk insert to SQL Server (3 tables)
   │
   ▼
SQL Server 2025
   ├── transactions     (392,690 rows - cleaned line-item data)
   ├── rfm\_customers    (4,337 rows - one row per customer with RFM scores)
   └── segment\_summary  (10 rows - aggregated segment metrics + strategy)
   │
   ▼
Power BI (Import mode via SQL Server connector)
   ├── Star schema relationships across 3 tables + DAX DateTable
   ├── 20+ DAX measures across Revenue, Customer, RFM, and Label folders
   └── 4-page interactive report with Deneb custom visuals
```

### Data Quality: What the Raw Data Contained and How We Handled It

The UCI Online Retail Dataset is intentionally unclean. It serves as a realistic representation of source system data quality. The cleaning pipeline handled each issue as a distinct, logged step:

| Issue | Rows Affected | Decision |
|-------|--------------|----------|
| Null CustomerID (guest checkouts) | 135,080 (24.9%) | **Removed.** Lacks a persistent identity and is unusable for longitudinal RFM tracking. |
| Cancelled invoices (prefix 'C') | 8,905 from 3,654 invoices | **Removed.** Treated as a distinct business event that nullifies purchase intent. |
| Invalid quantities (negative or >10,000) | 3 rows | **Removed.** Cleared manual adjustments and obvious data entry anomalies. |
| Zero or negative UnitPrice | 39 rows | **Removed.** Internal samples and accounting write-offs that generate zero commercial revenue. |
| Exact duplicate rows | 5,192 rows | **Removed.** Purged system re-submission artifacts to protect data integrity. |
| **Final clean dataset** | **392,690 rows (72.5% retained)** | |

Every step is logged with row counts and percentages. The log file persists across runs to provide a full audit trail of every pipeline execution.

### Why RFM? The Business Logic Behind the Model

RFM (Recency, Frequency, Monetary) is a customer segmentation framework with roots in 1960s direct mail marketing. It remains the industry standard for CRM analytics because it is interpretable, actionable, and requires no machine learning infrastructure.

Three dimensions capture the full picture of customer behavior:

- **Recency:** Days since the last purchase relative to a fixed snapshot date (2011-12-10, one day after the last transaction). A customer who bought yesterday is more likely to buy again than one who bought a year ago. Scored inversely. Lower days equals a higher score.

- **Frequency:** Distinct invoice count, not line items. Two customers who each spent £500 are not equivalent if one placed 10 orders and one placed 1. Frequency captures habitual behaviour that total spend misses.

- **Monetary:** Cumulative lifetime revenue, not average order value. Average order value is a separate operational metric. Monetary for RFM measures total relationship value.

Each dimension is scored 1–5 using quintiles (equal-population bins). Quintiles are preferred over fixed thresholds because they are self-calibrating. The scoring automatically adjusts to the distribution of your specific customer base rather than requiring manual threshold tuning that becomes stale as the business evolves.

The composite RFM score uses a weighted combination (R × 0.4 + F × 0.35 + M × 0.25). This reflects the empirical finding in CRM literature that recency is the strongest predictor of future purchase behaviour.

Segment assignment uses R and F scores only as the primary axes. Monetary correlates strongly with frequency. Adding it as a third segmentation axis increases complexity without meaningfully changing the strategic recommendation per segment.

### Why Deneb — Visual Design Decisions

Three of the four pages use Deneb (Vega / Vega-Lite) custom visuals rather than Power BI native visuals. Besides practice, each decision was made on specific grounds, not just aesthetic preference:

**Treemap (Page 1) — Vega with `nest` transform**

Power BI's native treemap cannot apply per-segment color control against an exact palette. It also cannot render two lines of text inside tiles with conditional visibility based on tile dimensions. The nest transform was chosen over stratify because the data is flat. Stratify requires a synthetic root node for hierarchical data structures, which adds unnecessary complexity for a single-level grouping.

**RFM Matrix (Page 2) — Vega-Lite layered spec**

A 5×5 heatmap with customer count and segment name in each cell. The native Matrix visual cannot render both a color fill and text overlay simultaneously in the same cell. Three Vega-Lite layers solve this cleanly. Conditional text color preserves readability across the full color scale.

**Customer Scatter Plot (Page 3) — Vega-Lite**

Chosen over native scatter for two reasons. The first is per-segment opacity control (0.55) to handle overplotting across 4,337 points. The second is a conditional label layer that surfaces only Champions and Cannot Lose Them customers above the £8,000 monetary threshold, making the chart actionable by name rather than anonymous.

**Indexed Dual Trend (Page 4) — Vega-Lite with `fold` and `window`**

Power BI's native dual-axis line chart uses separate Y scales for each series, making visual comparison between Revenue and Order Volume misleading. Indexing both series to base 100 at the first observation (using a window first\_value transform) normalizes them to the same scale. The fold function then melts the two index columns into a single series field. This enables one mark to render both lines via color encoding rather than requiring two separate layer definitions.

\### Project Structure

```
retail_pipeline/
├── main.py                  # single entry point orchestrates all stages
├── config.py                # constants, paths, thresholds
├── .env                     # credentials (not committed)
│
├── pipeline/
│   ├── ingest.py            # file loading with dtype protection
│   ├── clean.py             # 7 cleaning functions + orchestrator
│   ├── transform.py         # RFM pipeline orchestrator
│   └── load.py              # SQLAlchemy bulk insert with explicit schemas
│
├── analysis/
│   ├── rfm.py               # RFM aggregation and quintile scoring
│   └── segments.py          # segment mapping, strategy lookup, summary
│
├── visualization/
│   └── charts.py            # matplotlib/seaborn static charts
│
├── utils/
│   ├── logger.py            # structured logging to file + console
│   └── db.py                # connection factory with fail-fast validation
│
└── tests/
   ├── test\_clean.py         # pytest coverage for all cleaning functions
   └── test\_rfm.py           # pytest coverage for scoring logic
```

### Key Technical Decisions and Trade-offs

**Import mode over DirectQuery:** At 392,690 rows, Import mode gives faster visual rendering and full DAX time intelligence support. DirectQuery would be the correct choice at 10M+ rows or where real-time data freshness is required.

**SQLAlchemy over raw pyodbc:** This provides pandas `.to\_sql()` integration, connection pooling, and database-agnostic syntax. `chunksize=1000` in bulk inserts keeps parameter counts below SQL Server's 2,100-parameter statement limit.

**Explicit table schemas in `load.py`:** Rather than letting pandas infer SQL types, every column is defined explicitly. Pandas defaults all strings to `NVARCHAR(MAX)` which wastes storage and degrades query performance on large tables.

**`duplicates='drop'` in `pd.qcut`:** When many customers share identical values (common on the Frequency dimension where many customers have Frequency=1), equal-population bins produce duplicate edges. Dropping them merges those bins rather than raising an error. This is statistically honest because forcing 5 equal bins on data that doesn't support it would misrepresent the distribution.

**Weighted RFM composite vs simple average:** A simple average of R + F + M scores treats all dimensions equally. The weighted approach (0.4 / 0.35 / 0.25) encodes domain knowledge about predictive value directly into the scoring model, producing segment rankings more aligned with actual customer lifetime value.

---

## Reproducing This Project

```bash

# Clone and set up environment
git clone https://github.com/malxav/retail_pipeline
cd retail\pipeline
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt

# Configure database connection
cp .env.example .env
# Edit .env with your SQL Server details

# Place raw data file
# Download [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail) → data/online_retail.xlsx

# Run the full pipeline
python main.py
```

Pipeline runtime: approximately 45–60 seconds on a standard laptop.
Output: 3 SQL Server tables, 4 chart files in `/output/reports/`, full run log in `/logs/pipeline.log`.

---

## What I Would Build Next

- **Scheduled Execution:** Using Windows Task Scheduler or Apache Airflow so the pipeline runs automatically on new data drops without manual intervention.
- **Automated Alerts:** An email alert triggered when the "Cannot Lose Them" segment grows beyond a threshold, turning a dashboard insight into an operational trigger.
- **Cohort retention analysis:** Utilizing the transaction table to track what percentage of customers acquired in each month are still active 3, 6, and 12 months later.
- **Product affinity analysis:** Identifying which products are frequently bought together, and determining which Champions have never been exposed to the retailer's highest-margin items.