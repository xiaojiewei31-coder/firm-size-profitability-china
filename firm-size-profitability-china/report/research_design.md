# Empirical Research Design

## Research Question

This project asks whether larger firms in China's A-share market have stronger profitability than smaller firms, using CSI 300 and CSI 500 constituents as size-based comparison groups.

## Sample

The current dataset is an unbalanced selected-year firm panel. Firm-level observations are available for 2007, 2009, 2014, 2019, and 2023, depending on the availability of the original Wind/iFinD exports.

The selected-year design is useful for a course-project extension, but it is not yet a full annual panel. This limitation is explicitly handled in the interpretation.

## Main Specification

```text
EPS_it = alpha + beta1 log(MarketCap_it) + beta2 log(Assets_it)
         + beta3 CSI500_it + Industry FE + Year FE + error_it
```

where:

- `EPS_it` measures per-share profitability.
- `log(MarketCap_it)` and `log(Assets_it)` proxy for firm size.
- `CSI500_it` identifies mid-sized index constituents relative to CSI 300 constituents.
- Industry and year fixed effects absorb industry-level profitability differences and macro/time effects.

## Robustness Checks

The current Level 2 version includes:

- Pooled OLS benchmark.
- Year and industry fixed effects.
- Non-financial sample excluding banks and non-bank financial firms.
- Winsorized EPS to reduce outlier influence.
- Alternative efficiency outcome using EPS/assets.
- Firm and year fixed effects on the repeat-firm subsample.

## Interpretation Notes

The models should be interpreted as conditional associations, not causal estimates. CSI index membership is not randomly assigned, and the current sample may still contain selection and survivorship issues. A stronger future version should add a full firm-year panel, delisting controls, and standard profitability measures such as ROA and ROE.
