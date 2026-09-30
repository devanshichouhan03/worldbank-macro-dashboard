# Findings summary (World Bank WDI, 2000-2024)

Baseline 2015-2019 vs comparison 2021-2024; negative z-change = deterioration.


## Deterioration (signed z change)
```
     country  gdp_growth  inflation  gov_debt  trade_balance   fdi  current_account  unemployment  fx_change  reserves_months  COMPOSITE
      Brazil        1.35      -0.35     -0.25           0.32 -0.36             0.16          0.25       0.99            -1.65       0.05
       India        0.40      -0.55     -0.54           0.18 -0.44            -0.00          0.30      -0.02             0.04      -0.07
   Indonesia       -0.09       0.41     -0.53           0.81 -0.02             1.06          0.08       0.14            -0.22       0.18
South Africa        0.35      -0.21     -1.06           0.84  1.67             1.54         -0.72       0.30             0.08       0.31
```

## Average levels
```
     country  2015-2019 avg | gdp_growth  2015-2019 avg | inflation  2015-2019 avg | gov_debt  2015-2019 avg | trade_balance  2015-2019 avg | fdi  2015-2019 avg | current_account  2015-2019 avg | unemployment  2015-2019 avg | fx_change  2015-2019 avg | reserves_months  2021-2024 avg | gdp_growth  2021-2024 avg | inflation  2021-2024 avg | gov_debt  2021-2024 avg | trade_balance  2021-2024 avg | fdi  2021-2024 avg | current_account  2021-2024 avg | unemployment  2021-2024 avg | fx_change  2021-2024 avg | reserves_months
      Brazil                       -0.50                       5.72                     80.76                          -0.06                 3.77                            -2.53                         11.43                      12.04                            14.31                        3.61                       6.64                     86.04                           0.89                 3.23                            -2.18                          9.28                       1.25                             9.21
       India                        6.67                       4.17                     70.62                          -2.71                 1.78                            -1.30                          7.41                       2.95                             7.95                        7.90                       5.61                     82.04                          -2.16                 1.12                            -1.31                          4.89                       3.12                             8.09
   Indonesia                        5.03                       3.99                     29.07                           0.12                 1.77                            -2.22                          4.12                       3.71                             6.53                        4.77                       2.91                     40.27                           2.53                 1.74                             0.13                          3.47                       2.14                             5.86
South Africa                        0.99                       4.98                     49.71                           0.26                 0.87                            -2.99                         26.82                       6.39                             5.12                        2.06                       5.52                     72.31                           2.78                 3.39                             0.43                         32.91                       3.15                             5.37
```

## Inflation vs growth correlation
```
     country  corr_same_year  corr_ex_2020  corr_infl_lead_1y   n
      Brazil           -0.15         -0.28              -0.00  25
       India            0.00          0.07               0.20  25
   Indonesia            0.25          0.05               0.24  25
South Africa           -0.07         -0.29              -0.36  25
      POOLED            0.03         -0.07                NaN 100
```

## External-sector scorecard
```
     country  current_account_avg  current_account_vol  fdi_avg  trade_balance_avg  reserves_months_avg  exports_gdp_avg  avg_depreciation_pa  avg_rank (1=best)
      Brazil                -2.30                 0.85     3.43               0.39                12.34            15.77                 9.59               2.33
   Indonesia                -1.10                 1.32     1.76               1.25                 6.45            20.74                 3.02               2.33
       India                -1.05                 1.03     1.58              -2.26                 8.50            20.49                 3.25               2.50
South Africa                -1.12                 2.46     1.88               1.68                 5.42            29.53                 5.85               2.83
```

## Vulnerability flags (last 10 yrs)
```
     country  avg_flags_per_yr  worst_year_flags  total_flags
      Brazil               2.3                 4           23
       India               1.1                 2           11
   Indonesia               0.1                 1            1
South Africa               2.0                 3           20
```

## Data coverage (obs count per series)
```
     country  gdp_growth  inflation  gov_debt  gov_debt_central  exports_gdp  imports_gdp  fdi  current_account  unemployment  fx_rate  real_rate  lending_rate  reserves_months  trade_balance  fx_change
      Brazil          25         25        25                15           25           25   25               25            25       25         25            25               25             25         24
       India          25         25        25                19           25           25   25               25            25       25         23            23               25             25         24
   Indonesia          25         25        25                 4           25           25   25               25            25       25         25            25               25             25         24
South Africa          25         25        25                11           25           25   25               25            25       25         25            25               25             25         24
```

## Flags by country-year (last 6 years)
```
     country  year  n_flags                                                                          flags
      Brazil  2019        3                 Current a/c deficit >3%; Govt debt >60% GDP; Unemployment >10%
      Brazil  2020        4 GDP contraction; Govt debt >60% GDP; Unemployment >10%; Currency fell >15% y/y
      Brazil  2021        2                                          Govt debt >60% GDP; Unemployment >10%
      Brazil  2022        1                                                             Govt debt >60% GDP
      Brazil  2023        1                                                             Govt debt >60% GDP
      Brazil  2024        1                                                             Govt debt >60% GDP
       India  2019        1                                                             Govt debt >60% GDP
       India  2020        2                                            GDP contraction; Govt debt >60% GDP
       India  2021        1                                                             Govt debt >60% GDP
       India  2022        1                                                             Govt debt >60% GDP
       India  2023        1                                                             Govt debt >60% GDP
       India  2024        1                                                             Govt debt >60% GDP
   Indonesia  2019        0                                                                               
   Indonesia  2020        1                                                                GDP contraction
   Indonesia  2021        0                                                                               
   Indonesia  2022        0                                                                               
   Indonesia  2023        0                                                                               
   Indonesia  2024        0                                                                               
South Africa  2019        1                                                              Unemployment >10%
South Africa  2020        3                         GDP contraction; Govt debt >60% GDP; Unemployment >10%
South Africa  2021        2                                          Govt debt >60% GDP; Unemployment >10%
South Africa  2022        2                                          Govt debt >60% GDP; Unemployment >10%
South Africa  2023        2                                          Govt debt >60% GDP; Unemployment >10%
South Africa  2024        2                                          Govt debt >60% GDP; Unemployment >10%
```