# Dashboard Design

## Purpose

The Streamlit dashboard turns the empirical finance project into an interactive data product. It is designed for reviewers, classmates, and admissions readers who want to explore the research findings without reading the code first.

## Main User Questions

- How do CSI 300 and CSI 500 EPS trends differ over time?
- Within a selected year or industry, are larger firms more profitable?
- Do industry patterns explain part of the size-profitability relationship?
- Are the regression results consistent across fixed-effects and robustness specifications?

## Views

1. Market overview
   - EPS trend and annual EPS growth by index group.
   - Summary cards for selected observations.

2. Firm explorer
   - Interactive firm-level scatter plot.
   - Toggle between market capitalization and total assets as the size axis.
   - Filterable company table for auditability.

3. Industry comparison
   - Industry-level average EPS comparison.
   - Industry size-profitability relationship.

4. Regression results
   - Summary table for the Level 2 empirical models.
   - Coefficient comparison across robustness checks.

## ROA Limitation

The current raw exports include EPS, total assets, market capitalization, and industry, but not net income. Therefore, the dashboard does not calculate ROA. It reports `EPS/assets` as an asset-efficiency proxy and explicitly labels it as a proxy rather than ROA.

The next data upgrade should add:

- Net income
- Book equity
- Revenue
- Total liabilities

These fields would support ROA, ROE, profit margin, asset turnover, and leverage controls.
