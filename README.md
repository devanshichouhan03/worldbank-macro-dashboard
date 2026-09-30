# Macro-Financial Dashboard: India, Indonesia, Brazil, South Africa

Comparative analysis of four emerging economies using World Bank Open Data (WDI) and IMF World Economic Outlook data, 2000-2024. The project pulls the data through public APIs, builds an Excel workbook and an interactive HTML dashboard, and is accompanied by a 2-page analytical brief.



## Questions answered
1. Which economies saw the greatest deterioration in macroeconomic conditions (2015-19 vs 2021-24)?
2. How did inflation and GDP growth move together?
3. Which economies showed stronger external-sector performance?
4. Which indicators could signal rising financial vulnerability?

## Key findings (full detail in the brief)
- Government debt rose in all four countries, but the strain differs: South Africa +23 points to 72% of GDP, Brazil 86%, India 82%, Indonesia 40%.
- No stable inflation-growth relationship: pooled correlation 0.03; no country-level correlation is statistically significant (n = 25).
- External strength depends on the criterion: Brazil leads on buffers, Indonesia on stability, South Africa on trade surplus but with a volatile current account.
- India's current account deficit (1.3% of GDP) exceeds FDI inflows (1.1%), which, combined with debt above 80%, is its main vulnerability.

## Indicators
GDP growth, inflation (CPI), government gross debt, exports, imports, trade balance, FDI, current account, unemployment, exchange rate (and y/y depreciation), real and lending interest rates, reserves in months of imports.

## Method
- **Deterioration score:** change in pooled z-scores (sign-adjusted so higher = better) between 2015-19 and 2021-24 averages; 2020 excluded as a one-off shock.
- **Vulnerability screen:** seven rule-of-thumb flags (inflation >10%, GDP contraction, current account deficit >3% of GDP, debt >60% of GDP, reserves <3 months of imports, unemployment >10%, currency down >15% y/y).
- **Co-movement:** same-year, ex-2020 and one-year-lead correlations between inflation and growth.
- **External scorecard:** average rank across six measures over the last ten years.

## Data sources
- World Bank World Development Indicators, via the World Bank Indicators API.
- IMF World Economic Outlook (April 2025 vintage) general government gross debt, republished by FRED. 2024 is an IMF estimate.

## How to run
```
pip install requests pandas openpyxl
python build_macro_project.py
```
Outputs: `macro_dashboard.xlsx`, `macro_dashboard.html`, `worldbank_long.csv`, `findings_summary.md`.

## Limitations
- The composite score is a rough guide only; it pools all country-years and weights nine indicators equally.
- Unemployment is an ILO modelled estimate. India's debt is on a general-government basis and may differ from national definitions.
- The 2015-19 baseline includes Brazil's recession, so growth comparisons partly reflect base effects.
- Flag thresholds are rules of thumb, not forecasts. Correlations are not causal.

## Files
| File | Description |
|---|---|
| `build_macro_project.py` | Data pull, analysis and output builder |
| `macro_dashboard.xlsx` | Workbook: data, analysis tabs, charts |
| `macro_dashboard.html` | Interactive dashboard (needs internet for chart library) |
| `worldbank_long.csv` | Tidy data, ready for Power BI |
| `findings_summary.md` | Computed result tables |
| `Macro_Brief_India_Indonesia_Brazil_SouthAfrica.docx` | 2-page analytical brief |
