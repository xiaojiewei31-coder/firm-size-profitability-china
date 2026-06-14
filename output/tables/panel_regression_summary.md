# Panel Regression Summary

Standard errors are industry-clustered unless otherwise noted. Stars are reported in the CSV output.

| model | dependent_variable | sample | n_observations | n_firms | r_squared | log_market_cap_coef | log_market_cap_se | log_assets_coef | log_assets_se | is_csi500_coef | is_csi500_se |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1_pooled_ols | eps | Full selected-year sample | 3496 | 1707 | 0.1200 | 0.8297 | 0.2859 | -0.2514 | 0.1041 | 0.2743 | 0.1548 |
| M2_year_industry_fe | eps | Full sample with year and industry fixed effects | 3496 | 1707 | 0.1676 | 0.7800 | 0.2784 | -0.2642 | 0.0705 | 0.1281 | 0.2138 |
| M3_non_financial_fe | eps | Excludes banks and non-bank financial firms | 3201 | 1592 | 0.1720 | 0.8758 | 0.3274 | -0.2870 | 0.0664 | 0.2225 | 0.2613 |
| M4_winsorized_eps_fe | eps_w | EPS winsorized at 1st and 99th percentiles | 3496 | 1707 | 0.2720 | 0.4859 | 0.0784 | -0.1908 | 0.0436 | -0.0717 | 0.0860 |
| M5_efficiency_fe | eps_asset_scaled_w | Alternative outcome: winsorized EPS/assets, scaled by 1e12 | 3496 | 1707 | 0.3064 | 52.6449 | 6.8298 | -67.4894 | 8.3201 | 9.9599 | 4.8432 |
| M6_firm_year_fe | eps_w | Repeat-firm sample with firm and year fixed effects | 2722 | 933 | 0.7122 | 0.5430 | 0.0501 | -0.0698 | 0.0488 |  |  |